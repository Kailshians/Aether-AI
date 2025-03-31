#!/usr/bin/env python3
"""
Meme Coin Correlator - Links data between Ballistic and TrendForger services
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from ballistic_service.scripts.meme_scanner import MemeScanner
from trendforger.scripts.meme_analytics import MemeAnalytics
from analysis.sentiment.vader_custom import VaderSentimentAnalyzer

# Configure logging
logger = logging.getLogger("meme_coin_correlator")

class MemeCoinCorrelator:
    """Links data between meme detection and coin monitoring services"""
    
    def __init__(self):
        """Initialize the MemeCoinCorrelator"""
        self.meme_scanner = MemeScanner()
        self.meme_analytics = MemeAnalytics()
        self.sentiment_analyzer = VaderSentimentAnalyzer()
        
        # Load stored correlation data if available
        self.correlation_data_path = Path("analysis/cross_service/data/correlations.json")
        self.correlation_data_path.parent.mkdir(parents=True, exist_ok=True)
        self.correlation_data = self._load_correlation_data()
        
        logger.info("MemeCoinCorrelator initialized")
    
    def _load_correlation_data(self):
        """Load existing correlation data from JSON file"""
        if self.correlation_data_path.exists():
            try:
                with open(self.correlation_data_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Error loading correlation data: {str(e)}")
        
        return {"correlations": [], "last_updated": datetime.now().isoformat()}
    
    def _save_correlation_data(self):
        """Save correlation data to JSON file"""
        try:
            with open(self.correlation_data_path, 'w') as f:
                json.dump(self.correlation_data, f, indent=2)
        except OSError as e:
            logger.error(f"Error saving correlation data: {str(e)}")
    
    def load_meme_data(self):
        """Load meme data from Ballistic service"""
        try:
            meme_data_path = Path("ballistic_service/data/raw_memes.json")
            if not meme_data_path.exists():
                logger.warning(f"Meme data file not found: {meme_data_path}")
                return []
            
            with open(meme_data_path, 'r') as f:
                data = json.load(f)
                return data.get("memes", [])
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading meme data: {str(e)}")
            return []
    
    def load_coin_data(self):
        """Load coin data from Ballistic service"""
        try:
            coin_data_path = Path("ballistic_service/data/eth_contracts.json")
            if not coin_data_path.exists():
                logger.warning(f"Coin data file not found: {coin_data_path}")
                return []
            
            with open(coin_data_path, 'r') as f:
                data = json.load(f)
                return data.get("contracts", [])
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading coin data: {str(e)}")
            return []
    
    def load_alert_data(self):
        """Load alert data from Ballistic service"""
        alerts = []
        alerts_dir = Path("ballistic_service/data/alerts/triggered")
        
        if not alerts_dir.exists():
            logger.warning(f"Alerts directory not found: {alerts_dir}")
            return []
        
        try:
            for alert_file in alerts_dir.glob("*.json"):
                try:
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                        alerts.append(alert_data)
                except (json.JSONDecodeError, OSError) as e:
                    logger.error(f"Error loading alert {alert_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Error scanning alerts directory: {str(e)}")
        
        return alerts
    
    def load_tweet_data(self):
        """Load tweet data from TrendForger service"""
        try:
            # In a real implementation, this would query the TrendForger service API
            # or load data from a shared database
            
            # For this implementation, attempt to load data from a file
            tweet_data_path = Path("trendforger/data/tweets.json")
            if not tweet_data_path.exists():
                logger.warning(f"Tweet data file not found: {tweet_data_path}")
                return []
            
            with open(tweet_data_path, 'r') as f:
                data = json.load(f)
                return data.get("tweets", [])
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading tweet data: {str(e)}")
            return []
    
    def correlate_memes_with_coins(self):
        """Find correlations between memes and coins"""
        memes = self.load_meme_data()
        coins = self.load_coin_data()
        alerts = self.load_alert_data()
        
        logger.info(f"Correlating {len(memes)} memes with {len(coins)} coins")
        
        # Extract existing correlations to avoid duplicates
        existing_correlations = {c["id"] for c in self.correlation_data["correlations"]}
        
        # Look at recent coins (last 7 days)
        recent_date = (datetime.now() - timedelta(days=7)).isoformat()
        recent_coins = [c for c in coins if c.get("created_at", "") >= recent_date]
        
        new_correlations = []
        
        # First, process existing alerts as they're already correlated
        for alert in alerts:
            correlation_id = f"alert-{alert['id']}"
            
            # Skip if already processed
            if correlation_id in existing_correlations:
                continue
            
            # Create correlation from alert
            correlation = {
                "id": correlation_id,
                "source": "alert",
                "timestamp": datetime.now().isoformat(),
                "meme": alert.get("meme", {}),
                "coin": alert.get("coin", {}),
                "keywords": alert.get("keywords", []),
                "match_score": alert.get("match", {}).get("score", 0),
                "sentiment_score": 0,  # Will calculate below
                "viral_score": 0,      # Will calculate below
                "confirmation_status": "confirmed"  # Alerts are pre-confirmed
            }
            
            # Calculate sentiment and viral scores
            if "text" in correlation["meme"]:
                correlation["sentiment_score"] = self.sentiment_analyzer.analyze(correlation["meme"]["text"])
                correlation["viral_score"] = self.meme_analytics.predict_virality(correlation["meme"]["text"])
            
            new_correlations.append(correlation)
        
        # Now look for new correlations beyond existing alerts
        for meme in memes:
            if not meme.get("processed", False) or "keywords" not in meme:
                continue
            
            meme_keywords = meme.get("keywords", [])
            if not meme_keywords:
                continue
            
            for coin in recent_coins:
                # Skip coins that are already in alerts to avoid duplicates
                coin_address = coin.get("address", "")
                if any(a.get("coin", {}).get("address", "") == coin_address for a in alerts):
                    continue
                
                # Check if any keywords match the coin name or symbol
                coin_name = coin.get("name", "").lower()
                coin_symbol = coin.get("symbol", "").lower()
                
                for keyword in meme_keywords:
                    keyword_lower = keyword.lower()
                    
                    if keyword_lower in coin_name or keyword_lower in coin_symbol:
                        # Calculate match score
                        if keyword_lower == coin_name or keyword_lower == coin_symbol:
                            match_score = 1.0  # Perfect match
                        else:
                            # Calculate partial match score
                            name_ratio = len(keyword_lower) / len(coin_name) if coin_name else 0
                            symbol_ratio = len(keyword_lower) / len(coin_symbol) if coin_symbol else 0
                            match_score = max(name_ratio, symbol_ratio) * 0.8
                        
                        # Only consider if match score is significant
                        if match_score < 0.5:
                            continue
                        
                        # Create a unique ID for this correlation
                        correlation_id = f"manual-{meme['id']}-{coin_address}"
                        
                        # Skip if already processed
                        if correlation_id in existing_correlations:
                            continue
                        
                        # Create correlation
                        correlation = {
                            "id": correlation_id,
                            "source": "manual",
                            "timestamp": datetime.now().isoformat(),
                            "meme": {
                                "id": meme.get("id", ""),
                                "platform": meme.get("platform", ""),
                                "title": meme.get("title", ""),
                                "text": meme.get("text", ""),
                                "url": meme.get("url", ""),
                                "created_at": meme.get("created_utc", "")
                            },
                            "coin": {
                                "name": coin.get("name", ""),
                                "symbol": coin.get("symbol", ""),
                                "address": coin_address,
                                "blockchain": coin.get("blockchain", "ethereum"),
                                "created_at": coin.get("created_at", "")
                            },
                            "keywords": [keyword],
                            "match_score": match_score,
                            "sentiment_score": 0,  # Will calculate below
                            "viral_score": 0,      # Will calculate below
                            "confirmation_status": "potential"  # Not confirmed yet
                        }
                        
                        # Calculate sentiment score
                        meme_text = meme.get("title", "") + " " + meme.get("text", "")
                        correlation["sentiment_score"] = self.sentiment_analyzer.analyze(meme_text)
                        
                        # Calculate viral score
                        correlation["viral_score"] = self.meme_analytics.predict_virality(meme_text)
                        
                        new_correlations.append(correlation)
                        break  # Only create one correlation per meme-coin pair
        
        # Add new correlations to the data
        if new_correlations:
            logger.info(f"Found {len(new_correlations)} new correlations")
            self.correlation_data["correlations"].extend(new_correlations)
            self.correlation_data["last_updated"] = datetime.now().isoformat()
            self._save_correlation_data()
        
        return new_correlations
    
    def correlate_tweets_with_coins(self):
        """Find correlations between influencer tweets and coins"""
        tweets = self.load_tweet_data()
        coins = self.load_coin_data()
        
        logger.info(f"Correlating {len(tweets)} tweets with {len(coins)} coins")
        
        # Extract existing correlations to avoid duplicates
        existing_correlations = {c["id"] for c in self.correlation_data["correlations"]}
        
        # Look at recent coins (last 7 days)
        recent_date = (datetime.now() - timedelta(days=7)).isoformat()
        recent_coins = [c for c in coins if c.get("created_at", "") >= recent_date]
        
        new_correlations = []
        
        for tweet in tweets:
            tweet_keywords = tweet.get("keywords", [])
            if not tweet_keywords:
                # Extract keywords if not already present
                tweet_text = tweet.get("content", "")
                tweet_keywords = self.meme_analytics.extract_keywords(tweet_text)
            
            for coin in recent_coins:
                # Check if any keywords match the coin name or symbol
                coin_name = coin.get("name", "").lower()
                coin_symbol = coin.get("symbol", "").lower()
                
                for keyword in tweet_keywords:
                    keyword_lower = keyword.lower()
                    
                    if keyword_lower in coin_name or keyword_lower in coin_symbol:
                        # Calculate match score
                        if keyword_lower == coin_name or keyword_lower == coin_symbol:
                            match_score = 1.0  # Perfect match
                        else:
                            # Calculate partial match score
                            name_ratio = len(keyword_lower) / len(coin_name) if coin_name else 0
                            symbol_ratio = len(keyword_lower) / len(coin_symbol) if coin_symbol else 0
                            match_score = max(name_ratio, symbol_ratio) * 0.8
                        
                        # Only consider if match score is significant
                        if match_score < 0.5:
                            continue
                        
                        # Create a unique ID for this correlation
                        correlation_id = f"tweet-{tweet.get('tweet_id', '')}-{coin.get('address', '')}"
                        
                        # Skip if already processed
                        if correlation_id in existing_correlations:
                            continue
                        
                        # Create correlation
                        correlation = {
                            "id": correlation_id,
                            "source": "tweet",
                            "timestamp": datetime.now().isoformat(),
                            "tweet": {
                                "id": tweet.get("tweet_id", ""),
                                "author": tweet.get("author", ""),
                                "content": tweet.get("content", ""),
                                "created_at": tweet.get("created_at", "")
                            },
                            "coin": {
                                "name": coin.get("name", ""),
                                "symbol": coin.get("symbol", ""),
                                "address": coin.get("address", ""),
                                "blockchain": coin.get("blockchain", "ethereum"),
                                "created_at": coin.get("created_at", "")
                            },
                            "keywords": [keyword],
                            "match_score": match_score,
                            "sentiment_score": tweet.get("sentiment_score", 0),
                            "viral_score": tweet.get("viral_score", 0),
                            "confirmation_status": "potential"  # Not confirmed yet
                        }
                        
                        # Calculate sentiment and viral scores if not already present
                        if correlation["sentiment_score"] == 0:
                            correlation["sentiment_score"] = self.sentiment_analyzer.analyze(tweet.get("content", ""))
                        
                        if correlation["viral_score"] == 0:
                            correlation["viral_score"] = self.meme_analytics.predict_virality(
                                tweet.get("content", ""), 
                                tweet.get("author", "")
                            )
                        
                        new_correlations.append(correlation)
                        break  # Only create one correlation per tweet-coin pair
        
        # Add new correlations to the data
        if new_correlations:
            logger.info(f"Found {len(new_correlations)} new tweet-coin correlations")
            self.correlation_data["correlations"].extend(new_correlations)
            self.correlation_data["last_updated"] = datetime.now().isoformat()
            self._save_correlation_data()
        
        return new_correlations
    
    def update_all_correlations(self):
        """Update all correlations"""
        meme_correlations = self.correlate_memes_with_coins()
        tweet_correlations = self.correlate_tweets_with_coins()
        
        return {
            "meme_correlations": meme_correlations,
            "tweet_correlations": tweet_correlations,
            "total_new": len(meme_correlations) + len(tweet_correlations),
            "total_overall": len(self.correlation_data["correlations"])
        }
    
    def get_correlations(self, source=None, status=None, limit=None):
        """Get correlations with optional filters"""
        correlations = self.correlation_data["correlations"]
        
        # Apply source filter
        if source:
            correlations = [c for c in correlations if c.get("source") == source]
        
        # Apply status filter
        if status:
            correlations = [c for c in correlations if c.get("confirmation_status") == status]
        
        # Sort by timestamp (newest first)
        correlations = sorted(correlations, key=lambda c: c.get("timestamp", ""), reverse=True)
        
        # Apply limit
        if limit and isinstance(limit, int):
            correlations = correlations[:limit]
        
        return correlations
    
    def update_correlation_status(self, correlation_id, new_status):
        """Update the status of a correlation"""
        # Valid statuses: "potential", "confirmed", "rejected"
        valid_statuses = {"potential", "confirmed", "rejected"}
        if new_status not in valid_statuses:
            logger.error(f"Invalid correlation status: {new_status}")
            return False
        
        # Find the correlation
        for i, correlation in enumerate(self.correlation_data["correlations"]):
            if correlation["id"] == correlation_id:
                # Update the status
                self.correlation_data["correlations"][i]["confirmation_status"] = new_status
                self.correlation_data["correlations"][i]["updated_at"] = datetime.now().isoformat()
                
                # Save the updated data
                self._save_correlation_data()
                
                logger.info(f"Updated correlation {correlation_id} status to {new_status}")
                return True
        
        logger.error(f"Correlation {correlation_id} not found")
        return False


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    correlator = MemeCoinCorrelator()
    
    # Update correlations
    result = correlator.update_all_correlations()
    print(f"Updated correlations: {result['total_new']} new, {result['total_overall']} total")
    
    # Get recent correlations
    recent = correlator.get_correlations(limit=5)
    print("\nRecent correlations:")
    for correlation in recent:
        source_type = "Tweet" if correlation["source"] == "tweet" else "Meme"
        coin_name = correlation["coin"]["name"]
        match_score = correlation["match_score"]
        status = correlation["confirmation_status"]
        
        print(f"- {source_type} → {coin_name} (Match: {match_score:.2f}, Status: {status})")
