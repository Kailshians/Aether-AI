#!/usr/bin/env python3
"""
Ballistic Service - Meme-to-coin detection service
This service orchestrates meme scanning, contract monitoring, and alert generation
"""

import os
import sys
import time
import logging
import threading
import json
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from ballistic_service.scripts.meme_scanner import MemeScanner
from ballistic_service.scripts.contract_monitor import ContractMonitor
from ballistic_service.scripts.alert_engine import AlertEngine
from ballistic_service.scripts.anti_scam import AntiScamAnalyzer
from config import ALERT_CHECK_INTERVAL, HOST, BACKEND_PORT

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ballistic_service")

class BallisticService:
    """Main orchestrator for the Ballistic meme-to-coin detection service"""
    
    def __init__(self):
        """Initialize the Ballistic service components"""
        # Ensure data directories exist
        self._ensure_directories()
        
        # Initialize components
        self.meme_scanner = MemeScanner()
        self.contract_monitor = ContractMonitor()
        self.alert_engine = AlertEngine()
        self.anti_scam = AntiScamAnalyzer()
        
        self.running = False
        self.service_thread = None
        
        logger.info("Ballistic Service initialized")
    
    def _ensure_directories(self):
        """Ensure required data directories exist"""
        Path("ballistic_service/data/alerts/triggered").mkdir(parents=True, exist_ok=True)
        Path("ballistic_service/data/alerts/pending").mkdir(parents=True, exist_ok=True)
    
    def start(self):
        """Start the Ballistic service"""
        if self.running:
            logger.warning("Service is already running")
            return
        
        self.running = True
        self.service_thread = threading.Thread(target=self._service_loop)
        self.service_thread.daemon = True
        self.service_thread.start()
        
        logger.info("Ballistic Service started")
    
    def stop(self):
        """Stop the Ballistic service"""
        if not self.running:
            logger.warning("Service is not running")
            return
        
        self.running = False
        if self.service_thread:
            self.service_thread.join(timeout=5.0)
        
        logger.info("Ballistic Service stopped")
    
    def _service_loop(self):
        """Main service loop for meme-to-coin detection"""
        while self.running:
            try:
                # 1. Scan for trending memes
                memes = self.meme_scanner.scan_trending_memes()
                logger.debug(f"Found {len(memes)} trending memes")
                
                # 2. Extract keywords from memes
                for meme in memes:
                    keywords = self.meme_scanner.extract_keywords(meme)
                    logger.debug(f"Extracted keywords: {keywords}")
                    
                    # 3. Monitor contracts for matches
                    matches = self.contract_monitor.find_matches(keywords)
                    if matches:
                        logger.info(f"Found {len(matches)} potential meme coin matches")
                        
                        # 4. Generate alerts for matches
                        for match in matches:
                            # Perform safety analysis
                            safety_score = self.anti_scam.analyze(match['contract_address'])
                            match['safety_score'] = safety_score
                            
                            # Create alert
                            self.alert_engine.create_alert(
                                meme_data=meme,
                                coin_data=match,
                                keywords=keywords
                            )
                
                # Sleep for the configured interval
                time.sleep(ALERT_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in service loop: {str(e)}")
                time.sleep(10)  # Sleep before retrying
    
    def analyze_meme_coin(self, coin_address, blockchain="ethereum"):
        """Analyze a specific meme coin for safety"""
        return self.anti_scam.analyze(coin_address, blockchain)
    
    def get_active_alerts(self):
        """Get currently active alerts"""
        return self.alert_engine.get_active_alerts()


# Run the service if executed directly
if __name__ == "__main__":
    service = BallisticService()
    service.start()
    
    try:
        # Simple REST API for interacting with the service
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        
        @app.route('/api/alerts', methods=['GET'])
        def get_alerts():
            alerts = service.get_active_alerts()
            return jsonify({'alerts': alerts})
        
        @app.route('/api/analyze/<blockchain>/<address>', methods=['GET'])
        def analyze_coin(blockchain, address):
            result = service.analyze_meme_coin(address, blockchain)
            return jsonify(result)
        
        app.run(host=HOST, port=BACKEND_PORT, debug=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down Ballistic Service")
        service.stop()
