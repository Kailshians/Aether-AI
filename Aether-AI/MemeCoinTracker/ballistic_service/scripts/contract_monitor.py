#!/usr/bin/env python3
"""
Contract Monitor - Monitors blockchain for new token contracts
"""

import os
import sys
import json
import logging
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from config import ETHERSCAN_API_KEY, PUMPFUN_API_KEY, ETHERSCAN_API_ENDPOINT, PUMPFUN_API_ENDPOINT

# Configure logging
logger = logging.getLogger("contract_monitor")

class ContractMonitor:
    """Monitor blockchain for new token contracts and match against keywords"""
    
    def __init__(self):
        """Initialize the ContractMonitor"""
        self.eth_contracts_path = Path("ballistic_service/data/eth_contracts.json")
        self.eth_contracts = self._load_eth_contracts()
        
        logger.info("ContractMonitor initialized")
    
    def _load_eth_contracts(self):
        """Load existing Ethereum contracts data from JSON file"""
        if self.eth_contracts_path.exists():
            try:
                with open(self.eth_contracts_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Error loading ETH contracts data: {str(e)}")
        
        return {"contracts": [], "last_updated": datetime.now().isoformat()}
    
    def _save_eth_contracts(self):
        """Save Ethereum contracts data to JSON file"""
        try:
            with open(self.eth_contracts_path, 'w') as f:
                json.dump(self.eth_contracts, f, indent=2)
        except OSError as e:
            logger.error(f"Error saving ETH contracts data: {str(e)}")
    
    def update_ethereum_contracts(self):
        """Update Ethereum contracts from Etherscan API"""
        if not ETHERSCAN_API_KEY:
            logger.warning("Etherscan API key not configured")
            return False
        
        try:
            # Get the current time
            current_time = datetime.now()
            
            # Calculate the time 24 hours ago
            time_24h_ago = current_time - timedelta(hours=24)
            
            # Convert to Unix timestamp
            start_time = int(time_24h_ago.timestamp())
            end_time = int(current_time.timestamp())
            
            # Etherscan API to get token transfers (proxy for new tokens)
            params = {
                'module': 'account',
                'action': 'tokentx',
                'startblock': 0,
                'endblock': 999999999,
                'sort': 'desc',
                'apikey': ETHERSCAN_API_KEY
            }
            
            response = requests.get(ETHERSCAN_API_ENDPOINT, params=params)
            data = response.json()
            
            if data['status'] != '1':
                logger.error(f"Etherscan API error: {data['message']}")
                return False
            
            # Process the transactions
            new_contracts = []
            existing_addresses = {c['address'] for c in self.eth_contracts['contracts']}
            
            for tx in data['result']:
                # Only consider contracts we haven't seen before
                if tx['contractAddress'] not in existing_addresses:
                    # Basic token contract metadata
                    contract_data = {
                        'address': tx['contractAddress'],
                        'name': tx['tokenName'],
                        'symbol': tx['tokenSymbol'],
                        'created_at': datetime.fromtimestamp(int(tx['timeStamp'])).isoformat(),
                        'blockchain': 'ethereum'
                    }
                    
                    new_contracts.append(contract_data)
                    existing_addresses.add(tx['contractAddress'])
            
            # Update the contracts data
            if new_contracts:
                logger.info(f"Found {len(new_contracts)} new Ethereum contracts")
                self.eth_contracts['contracts'] = new_contracts + self.eth_contracts['contracts']
                self.eth_contracts['last_updated'] = current_time.isoformat()
                self._save_eth_contracts()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating Ethereum contracts: {str(e)}")
            return False
    
    def update_solana_contracts(self):
        """Update Solana contracts from PumpFun API"""
        if not PUMPFUN_API_KEY:
            logger.warning("PumpFun API key not configured")
            return False
        
        try:
            # For this implementation, we'll just log the attempt
            # as the actual PumpFun API endpoint is not specified
            logger.info("Attempted to update Solana contracts from PumpFun")
            
            # In a real implementation, this would make API calls to PumpFun
            # and update the contract data
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating Solana contracts: {str(e)}")
            return False
    
    def update_contracts(self):
        """Update contracts from all monitored blockchains"""
        ethereum_updated = self.update_ethereum_contracts()
        solana_updated = self.update_solana_contracts()
        
        return ethereum_updated or solana_updated
    
    def find_matches(self, keywords):
        """Find contracts that match the given keywords"""
        # First, update contracts to ensure we have the latest data
        self.update_contracts()
        
        # Convert keywords to lowercase for case-insensitive matching
        normalized_keywords = [kw.lower() for kw in keywords]
        
        matches = []
        
        # Search through Ethereum contracts
        for contract in self.eth_contracts['contracts']:
            # Check if any keyword is in the contract name or symbol
            name_lower = contract['name'].lower()
            symbol_lower = contract['symbol'].lower()
            
            for keyword in normalized_keywords:
                if keyword in name_lower or keyword in symbol_lower:
                    # Calculate a simple match score based on exact match vs substring
                    score = 0.0
                    
                    # Exact matches are scored higher
                    if keyword == name_lower or keyword == symbol_lower:
                        score = 1.0
                    else:
                        # Calculate partial match score based on length ratio
                        name_ratio = len(keyword) / len(name_lower) if name_lower else 0
                        symbol_ratio = len(keyword) / len(symbol_lower) if symbol_lower else 0
                        score = max(name_ratio, symbol_ratio) * 0.8  # Scale down partial matches
                    
                    match_data = {
                        **contract,  # Include all contract fields
                        'match_keyword': keyword,
                        'match_score': score,
                        'match_type': 'name' if keyword in name_lower else 'symbol'
                    }
                    
                    matches.append(match_data)
                    break  # Only count each contract once per keyword set
        
        # Sort matches by score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    monitor = ContractMonitor()
    
    # Update contracts
    print("Updating contracts...")
    monitor.update_contracts()
    
    # Test match finding
    test_keywords = ["doge", "pepe", "meme"]
    print(f"Finding matches for keywords: {test_keywords}")
    matches = monitor.find_matches(test_keywords)
    
    if matches:
        print(f"Found {len(matches)} matches:")
        for match in matches:
            print(f"- {match['name']} ({match['symbol']}): {match['match_score']}")
    else:
        print("No matches found")
