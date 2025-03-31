#!/usr/bin/env python3
"""
Whale Tracker - Monitors large holder activity for tokens
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import ETHERSCAN_API_KEY, ETHERSCAN_API_ENDPOINT

# Configure logging
logger = logging.getLogger("whale_tracker")

class WhaleTracker:
    """Tracks and analyzes large holder (whale) activity for tokens"""
    
    def __init__(self):
        """Initialize the WhaleTracker"""
        logger.info("WhaleTracker initialized")
    
    def get_top_holders(self, token_address, blockchain="ethereum", limit=10):
        """Get the top token holders"""
        logger.info(f"Getting top {limit} holders for {token_address} on {blockchain}")
        
        if blockchain.lower() == "ethereum":
            return self._get_ethereum_holders(token_address, limit)
        elif blockchain.lower() == "solana":
            return self._get_solana_holders(token_address, limit)
        else:
            logger.error(f"Unsupported blockchain: {blockchain}")
            return None
    
    def _get_ethereum_holders(self, token_address, limit=10):
        """Get top token holders on Ethereum"""
        try:
            # In a real implementation, this would call Etherscan API
            # or use a service like Ethplorer to get holder information
            
            if not ETHERSCAN_API_KEY:
                logger.warning("Etherscan API key not configured")
                return self._simulate_holders(token_address, "ethereum", limit)
            
            # Make API request to get token holder information
            # This is a placeholder for the actual API call
            params = {
                'module': 'token',
                'action': 'tokenholderlist',
                'contractaddress': token_address,
                'page': 1,
                'offset': limit,
                'apikey': ETHERSCAN_API_KEY
            }
            
            # Uncomment for actual implementation
            # response = requests.get(ETHERSCAN_API_ENDPOINT, params=params)
            # data = response.json()
            # 
            # if data['status'] != '1':
            #     logger.error(f"Etherscan API error: {data['message']}")
            #     return None
            # 
            # # Process holder data
            # holder_data = []
            # for holder in data['result']:
            #     holder_data.append({
            #         'address': holder['address'],
            #         'balance': float(holder['value']) / (10 ** 18),  # Convert from wei to tokens
            #         'percentage': float(holder['share']) * 100
            #     })
            # 
            # return {
            #     'token_address': token_address,
            #     'blockchain': 'ethereum',
            #     'timestamp': datetime.now().isoformat(),
            #     'total_holders': data.get('total_holder_count', len(holder_data)),
            #     'holders': holder_data
            # }
            
            # For this demo, simulate holder data
            return self._simulate_holders(token_address, "ethereum", limit)
            
        except Exception as e:
            logger.error(f"Error getting Ethereum holders for {token_address}: {str(e)}")
            return None
    
    def _get_solana_holders(self, token_address, limit=10):
        """Get top token holders on Solana"""
        try:
            # In a real implementation, this would call a Solana API
            # For this demo, simulate holder data
            return self._simulate_holders(token_address, "solana", limit)
            
        except Exception as e:
            logger.error(f"Error getting Solana holders for {token_address}: {str(e)}")
            return None
    
    def _simulate_holders(self, token_address, blockchain, limit=10):
        """Simulate holder data for demo purposes"""
        import random
        
        # Create a seed based on the token address for consistent random values
        seed = int(token_address.replace("0x", "")[:8], 16) if token_address.startswith("0x") else hash(token_address)
        random.seed(seed)
        
        # Generate holder data
        holder_data = []
        total_supply = 1000000000  # Typical token supply 
        remaining_percentage = 100.0
        
        for i in range(limit):
            # For realistic distribution, whales have more concentrated holdings at the top
            if i == 0:
                percentage = random.uniform(10, 30)  # Top holder has 10-30%
            elif i < 3:
                percentage = random.uniform(5, 15)  # Next few have 5-15%
            else:
                percentage = random.uniform(1, 5)  # Rest have 1-5%
            
            # Adjust if we're exceeding 100%
            if remaining_percentage - percentage < 0:
                percentage = remaining_percentage
            
            remaining_percentage -= percentage
            
            balance = (percentage / 100) * total_supply
            
            holder_data.append({
                'address': f"0x{random.getrandbits(160):040x}" if blockchain == "ethereum" else f"{random.getrandbits(32):08x}",
                'balance': balance,
                'percentage': percentage
            })
        
        # Add a final entry for "other holders" if we haven't reached 100%
        if remaining_percentage > 0:
            holder_data.append({
                'address': "Others",
                'balance': (remaining_percentage / 100) * total_supply,
                'percentage': remaining_percentage
            })
        
        return {
            'token_address': token_address,
            'blockchain': blockchain,
            'timestamp': datetime.now().isoformat(),
            'total_holders': random.randint(100, 10000),
            'holders': holder_data
        }
    
    def analyze_whale_concentration(self, token_address, blockchain="ethereum"):
        """Analyze whale concentration and risk"""
        holder_data = self.get_top_holders(token_address, blockchain, limit=10)
        if not holder_data:
            return None
        
        holders = holder_data['holders']
        
        # Calculate concentration metrics
        top_holder_percentage = holders[0]['percentage'] if holders else 0
        top5_percentage = sum(h['percentage'] for h in holders[:5] if h['address'] != "Others")
        top10_percentage = sum(h['percentage'] for h in holders[:10] if h['address'] != "Others")
        
        # Determine concentration risk
        if top_holder_percentage > 50:
            concentration_risk = "Very High"
            risk_score = 0.9
        elif top_holder_percentage > 30:
            concentration_risk = "High"
            risk_score = 0.7
        elif top5_percentage > 70:
            concentration_risk = "High"
            risk_score = 0.7
        elif top5_percentage > 50:
            concentration_risk = "Medium"
            risk_score = 0.5
        elif top10_percentage > 80:
            concentration_risk = "Medium"
            risk_score = 0.5
        else:
            concentration_risk = "Low"
            risk_score = 0.2
        
        return {
            'token_address': token_address,
            'blockchain': blockchain,
            'timestamp': datetime.now().isoformat(),
            'concentration_metrics': {
                'top_holder_percentage': top_holder_percentage,
                'top5_percentage': top5_percentage,
                'top10_percentage': top10_percentage
            },
            'concentration_risk': concentration_risk,
            'risk_score': risk_score,
            'holders': holders[:5]  # Include top 5 holders in the result
        }
    
    def track_whale_movements(self, token_address, blockchain="ethereum", days=7):
        """Track whale movements over time"""
        try:
            # In a real implementation, this would query historical transfer data
            # from the blockchain to track large wallet movements
            
            # For this demo, simulate whale movement data
            import random
            from datetime import datetime, timedelta
            
            # Create a seed based on the token address for consistent random values
            seed = int(token_address.replace("0x", "")[:8], 16) if token_address.startswith("0x") else hash(token_address)
            random.seed(seed)
            
            # Current time
            now = datetime.now()
            
            # Generate whale movement data
            movements = []
            
            # To make it somewhat realistic, create a few "whale wallets"
            whale_wallets = [f"0x{random.getrandbits(160):040x}" for _ in range(3)]
            
            for i in range(days):
                # Each day has 0-3 whale movements
                day_movements = random.randint(0, 3)
                
                for j in range(day_movements):
                    # Random timestamp within the day
                    timestamp = now - timedelta(days=i, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                    
                    # Random amount (1-5% of total supply)
                    amount_percentage = random.uniform(1, 5)
                    amount = 1000000000 * (amount_percentage / 100)  # Based on assumed total supply
                    
                    # Random whale wallet
                    whale = random.choice(whale_wallets)
                    
                    # Random direction (in or out)
                    direction = random.choice(["in", "out"])
                    
                    # If out, generate a destination
                    destination = f"0x{random.getrandbits(160):040x}" if direction == "out" else None
                    
                    # If in, generate a source
                    source = f"0x{random.getrandbits(160):040x}" if direction == "in" else None
                    
                    movements.append({
                        'timestamp': timestamp.isoformat(),
                        'wallet': whale,
                        'direction': direction,
                        'amount': amount,
                        'percentage': amount_percentage,
                        'source': source,
                        'destination': destination,
                        'transaction_hash': f"0x{random.getrandbits(256):064x}"
                    })
            
            # Sort by timestamp (most recent first)
            movements.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'token_address': token_address,
                'blockchain': blockchain,
                'period_start': (now - timedelta(days=days)).isoformat(),
                'period_end': now.isoformat(),
                'total_movements': len(movements),
                'movements': movements
            }
            
        except Exception as e:
            logger.error(f"Error tracking whale movements for {token_address}: {str(e)}")
            return None


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    tracker = WhaleTracker()
    
    # Test token address
    test_token = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    
    # Get top holders
    holders = tracker.get_top_holders(test_token)
    if holders:
        print(f"Top holders for {test_token}:")
        for i, holder in enumerate(holders['holders']):
            print(f"{i+1}. {holder['address'][:10]}...: {holder['percentage']:.2f}% ({holder['balance']} tokens)")
    
    # Analyze whale concentration
    concentration = tracker.analyze_whale_concentration(test_token)
    if concentration:
        print(f"\nWhale concentration: {concentration['concentration_risk']}")
        print(f"Top holder: {concentration['concentration_metrics']['top_holder_percentage']:.2f}%")
        print(f"Top 5 holders: {concentration['concentration_metrics']['top5_percentage']:.2f}%")
    
    # Track whale movements
    movements = tracker.track_whale_movements(test_token, days=3)
    if movements:
        print(f"\nRecent whale movements ({movements['total_movements']}):")
        for movement in movements['movements'][:3]:  # Show the 3 most recent
            direction_symbol = "←" if movement['direction'] == "in" else "→"
            print(f"{movement['timestamp']} {direction_symbol} {movement['percentage']:.2f}% ({movement['amount']} tokens)")
