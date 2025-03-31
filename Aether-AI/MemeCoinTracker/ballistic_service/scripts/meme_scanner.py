#!/usr/bin/env python3
"""
Meme Scanner - Scans social media for trending memes and extracts keywords
"""

import os
import sys
import json
import logging
import re
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
import praw
import tweepy
import spacy
from spacy.lang.en import English

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET,
    MEME_SOURCES
)

# Configure logging
logger = logging.getLogger("meme_scanner")

class MemeScanner:
    """Scanner for trending memes on social media platforms"""
    
    def __init__(self):
        """Initialize the MemeScanner with APIs and NLP models"""
        self.init_reddit()
        self.init_twitter()
        
        # Initialize NLP for keyword extraction
        try:
            # Try to load a more comprehensive model if available
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy en_core_web_sm model")
        except OSError:
            # Fall back to basic English tokenizer
            self.nlp = English()
            logger.warning("Using basic English tokenizer - for better results install en_core_web_sm")
        
        # Load existing keyword data if available
        self.meme_data_path = Path("ballistic_service/data/raw_memes.json")
        self.meme_data = self._load_meme_data()
        
        logger.info("MemeScanner initialized")
    
    def init_reddit(self):
        """Initialize Reddit API client"""
        try:
            self.reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )
            logger.info("Reddit API client initialized")
        except Exception as e:
            self.reddit = None
            logger.error(f"Failed to initialize Reddit API: {str(e)}")
    
    def init_twitter(self):
        """Initialize Twitter API client"""
        try:
            auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
            auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
            self.twitter = tweepy.API(auth)
            logger.info("Twitter API client initialized")
        except Exception as e:
            self.twitter = None
            logger.error(f"Failed to initialize Twitter API: {str(e)}")
    
    def _load_meme_data(self):
        """Load existing meme data from JSON file"""
        if self.meme_data_path.exists():
            try:
                with open(self.meme_data_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Error loading meme data: {str(e)}")
        
        return {"memes": []}
    
    def _save_meme_data(self):
        """Save meme data to JSON file"""
        try:
            with open(self.meme_data_path, 'w') as f:
                json.dump(self.meme_data, f, indent=2)
        except OSError as e:
            logger.error(f"Error saving meme data: {str(e)}")
    
    def scan_trending_memes(self):
        """Scan social media platforms for trending memes"""
        new_memes = []
        
        # Scan Reddit for memes
        if self.reddit:
            for source in [s for s in MEME_SOURCES if s["platform"] == "reddit"]:
                try:
                    subreddit_name = source["subreddit"]
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Get hot posts from subreddit
                    for post in subreddit.hot(limit=10):
                        # Skip posts we've already processed
                        if any(m["id"] == f"reddit-{post.id}" for m in self.meme_data["memes"]):
                            continue
                        
                        meme_data = {
                            "id": f"reddit-{post.id}",
                            "platform": "reddit",
                            "subreddit": subreddit_name,
                            "title": post.title,
                            "text": post.selftext if hasattr(post, "selftext") else "",
                            "url": post.url,
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "created_utc": post.created_utc,
                            "timestamp": datetime.now().isoformat(),
                            "processed": False
                        }
                        
                        new_memes.append(meme_data)
                        self.meme_data["memes"].append(meme_data)
                
                except Exception as e:
                    logger.error(f"Error scanning Reddit {source['subreddit']}: {str(e)}")
        
        # Scan Twitter for memes
        if self.twitter:
            for source in [s for s in MEME_SOURCES if s["platform"] == "twitter"]:
                try:
                    query = " OR ".join(source["track"])
                    
                    # Get recent tweets with the keywords
                    tweets = self.twitter.search_tweets(q=query, count=20, result_type="popular")
                    
                    for tweet in tweets:
                        # Skip tweets we've already processed
                        if any(m["id"] == f"twitter-{tweet.id}" for m in self.meme_data["memes"]):
                            continue
                        
                        meme_data = {
                            "id": f"twitter-{tweet.id}",
                            "platform": "twitter",
                            "user": tweet.user.screen_name,
                            "text": tweet.text,
                            "favorite_count": tweet.favorite_count,
                            "retweet_count": tweet.retweet_count,
                            "created_at": tweet.created_at.isoformat(),
                            "timestamp": datetime.now().isoformat(),
                            "processed": False
                        }
                        
                        new_memes.append(meme_data)
                        self.meme_data["memes"].append(meme_data)
                
                except Exception as e:
                    logger.error(f"Error scanning Twitter for {source['track']}: {str(e)}")
        
        # Save the updated meme data
        if new_memes:
            logger.info(f"Found {len(new_memes)} new memes")
            self._save_meme_data()
        
        return new_memes
    
    def extract_keywords(self, meme_data):
        """Extract relevant keywords from meme data using NLP"""
        # Combine title and text for processing
        text = ""
        if "title" in meme_data:
            text += meme_data["title"] + " "
        if "text" in meme_data:
            text += meme_data["text"]
        
        # Process the text
        doc = self.nlp(text)
        
        # Extract keywords (nouns, proper nouns, and hashtags)
        keywords = []
        
        # Extract hashtags first
        hashtags = re.findall(r'#(\w+)', text)
        keywords.extend(hashtags)
        
        # Extract named entities if available
        if hasattr(doc, "ents"):
            for ent in doc.ents:
                if ent.label_ in ("PERSON", "ORG", "PRODUCT", "WORK_OF_ART"):
                    keywords.append(ent.text.lower())
        
        # Extract nouns and proper nouns
        for token in doc:
            if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 2:
                keywords.append(token.text.lower())
        
        # Remove duplicates and normalize
        keywords = list(set(keywords))
        
        # Update the meme entry to mark it as processed
        for i, meme in enumerate(self.meme_data["memes"]):
            if meme["id"] == meme_data["id"]:
                self.meme_data["memes"][i]["processed"] = True
                self.meme_data["memes"][i]["keywords"] = keywords
                break
        
        # Save the updated data
        self._save_meme_data()
        
        return keywords
    
    def clean_old_memes(self, days=7):
        """Clean memes older than specified days"""
        if not self.meme_data or "memes" not in self.meme_data:
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter out old memes
        original_count = len(self.meme_data["memes"])
        self.meme_data["memes"] = [
            meme for meme in self.meme_data["memes"]
            if datetime.fromisoformat(meme["timestamp"]) > cutoff_date
        ]
        
        removed_count = original_count - len(self.meme_data["memes"])
        if removed_count > 0:
            logger.info(f"Removed {removed_count} old memes")
            self._save_meme_data()


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    scanner = MemeScanner()
    memes = scanner.scan_trending_memes()
    
    if memes:
        for meme in memes:
            print(f"Found meme: {meme['id']}")
            keywords = scanner.extract_keywords(meme)
            print(f"Keywords: {keywords}\n")
    else:
        print("No new memes found")
