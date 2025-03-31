#!/usr/bin/env python3
"""
Alert Optimizer - Reduces false positives in meme coin predictions
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from analysis.sentiment.vader_custom import VaderSentimentAnalyzer
from ballistic_service.scripts.anti_scam import AntiScamAnalyzer
from analysis.onchain.dex_metrics import DexMetricsAnalyzer
from analysis.onchain.whale_tracker import WhaleTracker

# Configure logging
logger = logging.getLogger("alert_optimizer")

class AlertOptimizer:
    """Optimizer for reducing false positives in meme coin alerts"""
    
    def __init__(self):
        """Initialize the AlertOptimizer"""
        self.sentiment_analyzer = VaderSentimentAnalyzer()
        self.anti_scam = AntiScamAnalyzer()
        self.dex_metrics = DexMetricsAnalyzer()
        self.whale_tracker = WhaleTracker()
        
        # Load optimization rules
        self.rules = self._load_optimization_rules()
        
        logger.info("AlertOptimizer initialized")
    
    def _load_optimization_rules(self):
        """Load optimization rules from configuration"""
        # Default rules
        default_rules = {
            "minimum_match_score": 0.6,
            "minimum_safety_score": 0.4,
            "maximum_whale_concentration": 0.8,  # 80%
            "minimum_sentiment_score": -0.5,     # Allow somewhat negative sentiment
            "minimum_meme_virality": 0.3,
            "keyword_blacklist": ["scam", "rugpull", "fake", "honeypot"],
            "minimum_meme_age_hours": 0,         # Accept any age
            "minimum_coin_age_hours": 0          # Accept any age
        }
        
        # Try to load custom rules from file
        rules_path = Path("analysis/cross_service/config/optimization_rules.json")
        if rules_path.exists():
            try:
                with open(rules_path, 'r') as f:
                    custom_rules = json.load(f)
                    # Update default rules with custom ones
                    default_rules.update(custom_rules)
                    logger.info("Loaded custom optimization rules")
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Error loading optimization rules: {str(e)}")
        
        return default_rules
    
    def optimize_alert(self, alert_data):
        """Optimize and score an alert to reduce false positives"""
        logger.info(f"Optimizing alert {alert_data.get('id', 'unknown')}")
        
        # Extract key data from alert
        match_score = alert_data.get("match", {}).get("score", 0)
        safety_score = alert_data.get("safety", {}).get("score", 0)
        
        # Extract meme data
        meme = alert_data.get("meme", {})
        meme_text = (meme.get("title", "") + " " + meme.get("text", "")).strip()
        
        # Extract coin data
        coin = alert_data.get("coin", {})
        coin_address = coin.get("address", "")
        blockchain = coin.get("blockchain", "ethereum")
        
        # Calculate additional metrics
        sentiment_score = self.sentiment_analyzer.analyze(meme_text) if meme_text else 0
        
        # Check wallet concentration (whales)
        whale_concentration = 0
        if coin_address:
            whale_analysis = self.whale_tracker.analyze_whale_concentration(coin_address, blockchain)
            if whale_analysis:
                whale_concentration = whale_analysis.get("concentration_metrics", {}).get("top5_percentage", 0) / 100
        
        # Check meme virality
        meme_virality = 0
        from trendforger.scripts.meme_analytics import MemeAnalytics
        meme_analytics = MemeAnalytics()
        if meme_text:
            meme_virality = meme_analytics.predict_virality(meme_text)
        
        # Calculate ages
        meme_age_hours = 0
        if meme.get("created_at"):
            try:
                meme_time = datetime.fromisoformat(meme["created_at"])
                meme_age_hours = (datetime.now() - meme_time).total_seconds() / 3600
            except (ValueError, TypeError):
                pass
        
        coin_age_hours = 0
        if coin.get("created_at"):
            try:
                coin_time = datetime.fromisoformat(coin["created_at"])
                coin_age_hours = (datetime.now() - coin_time).total_seconds() / 3600
            except (ValueError, TypeError):
                pass
        
        # Check for blacklisted keywords
        keywords = alert_data.get("keywords", [])
        blacklisted_keywords = [kw for kw in keywords if kw.lower() in self.rules["keyword_blacklist"]]
        
        # Create optimization results
        optimization_results = {
            "original_match_score": match_score,
            "original_safety_score": safety_score,
            "sentiment_score": sentiment_score,
            "whale_concentration": whale_concentration,
            "meme_virality": meme_virality,
            "meme_age_hours": meme_age_hours,
            "coin_age_hours": coin_age_hours,
            "blacklisted_keywords": blacklisted_keywords,
            "optimization_timestamp": datetime.now().isoformat()
        }
        
        # Apply rules to determine if alert should be triggered
        should_trigger = True
        rejection_reasons = []
        
        if match_score < self.rules["minimum_match_score"]:
            should_trigger = False
            rejection_reasons.append(f"Match score too low: {match_score:.2f} < {self.rules['minimum_match_score']}")
        
        if safety_score < self.rules["minimum_safety_score"]:
            should_trigger = False
            rejection_reasons.append(f"Safety score too low: {safety_score:.2f} < {self.rules['minimum_safety_score']}")
        
        if whale_concentration > self.rules["maximum_whale_concentration"]:
            should_trigger = False
            rejection_reasons.append(f"Whale concentration too high: {whale_concentration*100:.2f}% > {self.rules['maximum_whale_concentration']*100}%")
        
        if sentiment_score < self.rules["minimum_sentiment_score"]:
            should_trigger = False
            rejection_reasons.append(f"Sentiment too negative: {sentiment_score:.2f} < {self.rules['minimum_sentiment_score']}")
        
        if meme_virality < self.rules["minimum_meme_virality"]:
            should_trigger = False
            rejection_reasons.append(f"Meme virality too low: {meme_virality:.2f} < {self.rules['minimum_meme_virality']}")
        
        if blacklisted_keywords:
            should_trigger = False
            rejection_reasons.append(f"Blacklisted keywords found: {', '.join(blacklisted_keywords)}")
        
        if meme_age_hours < self.rules["minimum_meme_age_hours"]:
            should_trigger = False
            rejection_reasons.append(f"Meme too new: {meme_age_hours:.2f}h < {self.rules['minimum_meme_age_hours']}h")
        
        if coin_age_hours < self.rules["minimum_coin_age_hours"]:
            should_trigger = False
            rejection_reasons.append(f"Coin too new: {coin_age_hours:.2f}h < {self.rules['minimum_coin_age_hours']}h")
        
        # Add results to optimization data
        optimization_results["should_trigger"] = should_trigger
        optimization_results["rejection_reasons"] = rejection_reasons
        
        # Calculate an optimized confidence score
        confidence_factors = [
            match_score,
            safety_score,
            (sentiment_score + 1) / 2,  # Convert from -1:1 to 0:1 range
            1 - whale_concentration,  # Lower concentration is better
            meme_virality
        ]
        
        # Only include non-zero factors
        valid_factors = [f for f in confidence_factors if f > 0]
        if valid_factors:
            # Weighted average with more emphasis on match and safety
            weights = [0.3, 0.3, 0.15, 0.1, 0.15]  # Should sum to 1
            optimized_score = sum(f * w for f, w in zip(valid_factors, weights[:len(valid_factors)]))
            
            # Adjust weights if we have fewer factors
            if len(valid_factors) < len(weights):
                weight_sum = sum(weights[:len(valid_factors)])
                if weight_sum > 0:
                    optimized_score /= weight_sum
        else:
            optimized_score = 0
        
        optimization_results["optimized_score"] = optimized_score
        
        return optimization_results
    
    def batch_optimize_alerts(self, alerts_dir=None):
        """Optimize a batch of alerts from the alerts directory"""
        # Default to the triggered alerts directory
        if alerts_dir is None:
            alerts_dir = Path("ballistic_service/data/alerts/triggered")
        else:
            alerts_dir = Path(alerts_dir)
        
        if not alerts_dir.exists():
            logger.error(f"Alerts directory not found: {alerts_dir}")
            return []
        
        logger.info(f"Batch optimizing alerts in {alerts_dir}")
        
        results = []
        
        try:
            for alert_file in alerts_dir.glob("*.json"):
                try:
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                    
                    # Optimize the alert
                    optimization_result = self.optimize_alert(alert_data)
                    
                    # Add alert ID for reference
                    optimization_result["alert_id"] = alert_data.get("id", "unknown")
                    
                    # Add to results
                    results.append(optimization_result)
                    
                    # Update the alert file with optimization results
                    alert_data["optimization"] = optimization_result
                    
                    with open(alert_file, 'w') as f:
                        json.dump(alert_data, f, indent=2)
                    
                except (json.JSONDecodeError, OSError) as e:
                    logger.error(f"Error processing alert {alert_file}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in batch optimization: {str(e)}")
        
        return results
    
    def update_optimization_rule(self, rule_name, rule_value):
        """Update a specific optimization rule"""
        if rule_name not in self.rules:
            logger.error(f"Unknown optimization rule: {rule_name}")
            return False
        
        # Validate rule value type matches the existing rule
        existing_type = type(self.rules[rule_name])
        if not isinstance(rule_value, existing_type):
            logger.error(f"Invalid type for rule {rule_name}: expected {existing_type.__name__}, got {type(rule_value).__name__}")
            return False
        
        # Update the rule
        self.rules[rule_name] = rule_value
        
        # Save the updated rules
        rules_path = Path("analysis/cross_service/config/optimization_rules.json")
        rules_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(rules_path, 'w') as f:
                json.dump(self.rules, f, indent=2)
            
            logger.info(f"Updated optimization rule {rule_name} to {rule_value}")
            return True
        except OSError as e:
            logger.error(f"Error saving optimization rules: {str(e)}")
            return False


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    optimizer = AlertOptimizer()
    
    # Test with a sample alert
    sample_alert = {
        "id": "test-alert-1",
        "created_at": datetime.now().isoformat(),
        "meme": {
            "id": "test-meme-1",
            "platform": "reddit",
            "title": "This DOGE meme is going to the moon!",
            "text": "Look at this awesome Dogecoin meme 🚀 🚀 🚀",
            "created_at": (datetime.now() - timedelta(days=1)).isoformat()
        },
        "coin": {
            "name": "DogeMoon",
            "symbol": "DOGMN",
            "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "blockchain": "ethereum",
            "created_at": datetime.now().isoformat()
        },
        "match": {
            "keyword": "doge",
            "score": 0.85,
            "type": "name"
        },
        "keywords": ["doge", "moon"],
        "safety": {
            "score": 0.65,
            "risk_factors": ["New Contract", "Low Liquidity"]
        }
    }
    
    # Optimize the sample alert
    optimization = optimizer.optimize_alert(sample_alert)
    
    print(f"Alert optimization results:")
    print(f"Match score: {optimization['original_match_score']:.2f}")
    print(f"Safety score: {optimization['original_safety_score']:.2f}")
    print(f"Sentiment score: {optimization['sentiment_score']:.2f}")
    print(f"Meme virality: {optimization['meme_virality']:.2f}")
    print(f"Whale concentration: {optimization['whale_concentration']*100:.2f}%")
    print(f"Optimized score: {optimization['optimized_score']:.2f}")
    print(f"Should trigger: {optimization['should_trigger']}")
    
    if not optimization['should_trigger']:
        print("Rejection reasons:")
        for reason in optimization['rejection_reasons']:
            print(f"- {reason}")
