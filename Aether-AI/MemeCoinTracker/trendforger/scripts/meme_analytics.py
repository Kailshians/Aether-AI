#!/usr/bin/env python3
"""
Meme Analytics - Analyzes meme content for virality prediction
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime
import random

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from analysis.sentiment.vader_custom import VaderSentimentAnalyzer

# Configure logging
logger = logging.getLogger("meme_analytics")

class MemeAnalytics:
    """Analytics for meme content to predict virality and potential"""
    
    def __init__(self):
        """Initialize the MemeAnalytics"""
        # Initialize sentiment analyzer
        self.sentiment_analyzer = VaderSentimentAnalyzer()
        
        logger.info("MemeAnalytics initialized")
    
    def extract_keywords(self, content):
        """Extract relevant keywords from content"""
        # A simple keyword extractor for demo purposes
        # In a real implementation, this would use more sophisticated NLP
        
        # Convert to lowercase and remove special characters
        cleaned_content = re.sub(r'[^\w\s#]', '', content.lower())
        
        # Extract hashtags first
        hashtags = re.findall(r'#(\w+)', content)
        
        # Basic tokenization
        words = cleaned_content.split()
        
        # Remove common stop words
        stop_words = {"a", "an", "the", "and", "or", "but", "is", "are", "was", "were", 
                      "be", "been", "being", "in", "on", "at", "to", "for", "with", "by"}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Add hashtags to the keywords
        keywords = hashtags + filtered_words
        
        # Remove duplicates while preserving order
        unique_keywords = []
        seen = set()
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:10]  # Return top 10 keywords
    
    def analyze_sentiment(self, content):
        """Analyze the sentiment of content"""
        # Use our custom VADER sentiment analyzer
        sentiment_score = self.sentiment_analyzer.analyze(content)
        
        # Return the compound score (-1 to 1 range)
        return sentiment_score
    
    def predict_virality(self, content, author=None):
        """Predict the virality potential of content"""
        # In a real implementation, this would use a trained model
        # For this demo, we'll use a simple heuristic approach
        
        # Extract features
        word_count = len(content.split())
        contains_hashtag = '#' in content
        contains_emoji = any(c in content for c in "😂🔥👀💯🚀💰")
        sentiment = self.analyze_sentiment(content)
        
        # Calculate base score
        base_score = 0.5  # Start at middle
        
        # Adjust based on content features
        if word_count < 10:
            base_score += 0.1  # Shorter content tends to do better
        if contains_hashtag:
            base_score += 0.1  # Hashtags increase visibility
        if contains_emoji:
            base_score += 0.15  # Emojis tend to increase engagement
        
        # Sentiment impacts - extreme sentiments (positive or negative) tend to go viral
        sentiment_impact = abs(sentiment) * 0.3
        base_score += sentiment_impact
        
        # Adjust for author influence if provided
        if author:
            influence_scores = {
                "elonmusk": 0.9,
                "realDonaldTrump": 0.85,
                # Add more influencers as needed
            }
            author_influence = influence_scores.get(author.lower(), 0.5)
            base_score = (base_score + author_influence) / 2  # Average with author influence
        
        # Ensure score is in 0-1 range
        viral_score = max(0, min(1, base_score))
        
        return viral_score
    
    def compare_to_historical(self, keywords, sentiment_score, viral_score):
        """Compare analysis to historical viral memes"""
        # In a real implementation, this would query a database of historical memes
        # and compare features to identify similar patterns
        
        # For this demo, we'll return a simulated comparison
        return {
            "similarity_score": random.uniform(0.6, 0.9),
            "historical_matches": [
                {
                    "keyword": keywords[0] if keywords else "unknown",
                    "timestamp": (datetime.now().replace(day=1, month=1)).isoformat(),
                    "viral_score": 0.85,
                    "outcome": "Successful meme coin"
                }
            ],
            "success_probability": random.uniform(0.3, 0.7)
        }
    
    def get_related_coins(self, keywords):
        """Get related existing coins based on keywords"""
        # In a real implementation, this would query a database of existing coins
        # or use an API to find related coins
        
        # For this demo, we'll return simulated related coins
        related_coins = []
        
        # Only generate if we have keywords
        if keywords:
            for i in range(min(3, len(keywords))):
                related_coins.append({
                    "name": f"{keywords[i].title()}Coin",
                    "symbol": keywords[i][:4].upper(),
                    "address": f"0x{hash(keywords[i])%10**40:040x}",
                    "blockchain": "ethereum" if i % 2 == 0 else "solana",
                    "market_cap": random.uniform(50000, 5000000),
                    "similarity": random.uniform(0.7, 0.95)
                })
        
        return related_coins
    
    def analyze_content_full(self, content, author=None):
        """Perform a full analysis of content"""
        # Extract keywords
        keywords = self.extract_keywords(content)
        
        # Analyze sentiment
        sentiment_score = self.analyze_sentiment(content)
        
        # Predict virality
        viral_score = self.predict_virality(content, author)
        
        # Compare to historical data
        historical = self.compare_to_historical(keywords, sentiment_score, viral_score)
        
        # Get related coins
        related_coins = self.get_related_coins(keywords)
        
        # Compile the full analysis
        full_analysis = {
            "content": content,
            "author": author,
            "timestamp": datetime.now().isoformat(),
            "keywords": keywords,
            "sentiment_score": sentiment_score,
            "viral_score": viral_score,
            "historical_comparison": historical,
            "related_coins": related_coins,
            "overall_potential": (viral_score + historical["success_probability"]) / 2
        }
        
        return full_analysis


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    analytics = MemeAnalytics()
    
    # Test content
    test_content = "Just bought some #Dogecoin! 🚀 To the moon! Crypto is the future 💰"
    
    # Extract keywords
    keywords = analytics.extract_keywords(test_content)
    print(f"Keywords: {keywords}")
    
    # Analyze sentiment
    sentiment = analytics.analyze_sentiment(test_content)
    print(f"Sentiment score: {sentiment}")
    
    # Predict virality
    virality = analytics.predict_virality(test_content, "elonmusk")
    print(f"Virality score: {virality}")
    
    # Full analysis
    full = analytics.analyze_content_full(test_content, "elonmusk")
    print("\nFull Analysis:")
    print(json.dumps(full, indent=2))
