#!/usr/bin/env python3
"""
DEX Metrics - Analyzes decentralized exchange data for tokens
"""

import os
import sys
import json
import logging
import time
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import ETHERSCAN_API_KEY

# Configure logging
logger = logging.getLogger("dex_metrics")

class DexMetricsAnalyzer:
    """Analyzer for DEX metrics like volume, liquidity, and market cap"""
    
    def __init__(self):
        """Initialize the DEX metrics analyzer"""
        logger.info("DEX Metrics Analyzer initialized")
    
    def get_token_metrics(self, token_address, blockchain="ethereum"):
        """Get comprehensive metrics for a token"""
        logger.info(f"Getting metrics for {token_address} on {blockchain}")
        
        if blockchain.lower() == "ethereum":
            return self._get_ethereum_metrics(token_address)
        elif blockchain.lower() == "solana":
            return self._get_solana_metrics(token_address)
        else:
            logger.error(f"Unsupported blockchain: {blockchain}")
            return None
    
    def _get_ethereum_metrics(self, token_address):
        """Get metrics for an Ethereum token"""
        try:
            # In a real implementation, this would query:
            # 1. Etherscan for basic token info
            # 2. DEX APIs/subgraphs (e.g., Uniswap) for liquidity and volume
            # 3. CoinGecko or similar for price data
            
            # For this demo, we'll simulate the metrics
            return self._simulate_metrics(token_address, "ethereum")
            
        except Exception as e:
            logger.error(f"Error getting Ethereum metrics for {token_address}: {str(e)}")
            return None
    
    def _get_solana_metrics(self, token_address):
        """Get metrics for a Solana token"""
        try:
            # In a real implementation, this would query:
            # 1. Solana blockchain explorers
            # 2. Raydium or other Solana DEX APIs
            
            # For this demo, we'll simulate the metrics
            return self._simulate_metrics(token_address, "solana")
            
        except Exception as e:
            logger.error(f"Error getting Solana metrics for {token_address}: {str(e)}")
            return None
    
    def _simulate_metrics(self, token_address, blockchain):
        """Simulate metrics for demo purposes"""
        import random
        
        # Create a seed based on the token address for consistent random values
        seed = int(token_address.replace("0x", "")[:8], 16) if token_address.startswith("0x") else hash(token_address)
        random.seed(seed)
        
        # Current timestamp
        current_time = datetime.now().timestamp()
        
        # Generate metrics
        price_usd = random.uniform(0.00001, 0.1)
        market_cap = random.uniform(10000, 10000000)
        volume_24h = market_cap * random.uniform(0.01, 0.2)
        liquidity = market_cap * random.uniform(0.05, 0.5)
        holders = int(random.uniform(100, 10000))
        
        # Generate price history (last 7 days, hourly)
        price_history = []
        for i in range(168):  # 7 days * 24 hours
            timestamp = current_time - ((168 - i) * 3600)
            # Create a somewhat realistic price movement
            if i > 0:
                last_price = price_history[-1]["price"]
                change = random.uniform(-0.05, 0.05)  # -5% to +5% change
                new_price = last_price * (1 + change)
            else:
                new_price = price_usd * random.uniform(0.7, 1.3)
            
            price_history.append({
                "timestamp": timestamp,
                "price": new_price
            })
        
        # Generate volume history (last 7 days, daily)
        volume_history = []
        for i in range(7):  # 7 days
            timestamp = current_time - ((7 - i) * 86400)
            daily_volume = volume_24h * random.uniform(0.5, 1.5)
            
            volume_history.append({
                "timestamp": timestamp,
                "volume": daily_volume
            })
        
        # Calculate simple metrics
        price_change_24h = ((price_history[-1]["price"] / price_history[-24]["price"]) - 1) * 100
        price_change_7d = ((price_history[-1]["price"] / price_history[0]["price"]) - 1) * 100
        
        # Return compiled metrics
        return {
            "token_address": token_address,
            "blockchain": blockchain,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "price_usd": price_usd,
                "market_cap": market_cap,
                "volume_24h": volume_24h,
                "liquidity": liquidity,
                "holders": holders,
                "price_change_24h": price_change_24h,
                "price_change_7d": price_change_7d,
                "fully_diluted_valuation": market_cap * random.uniform(1.2, 2.0)
            },
            "history": {
                "price": price_history,
                "volume": volume_history
            },
            "exchange_data": {
                "primary_dex": "Uniswap V3" if blockchain == "ethereum" else "Raydium",
                "dex_url": f"https://{'app.uniswap.org' if blockchain == 'ethereum' else 'raydium.io'}/swap?inputCurrency=ETH&outputCurrency={token_address}"
            }
        }
    
    def calculate_token_safety(self, token_address, blockchain="ethereum"):
        """Calculate safety metrics for a token based on DEX data"""
        metrics = self.get_token_metrics(token_address, blockchain)
        if not metrics:
            return None
        
        # In a real implementation, this would analyze:
        # 1. Liquidity concentration (rugpull risk)
        # 2. Trading volume patterns (pump and dump signs)
        # 3. Holder distribution (whale concentration)
        # 4. Contract interactions
        
        import random
        
        # Extract metrics
        market_cap = metrics["metrics"]["market_cap"]
        liquidity = metrics["metrics"]["liquidity"]
        volume_24h = metrics["metrics"]["volume_24h"]
        holders = metrics["metrics"]["holders"]
        
        # Calculate safety metrics
        liquidity_ratio = liquidity / market_cap if market_cap > 0 else 0
        volume_to_mcap_ratio = volume_24h / market_cap if market_cap > 0 else 0
        
        # Initialize safety score components
        safety_components = {}
        
        # Liquidity score (higher liquidity ratio is safer)
        if liquidity_ratio >= 0.3:
            safety_components["liquidity"] = 0.9
        elif liquidity_ratio >= 0.15:
            safety_components["liquidity"] = 0.7
        elif liquidity_ratio >= 0.05:
            safety_components["liquidity"] = 0.5
        else:
            safety_components["liquidity"] = 0.2
        
        # Volume score (extreme volume relative to market cap can be suspicious)
        if volume_to_mcap_ratio <= 0.05:
            safety_components["volume"] = 0.9  # Low volume is often safer for new tokens
        elif volume_to_mcap_ratio <= 0.2:
            safety_components["volume"] = 0.7
        elif volume_to_mcap_ratio <= 0.5:
            safety_components["volume"] = 0.5
        else:
            safety_components["volume"] = 0.3  # Very high volume can indicate manipulation
        
        # Holder score (more holders is generally safer)
        if holders >= 1000:
            safety_components["holders"] = 0.9
        elif holders >= 500:
            safety_components["holders"] = 0.7
        elif holders >= 100:
            safety_components["holders"] = 0.5
        else:
            safety_components["holders"] = 0.3
        
        # Market cap score (higher market cap typically indicates more stability)
        if market_cap >= 1000000:
            safety_components["market_cap"] = 0.9
        elif market_cap >= 100000:
            safety_components["market_cap"] = 0.7
        elif market_cap >= 10000:
            safety_components["market_cap"] = 0.5
        else:
            safety_components["market_cap"] = 0.3
        
        # Calculate an overall safety score
        weights = {
            "liquidity": 0.4,
            "volume": 0.2,
            "holders": 0.2,
            "market_cap": 0.2
        }
        
        safety_score = sum(score * weights[component] for component, score in safety_components.items())
        
        # Generate risk factors based on scores
        risk_factors = []
        
        if safety_components["liquidity"] < 0.5:
            risk_factors.append("Low liquidity relative to market cap")
        if safety_components["volume"] < 0.5:
            risk_factors.append("Unusual trading volume patterns")
        if safety_components["holders"] < 0.5:
            risk_factors.append("Small number of token holders")
        if safety_components["market_cap"] < 0.5:
            risk_factors.append("Low market capitalization")
        
        return {
            "token_address": token_address,
            "blockchain": blockchain,
            "safety_score": safety_score,
            "safety_components": safety_components,
            "risk_factors": risk_factors,
            "analysis_timestamp": datetime.now().isoformat()
        }


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    analyzer = DexMetricsAnalyzer()
    
    # Test token address
    test_token = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    
    # Get token metrics
    metrics = analyzer.get_token_metrics(test_token)
    if metrics:
        print(f"Token metrics for {test_token}:")
        print(f"Price: ${metrics['metrics']['price_usd']:.6f}")
        print(f"Market Cap: ${metrics['metrics']['market_cap']:.2f}")
        print(f"24h Volume: ${metrics['metrics']['volume_24h']:.2f}")
        print(f"Liquidity: ${metrics['metrics']['liquidity']:.2f}")
        print(f"Holders: {metrics['metrics']['holders']}")
        print(f"24h Change: {metrics['metrics']['price_change_24h']:.2f}%")
    
    # Calculate token safety
    safety = analyzer.calculate_token_safety(test_token)
    if safety:
        print("\nSafety Analysis:")
        print(f"Overall Safety Score: {safety['safety_score']:.2f}")
        print("Risk Factors:")
        for factor in safety['risk_factors']:
            print(f"- {factor}")
