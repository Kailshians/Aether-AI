#!/usr/bin/env python3
"""
Alert Engine - Generates and manages alerts for potential meme coins
"""

import os
import sys
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from config import ALERT_THRESHOLD_SCORE

# Configure logging
logger = logging.getLogger("alert_engine")

class AlertEngine:
    """Engine for generating and managing meme coin alerts"""
    
    def __init__(self):
        """Initialize the AlertEngine"""
        # Ensure alerts directories exist
        self.alerts_dir = Path("ballistic_service/data/alerts")
        self.triggered_dir = self.alerts_dir / "triggered"
        self.pending_dir = self.alerts_dir / "pending"
        
        self.triggered_dir.mkdir(parents=True, exist_ok=True)
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for active alerts
        self.active_alerts = self._load_active_alerts()
        
        logger.info("AlertEngine initialized")
    
    def _load_active_alerts(self):
        """Load all active alerts from the triggered directory"""
        active_alerts = []
        
        for alert_file in self.triggered_dir.glob("*.json"):
            try:
                with open(alert_file, 'r') as f:
                    alert_data = json.load(f)
                    active_alerts.append(alert_data)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Error loading alert {alert_file}: {str(e)}")
        
        logger.info(f"Loaded {len(active_alerts)} active alerts")
        return active_alerts
    
    def create_alert(self, meme_data, coin_data, keywords):
        """Create a new alert for a potential meme coin match"""
        # Skip if match score is below threshold
        if coin_data.get('match_score', 0) < ALERT_THRESHOLD_SCORE:
            logger.debug(f"Match score {coin_data.get('match_score', 0)} below threshold, skipping alert")
            return None
        
        # Generate alert ID
        alert_id = str(uuid.uuid4())
        
        # Create alert data
        alert_data = {
            "id": alert_id,
            "created_at": datetime.now().isoformat(),
            "status": "triggered",
            "meme": {
                "id": meme_data.get("id", ""),
                "platform": meme_data.get("platform", ""),
                "title": meme_data.get("title", ""),
                "text": meme_data.get("text", ""),
                "url": meme_data.get("url", ""),
                "created_at": meme_data.get("created_utc", "")
            },
            "coin": {
                "name": coin_data.get("name", ""),
                "symbol": coin_data.get("symbol", ""),
                "address": coin_data.get("address", ""),
                "blockchain": coin_data.get("blockchain", ""),
                "created_at": coin_data.get("created_at", "")
            },
            "match": {
                "keyword": coin_data.get("match_keyword", ""),
                "score": coin_data.get("match_score", 0),
                "type": coin_data.get("match_type", "")
            },
            "keywords": keywords,
            "safety": {
                "score": coin_data.get("safety_score", {}).get("overall_score", 0),
                "risk_factors": coin_data.get("safety_score", {}).get("risk_factors", [])
            }
        }
        
        # Save the alert to triggered directory
        alert_path = self.triggered_dir / f"{alert_id}.json"
        try:
            with open(alert_path, 'w') as f:
                json.dump(alert_data, f, indent=2)
            
            # Add to active alerts cache
            self.active_alerts.append(alert_data)
            
            logger.info(f"Created new alert {alert_id} for {coin_data['name']}")
            return alert_data
            
        except OSError as e:
            logger.error(f"Error saving alert {alert_id}: {str(e)}")
            return None
    
    def get_active_alerts(self):
        """Get all currently active alerts"""
        # Refresh the cache first
        self.active_alerts = self._load_active_alerts()
        return self.active_alerts
    
    def update_alert_status(self, alert_id, new_status):
        """Update the status of an alert"""
        # Valid statuses: "triggered", "pending", "dismissed", "resolved"
        valid_statuses = {"triggered", "pending", "dismissed", "resolved"}
        if new_status not in valid_statuses:
            logger.error(f"Invalid alert status: {new_status}")
            return False
        
        # Look for the alert in triggered directory
        alert_path = self.triggered_dir / f"{alert_id}.json"
        if not alert_path.exists():
            # Try the pending directory
            alert_path = self.pending_dir / f"{alert_id}.json"
            if not alert_path.exists():
                logger.error(f"Alert {alert_id} not found")
                return False
        
        try:
            # Load the alert
            with open(alert_path, 'r') as f:
                alert_data = json.load(f)
            
            # Update the status
            alert_data["status"] = new_status
            alert_data["updated_at"] = datetime.now().isoformat()
            
            # Determine the new directory based on status
            if new_status == "triggered":
                new_dir = self.triggered_dir
            elif new_status == "pending":
                new_dir = self.pending_dir
            else:
                # For dismissed and resolved, we'll keep in pending
                new_dir = self.pending_dir
            
            # Save to the new location
            new_path = new_dir / f"{alert_id}.json"
            with open(new_path, 'w') as f:
                json.dump(alert_data, f, indent=2)
            
            # Remove from the old location if different
            if alert_path != new_path and alert_path.exists():
                alert_path.unlink()
            
            # Update the active alerts cache if needed
            if new_status in {"dismissed", "resolved"}:
                self.active_alerts = [a for a in self.active_alerts if a["id"] != alert_id]
            elif new_status in {"triggered", "pending"}:
                for i, alert in enumerate(self.active_alerts):
                    if alert["id"] == alert_id:
                        self.active_alerts[i] = alert_data
                        break
                else:
                    # Not found in cache, add it
                    self.active_alerts.append(alert_data)
            
            logger.info(f"Updated alert {alert_id} status to {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating alert {alert_id}: {str(e)}")
            return False


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    alert_engine = AlertEngine()
    
    # Test creating an alert
    meme_data = {
        "id": "test-meme-1",
        "platform": "reddit",
        "title": "Test Meme",
        "text": "This is a test meme about Dogecoin",
        "url": "https://reddit.com/r/memes/123",
        "created_utc": datetime.now().isoformat()
    }
    
    coin_data = {
        "name": "DogeCoin Test",
        "symbol": "DOGETEST",
        "address": "0x123456789abcdef",
        "blockchain": "ethereum",
        "created_at": datetime.now().isoformat(),
        "match_keyword": "doge",
        "match_score": 0.9,
        "match_type": "name",
        "safety_score": {
            "overall_score": 0.7,
            "risk_factors": ["New Contract", "Low Liquidity"]
        }
    }
    
    keywords = ["doge", "coin", "test"]
    
    alert = alert_engine.create_alert(meme_data, coin_data, keywords)
    if alert:
        print(f"Created alert: {alert['id']}")
        
        # Test updating the status
        alert_engine.update_alert_status(alert['id'], "pending")
        alert_engine.update_alert_status(alert['id'], "triggered")  # Back to triggered
