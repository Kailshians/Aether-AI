#!/usr/bin/env python3
"""
Keyword Database - SQLite database for crypto-related keywords and slang
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from config import KEYWORD_DB_PATH

# Configure logging
logger = logging.getLogger("keyword_db")

class KeywordDatabase:
    """SQLite database for managing crypto-related keywords and slang"""
    
    def __init__(self, db_path=KEYWORD_DB_PATH):
        """Initialize the keyword database"""
        self.db_path = db_path
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create database and tables if they don't exist
        self._init_db()
        
        logger.info("Keyword database initialized")
    
    def _init_db(self):
        """Initialize the database schema"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create keyword table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                relevance REAL NOT NULL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create slang table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS slang (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL UNIQUE,
                definition TEXT NOT NULL,
                sentiment REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create meme_keywords table for tracking keywords per meme
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS meme_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meme_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(meme_id, keyword)
            )
            ''')
            
            conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def add_keyword(self, keyword, category, relevance=1.0):
        """Add a new keyword to the database"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR REPLACE INTO keywords (keyword, category, relevance) VALUES (?, ?, ?)",
                (keyword.lower(), category, relevance)
            )
            
            conn.commit()
            logger.debug(f"Added keyword: {keyword} ({category})")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error adding keyword {keyword}: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def add_slang(self, term, definition, sentiment=0.0):
        """Add a new slang term to the database"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR REPLACE INTO slang (term, definition, sentiment) VALUES (?, ?, ?)",
                (term.lower(), definition, sentiment)
            )
            
            conn.commit()
            logger.debug(f"Added slang term: {term}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error adding slang term {term}: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def track_meme_keyword(self, meme_id, keyword):
        """Track a keyword extracted from a meme"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR IGNORE INTO meme_keywords (meme_id, keyword) VALUES (?, ?)",
                (meme_id, keyword.lower())
            )
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error tracking keyword {keyword} for meme {meme_id}: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_keywords_by_category(self, category):
        """Get all keywords for a specific category"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return results as dictionaries
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM keywords WHERE category = ? ORDER BY relevance DESC",
                (category,)
            )
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Error getting keywords for category {category}: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_all_keywords(self):
        """Get all keywords from the database"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return results as dictionaries
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM keywords ORDER BY category, relevance DESC")
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Error getting all keywords: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_slang_terms(self):
        """Get all slang terms from the database"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return results as dictionaries
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM slang ORDER BY sentiment DESC")
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Error getting slang terms: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_popular_keywords(self, limit=10):
        """Get the most frequently used keywords in memes"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT keyword, COUNT(*) as count 
                FROM meme_keywords 
                GROUP BY keyword 
                ORDER BY count DESC 
                LIMIT ?
            """, (limit,))
            
            return cursor.fetchall()
            
        except sqlite3.Error as e:
            logger.error(f"Error getting popular keywords: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def initialize_default_data(self):
        """Initialize database with default crypto keywords and slang"""
        # Add some default crypto categories
        categories = ["meme", "defi", "nft", "exchange", "layer1", "layer2", "stablecoin"]
        
        # Add some default keywords
        default_keywords = [
            # Meme keywords
            ("doge", "meme", 1.0),
            ("shiba", "meme", 1.0),
            ("pepe", "meme", 1.0),
            ("moon", "meme", 0.8),
            ("rocket", "meme", 0.7),
            ("ape", "meme", 0.7),
            ("wojak", "meme", 0.6),
            
            # DeFi keywords
            ("defi", "defi", 1.0),
            ("yield", "defi", 0.9),
            ("farm", "defi", 0.8),
            ("staking", "defi", 0.8),
            ("liquidity", "defi", 0.7),
            
            # Exchange keywords
            ("binance", "exchange", 1.0),
            ("coinbase", "exchange", 1.0),
            ("kraken", "exchange", 0.9),
            ("dex", "exchange", 0.8)
        ]
        
        # Add some default slang terms
        default_slang = [
            ("hodl", "Hold on for dear life - to keep your crypto assets", 0.7),
            ("fud", "Fear, uncertainty and doubt - negative sentiment", -0.7),
            ("fomo", "Fear of missing out - driving buying behavior", 0.3),
            ("rekt", "Wrecked - lost a lot of money", -0.8),
            ("pump", "Rapid price increase", 0.6),
            ("dump", "Rapid price decrease", -0.6),
            ("whale", "Large holder of crypto", 0.2),
            ("rugpull", "Scam where developers abandon the project", -0.9)
        ]
        
        # Add all default data
        for keyword, category, relevance in default_keywords:
            self.add_keyword(keyword, category, relevance)
        
        for term, definition, sentiment in default_slang:
            self.add_slang(term, definition, sentiment)
        
        logger.info("Initialized default keyword and slang data")


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Create test database in memory
    db = KeywordDatabase(":memory:")
    
    # Initialize with default data
    db.initialize_default_data()
    
    # Print all keywords
    print("All Keywords:")
    for kw in db.get_all_keywords():
        print(f"- {kw['keyword']} ({kw['category']}): {kw['relevance']}")
    
    print("\nAll Slang Terms:")
    for term in db.get_slang_terms():
        print(f"- {term['term']}: {term['definition']} ({term['sentiment']})")
    
    # Add a test keyword
    db.add_keyword("testkeyword", "test", 0.5)
    
    # Track keywords for a test meme
    db.track_meme_keyword("test-meme-1", "doge")
    db.track_meme_keyword("test-meme-1", "moon")
    db.track_meme_keyword("test-meme-2", "doge")
    
    # Get popular keywords
    print("\nPopular Keywords:")
    for keyword, count in db.get_popular_keywords():
        print(f"- {keyword}: {count} occurrences")
