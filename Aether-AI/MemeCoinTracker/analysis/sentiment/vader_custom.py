#!/usr/bin/env python3
"""
Custom VADER Sentiment Analyzer for Crypto Content
This module extends the VADER sentiment analyzer with crypto-specific lexicon
"""

import os
import sys
import logging
from pathlib import Path
import re
import math

# Try to import VADER from NLTK
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer, NEGATE
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logging.warning("NLTK VADER not available - using simplified sentiment analysis")

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Configure logging
logger = logging.getLogger("vader_custom")

class VaderSentimentAnalyzer:
    """Custom VADER Sentiment Analyzer for crypto content"""
    
    def __init__(self):
        """Initialize the sentiment analyzer with custom lexicon"""
        self.lexicon_path = Path("analysis/sentiment/crypto_lexicon.txt")
        
        # Initialize VADER if available
        if VADER_AVAILABLE:
            self.vader = SentimentIntensityAnalyzer()
            
            # Add custom lexicon
            if self.lexicon_path.exists():
                self._load_custom_lexicon()
            else:
                # Create default lexicon if it doesn't exist
                self._create_default_lexicon()
                self._load_custom_lexicon()
            
            logger.info("VADER sentiment analyzer initialized with custom lexicon")
        else:
            # Create a simple fallback analyzer
            self.crypto_lexicon = self._create_fallback_lexicon()
            logger.info("Fallback sentiment analyzer initialized")
    
    def _create_default_lexicon(self):
        """Create a default crypto lexicon file"""
        default_lexicon = """
# Crypto Lexicon for Sentiment Analysis
# Format: term[tab]sentiment_value
# Sentiment values range from -4 (very negative) to +4 (very positive)

# Positive terms
moon	3.9
hodl	2.5
bullish	3.0
lambo	2.8
diamond hands	3.2
to the moon	3.9
rocket	3.0
🚀	3.5
pump	2.0
gainz	3.0
rekt	-3.0
fud	-2.5
based	2.0
btfd	2.5
diamond	2.8
hands	1.5
diamond hands	3.4
gm	1.5
wagmi	3.0
bullrun	3.5
altseason	2.5
ape	1.5
ape in	2.0
hold	1.8
holding	1.8
#HODL	3.0

# Negative terms
rugpull	-3.8
rug pull	-3.8
rug	-3.0
dump	-2.5
ponzi	-3.5
scam	-3.5
bearish	-2.5
shitcoin	-2.5
shilling	-1.5
fomo	-1.0
ngmi	-2.0
bear market	-2.5
crash	-3.0
dumping	-2.8
dumped	-2.8
exit scam	-3.8
honeypot	-3.5
scamcoin	-3.5

# Neutral/context-dependent
degen	0.0
airdrop	1.5
staking	1.0
yield	1.0
mining	0.5
nft	0.5
ico	0.0
token	0.0
whale	0.0
gas	-0.5
fees	-1.0
"""
        
        try:
            with open(self.lexicon_path, 'w') as f:
                f.write(default_lexicon.strip())
            logger.info(f"Created default crypto lexicon at {self.lexicon_path}")
        except OSError as e:
            logger.error(f"Error creating default lexicon: {str(e)}")
    
    def _load_custom_lexicon(self):
        """Load custom lexicon into VADER sentiment analyzer"""
        try:
            with open(self.lexicon_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) == 2:
                        term, score = parts
                        try:
                            score = float(score)
                            # Add to VADER lexicon
                            self.vader.lexicon[term] = score
                        except ValueError:
                            logger.warning(f"Invalid score format for term '{term}': {score}")
            
            logger.info(f"Loaded custom crypto lexicon with {len(self.vader.lexicon)} terms")
        except OSError as e:
            logger.error(f"Error loading custom lexicon: {str(e)}")
    
    def _create_fallback_lexicon(self):
        """Create a simple lexicon for fallback sentiment analysis"""
        # Basic crypto sentiment lexicon with values between -1 and 1
        return {
            # Positive terms
            "moon": 0.9, "hodl": 0.6, "bullish": 0.7, "lambo": 0.7,
            "diamond hands": 0.8, "to the moon": 0.9, "rocket": 0.7,
            "🚀": 0.9, "pump": 0.5, "gainz": 0.7, "based": 0.5,
            "btfd": 0.6, "diamond": 0.7, "hands": 0.3, "gm": 0.3,
            "wagmi": 0.7, "bullrun": 0.8, "altseason": 0.6, "ape": 0.3,
            "ape in": 0.5, "hold": 0.4, "holding": 0.4,
            
            # Negative terms
            "rugpull": -0.9, "rug pull": -0.9, "rug": -0.7, "dump": -0.6,
            "ponzi": -0.9, "scam": -0.9, "bearish": -0.6, "shitcoin": -0.6,
            "shilling": -0.4, "fomo": -0.2, "ngmi": -0.5, "bear market": -0.6,
            "crash": -0.7, "dumping": -0.7, "dumped": -0.7, "exit scam": -0.9,
            "honeypot": -0.8, "scamcoin": -0.8, "rekt": -0.7, "fud": -0.6,
            
            # Neutral/context-dependent
            "degen": 0.0, "airdrop": 0.3, "staking": 0.2, "yield": 0.2,
            "mining": 0.1, "nft": 0.1, "ico": 0.0, "token": 0.0,
            "whale": 0.0, "gas": -0.1, "fees": -0.2
        }
    
    def _fallback_analyze(self, text):
        """Fallback sentiment analysis when VADER is not available"""
        text = text.lower()
        words = re.findall(r'\b\w+\b|[^\w\s]', text)
        
        # Check for negation words
        negation_words = {"no", "not", "never", "none", "nobody", "nothing", "nowhere", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't", "hadn't", "don't", "doesn't", "didn't", "won't", "wouldn't", "can't", "couldn't", "shouldn't"}
        
        sentiment_score = 0
        word_count = 0
        negation_active = False
        
        for i, word in enumerate(words):
            # Check for negation
            if word in negation_words:
                negation_active = True
                continue
            
            # Reset negation after 3 words
            if negation_active and i > 0 and (i - words.index(list(negation_words)[0]) if any(w in negation_words for w in words[:i]) else 0) > 3:
                negation_active = False
            
            # Check word sentiment
            if word in self.crypto_lexicon:
                score = self.crypto_lexicon[word]
                
                # Apply negation if active
                if negation_active:
                    score = -score
                
                sentiment_score += score
                word_count += 1
        
        # Normalize score to -1 to 1 range
        if word_count > 0:
            compound_score = sentiment_score / (word_count + math.log(len(words) + 1))
            # Ensure score is between -1 and 1
            compound_score = max(-1, min(1, compound_score))
        else:
            compound_score = 0
        
        return compound_score
    
    def analyze(self, text):
        """Analyze the sentiment of text"""
        if VADER_AVAILABLE:
            # Use VADER with our custom lexicon
            scores = self.vader.polarity_scores(text)
            return scores['compound']  # Return the compound score (-1 to 1)
        else:
            # Use our simple fallback analyzer
            return self._fallback_analyze(text)


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    analyzer = VaderSentimentAnalyzer()
    
    # Test some crypto-related text
    test_texts = [
        "Just bought some Dogecoin! To the moon! 🚀",
        "This token is a complete scam, clear rugpull incoming.",
        "HODL strong, diamond hands will be rewarded!",
        "The market is crashing, everything is dumping.",
        "New NFT project looks interesting, might be worth investing."
    ]
    
    for text in test_texts:
        score = analyzer.analyze(text)
        sentiment = "positive" if score > 0.05 else "negative" if score < -0.05 else "neutral"
        print(f"Text: {text}")
        print(f"Sentiment score: {score:.2f} ({sentiment})\n")
