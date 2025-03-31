#!/usr/bin/env python3
"""
TrendForger Service - Creator tokenization service and influencer tweet tracker
This service monitors influential figures and helps create tokens based on trending content
"""

import os
import sys
import time
import logging
import threading
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from trendforger.scripts.tokenizer import Tokenizer
from trendforger.scripts.royalty_tracker import RoyaltyTracker
from trendforger.scripts.meme_analytics import MemeAnalytics
from config import HOST, BACKEND_PORT, INFLUENCERS

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("trendforger_service")

# Initialize FastAPI app
app = FastAPI(
    title="TrendForger API",
    description="API for monitoring influencer tweets and creator tokenization",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class TweetBase(BaseModel):
    tweet_id: str
    author: str
    content: str
    created_at: str
    
class TweetCreate(TweetBase):
    pass

class Tweet(TweetBase):
    id: int
    keywords: List[str]
    sentiment_score: float
    viral_score: float
    
    class Config:
        orm_mode = True

class TokenBase(BaseModel):
    name: str
    symbol: str
    creator: str
    
class TokenCreate(TokenBase):
    initial_supply: int
    description: str
    
class Token(TokenBase):
    id: int
    address: str
    blockchain: str
    created_at: str
    market_cap: Optional[float] = None
    
    class Config:
        orm_mode = True

class AnalysisRequest(BaseModel):
    content: str
    
class AnalysisResponse(BaseModel):
    keywords: List[str]
    sentiment_score: float
    viral_score: float
    potential_matches: List[Dict[str, Any]]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# Initialize components
manager = ConnectionManager()
tokenizer = Tokenizer()
royalty_tracker = RoyaltyTracker()
meme_analytics = MemeAnalytics()

# In-memory storage for MVP
tweets_db = []
tokens_db = []
tweet_counter = 0
token_counter = 0

# Background task for monitoring tweets
def monitor_influencer_tweets():
    """Background task to monitor tweets from influential figures"""
    global tweet_counter
    
    logger.info("Starting influencer tweet monitoring")
    
    try:
        while True:
            logger.debug("Checking for new influencer tweets")
            
            # Simulate finding new tweets (in production, would use Twitter API)
            for influencer in INFLUENCERS:
                # This is just a simulation - would be replaced with actual API calls
                if random.random() < 0.2:  # 20% chance of new tweet for demo
                    tweet_counter += 1
                    
                    # Create simulated tweet
                    tweet = {
                        "id": tweet_counter,
                        "tweet_id": f"tweet_{int(time.time())}_{random.randint(1000, 9999)}",
                        "author": influencer["twitter_handle"],
                        "content": f"This is a simulated tweet about crypto and memes #{random.choice(['doge', 'pepe', 'shiba', 'moon'])}",
                        "created_at": datetime.now().isoformat(),
                        "keywords": [],
                        "sentiment_score": 0.0,
                        "viral_score": 0.0
                    }
                    
                    # Extract keywords and analyze
                    keywords = meme_analytics.extract_keywords(tweet["content"])
                    sentiment = meme_analytics.analyze_sentiment(tweet["content"])
                    viral_score = meme_analytics.predict_virality(tweet["content"], influencer["twitter_handle"])
                    
                    tweet["keywords"] = keywords
                    tweet["sentiment_score"] = sentiment
                    tweet["viral_score"] = viral_score
                    
                    # Add to database
                    tweets_db.append(tweet)
                    
                    # Find potential coin matches
                    potential_matches = [] 
                    # This would call into contract_monitor in real impl
                    
                    # Create notification
                    notification = {
                        "type": "new_tweet",
                        "tweet": tweet,
                        "potential_matches": potential_matches
                    }
                    
                    # Send notification through WebSockets
                    asyncio.run(manager.broadcast(json.dumps(notification)))
                    
                    logger.info(f"New tweet from {influencer['twitter_handle']} detected and processed")
            
            # Sleep before next check
            time.sleep(60)  # Check every minute
            
    except Exception as e:
        logger.error(f"Error in tweet monitoring: {str(e)}")

# Start background task
import random
import asyncio
from datetime import datetime

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    # Create data directories
    Path("trendforger/data/creator_tokens.json").parent.mkdir(parents=True, exist_ok=True)
    
    # Start tweet monitoring in a background thread
    threading.Thread(target=monitor_influencer_tweets, daemon=True).start()
    logger.info("TrendForger service started")

# WebSocket endpoint for real-time notifications
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            # Process any incoming messages if needed
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# API endpoints
@app.get("/api/tweets", response_model=List[Tweet])
async def get_tweets():
    """Get all monitored tweets"""
    return tweets_db

@app.get("/api/tweets/{tweet_id}", response_model=Tweet)
async def get_tweet(tweet_id: str):
    """Get a specific tweet by ID"""
    for tweet in tweets_db:
        if tweet["tweet_id"] == tweet_id:
            return tweet
    raise HTTPException(status_code=404, detail="Tweet not found")

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_content(analysis_request: AnalysisRequest):
    """Analyze content for keywords, sentiment, and virality"""
    content = analysis_request.content
    
    # Extract keywords
    keywords = meme_analytics.extract_keywords(content)
    
    # Analyze sentiment
    sentiment_score = meme_analytics.analyze_sentiment(content)
    
    # Predict virality
    viral_score = meme_analytics.predict_virality(content)
    
    # Find potential matches (would use contract_monitor in real impl)
    potential_matches = []
    
    return {
        "keywords": keywords,
        "sentiment_score": sentiment_score,
        "viral_score": viral_score,
        "potential_matches": potential_matches
    }

@app.post("/api/tokens", response_model=Token)
async def create_token(token_create: TokenCreate, background_tasks: BackgroundTasks):
    """Create a new token"""
    global token_counter
    token_counter += 1
    
    # Create token data
    token = {
        "id": token_counter,
        "name": token_create.name,
        "symbol": token_create.symbol,
        "creator": token_create.creator,
        "address": f"0x{token_counter:x}{'0' * 38}",  # Mock address
        "blockchain": "ethereum",
        "created_at": datetime.now().isoformat(),
        "market_cap": None
    }
    
    # In a real implementation, this would call tokenizer to deploy the contract
    # background_tasks.add_task(tokenizer.deploy_token, token)
    
    # Add to database
    tokens_db.append(token)
    
    # Save to JSON for persistence
    try:
        token_path = Path("trendforger/data/creator_tokens.json")
        if token_path.exists():
            with open(token_path, 'r') as f:
                existing_tokens = json.load(f)
        else:
            existing_tokens = {"tokens": []}
        
        existing_tokens["tokens"].append(token)
        
        with open(token_path, 'w') as f:
            json.dump(existing_tokens, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving token data: {str(e)}")
    
    return token

@app.get("/api/tokens", response_model=List[Token])
async def get_tokens():
    """Get all tokens"""
    return tokens_db

@app.get("/api/tokens/{token_id}", response_model=Token)
async def get_token(token_id: int):
    """Get a specific token by ID"""
    for token in tokens_db:
        if token["id"] == token_id:
            return token
    raise HTTPException(status_code=404, detail="Token not found")

@app.get("/api/influencers")
async def get_influencers():
    """Get the list of monitored influencers"""
    return INFLUENCERS

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"status": "ok", "service": "TrendForger"}


# Run the API if executed directly
if __name__ == "__main__":
    uvicorn.run("app:app", host=HOST, port=BACKEND_PORT, reload=True)
