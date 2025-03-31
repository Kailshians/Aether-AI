import os

# API keys
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "MemeTokenPredictor/1.0")

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
PUMPFUN_API_KEY = os.getenv("PUMPFUN_API_KEY", "")

RUGPULL_API_KEY = os.getenv("RUGPULL_API_KEY", "")
TOKEN_SNIFFER_API_KEY = os.getenv("TOKEN_SNIFFER_API_KEY", "")

# Service configuration
WEB_PORT = 5000
BACKEND_PORT = 8000
HOST = "0.0.0.0"

# Database paths
KEYWORD_DB_PATH = "ballistic_service/models/keyword_db.sqlite"

# Endpoints
ETHERSCAN_API_ENDPOINT = "https://api.etherscan.io/api"
PUMPFUN_API_ENDPOINT = "https://api.pumpfun.com/v1"  # Placeholder
RUGPULL_API_ENDPOINT = "https://api.rugpull.com/v1"  # Placeholder
TOKEN_SNIFFER_API_ENDPOINT = "https://api.tokensniffer.com/v1"  # Placeholder

# Influencers to track
INFLUENCERS = [
    {"name": "Elon Musk", "twitter_handle": "elonmusk"},
    {"name": "Donald Trump", "twitter_handle": "realDonaldTrump"}
]

# Meme sources
MEME_SOURCES = [
    {"platform": "reddit", "subreddit": "memes"},
    {"platform": "reddit", "subreddit": "dankmemes"},
    {"platform": "reddit", "subreddit": "CryptoCurrency"},
    {"platform": "twitter", "track": ["meme", "crypto", "memecoin"]}
]

# Alert settings
ALERT_CHECK_INTERVAL = 60  # seconds
ALERT_THRESHOLD_SCORE = 0.7  # minimum confidence score for alerts
