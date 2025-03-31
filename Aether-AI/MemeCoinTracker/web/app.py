#!/usr/bin/env python3
"""
Aether AI Web Application - Main web server for the meme coin prediction platform
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import threading
import time

from flask import Flask, render_template, jsonify, request, abort, session, redirect, url_for

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import (
    WEB_PORT, HOST, BACKEND_PORT, ALERT_CHECK_INTERVAL,
    ETHERSCAN_API_KEY, PUMPFUN_API_KEY
)

# Import service components for direct integration
from ballistic_service.scripts.meme_scanner import MemeScanner
from ballistic_service.scripts.contract_monitor import ContractMonitor
from ballistic_service.scripts.alert_engine import AlertEngine
from ballistic_service.scripts.anti_scam import AntiScamAnalyzer
from trendforger.scripts.meme_analytics import MemeAnalytics
from analysis.cross_service.meme_coin_correlator import MemeCoinCorrelator
from analysis.cross_service.alert_optimizer import AlertOptimizer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("web_app")

# Initialize Flask app
template_dir = Path(__file__).resolve().parent / 'templates'
static_dir = Path(__file__).resolve().parent / 'static'
app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))
app.secret_key = os.environ.get("SESSION_SECRET", "aether_ai_development_key")

# Initialize components
meme_scanner = MemeScanner()
contract_monitor = ContractMonitor()
alert_engine = AlertEngine()
anti_scam = AntiScamAnalyzer()
meme_analytics = MemeAnalytics()
correlator = MemeCoinCorrelator()
optimizer = AlertOptimizer()

# In-memory storage for active alert cache
active_alerts_cache = []
last_alert_update = datetime.now()

# Background task to update alerts periodically
def update_alerts_background():
    """Background task to update alerts periodically"""
    global active_alerts_cache, last_alert_update
    
    logger.info("Starting background alert updater")
    
    while True:
        try:
            # Get latest alerts
            try:
                alerts = alert_engine.get_active_alerts()
                active_alerts_cache = alerts
                last_alert_update = datetime.now()
                logger.debug(f"Updated alerts: {len(alerts)} active alerts")
            except Exception as e:
                logger.error(f"Error updating alerts: {str(e)}")
            
            # Sleep for the interval
            time.sleep(ALERT_CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error in alert update loop: {str(e)}")
            time.sleep(10)  # Sleep before retrying

# Start background task
alert_updater = threading.Thread(target=update_alerts_background)
alert_updater.daemon = True
alert_updater.start()

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/ballistic')
def ballistic():
    """Ballistic service dashboard (meme-to-coin detection)"""
    return render_template('ballistic.html')

@app.route('/trendforger')
def trendforger():
    """TrendForger service dashboard (influencer tweet tracking)"""
    return render_template('trendforger.html')

# API Routes
@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ballistic": True,
            "trendforger": True,
            "web": True
        },
        "api_keys": {
            "etherscan": bool(ETHERSCAN_API_KEY),
            "pumpfun": bool(PUMPFUN_API_KEY)
        }
    })

@app.route('/api/alerts')
def api_alerts():
    """Get current active alerts"""
    global active_alerts_cache
    
    limit = request.args.get('limit', default=10, type=int)
    
    # Ensure limit is reasonable
    if limit < 1:
        limit = 1
    elif limit > 100:
        limit = 100
    
    # Get alerts with optimization data
    alerts = active_alerts_cache[:limit]
    
    # Add optimization data if not present
    for alert in alerts:
        if "optimization" not in alert:
            try:
                optimization = optimizer.optimize_alert(alert)
                alert["optimization"] = optimization
            except Exception as e:
                logger.error(f"Error optimizing alert: {str(e)}")
                alert["optimization"] = {"error": str(e)}
    
    return jsonify({
        "alerts": alerts,
        "count": len(alerts),
        "total": len(active_alerts_cache),
        "updated_at": last_alert_update.isoformat()
    })

@app.route('/api/alerts/<alert_id>')
def api_alert_detail(alert_id):
    """Get details for a specific alert"""
    global active_alerts_cache
    
    # Search for the alert in the cache
    for alert in active_alerts_cache:
        if alert.get("id") == alert_id:
            return jsonify(alert)
    
    # If not found in cache, try to load from file
    alert_path = Path(f"ballistic_service/data/alerts/triggered/{alert_id}.json")
    if alert_path.exists():
        try:
            with open(alert_path, 'r') as f:
                alert_data = json.load(f)
                return jsonify(alert_data)
        except Exception as e:
            logger.error(f"Error loading alert {alert_id}: {str(e)}")
    
    # Try pending directory if not in triggered
    alert_path = Path(f"ballistic_service/data/alerts/pending/{alert_id}.json")
    if alert_path.exists():
        try:
            with open(alert_path, 'r') as f:
                alert_data = json.load(f)
                return jsonify(alert_data)
        except Exception as e:
            logger.error(f"Error loading alert {alert_id}: {str(e)}")
    
    # Alert not found
    return jsonify({"error": "Alert not found"}), 404

@app.route('/api/alerts/<alert_id>/status', methods=['POST'])
def api_update_alert_status(alert_id):
    """Update the status of an alert"""
    if not request.json or 'status' not in request.json:
        return jsonify({"error": "Missing status field"}), 400
    
    new_status = request.json['status']
    
    # Check if status is valid
    valid_statuses = ["triggered", "pending", "dismissed", "resolved"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
    
    # Update the alert status
    result = alert_engine.update_alert_status(alert_id, new_status)
    
    if result:
        # Update the cache
        global active_alerts_cache
        for i, alert in enumerate(active_alerts_cache):
            if alert.get("id") == alert_id:
                active_alerts_cache[i]["status"] = new_status
                active_alerts_cache[i]["updated_at"] = datetime.now().isoformat()
                break
        
        return jsonify({"success": True, "status": new_status})
    else:
        return jsonify({"error": "Failed to update alert status"}), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze_content():
    """Analyze content for meme coin potential"""
    if not request.json or 'content' not in request.json:
        return jsonify({"error": "Missing content field"}), 400
    
    content = request.json['content']
    
    try:
        # Extract keywords
        keywords = meme_analytics.extract_keywords(content)
        
        # Analyze sentiment
        sentiment_score = meme_analytics.analyze_sentiment(content)
        
        # Predict virality
        viral_score = meme_analytics.predict_virality(content)
        
        # Find potential coin matches
        matches = []
        if keywords:
            matches = contract_monitor.find_matches(keywords)
            
            # Add safety analysis to matches
            for match in matches:
                safety = anti_scam.analyze(match.get("address", ""), match.get("blockchain", "ethereum"))
                match["safety"] = safety
        
        return jsonify({
            "content": content,
            "keywords": keywords,
            "sentiment_score": sentiment_score,
            "viral_score": viral_score,
            "potential_matches": matches,
            "analyzed_at": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error analyzing content: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route('/api/analyze/coin', methods=['POST'])
def api_analyze_coin():
    """Analyze a specific coin for safety"""
    if not request.json or 'address' not in request.json:
        return jsonify({"error": "Missing address field"}), 400
    
    address = request.json['address']
    blockchain = request.json.get('blockchain', 'ethereum')
    
    try:
        # Analyze coin safety
        safety = anti_scam.analyze(address, blockchain)
        
        return jsonify({
            "address": address,
            "blockchain": blockchain,
            "safety": safety,
            "analyzed_at": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error analyzing coin {address}: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route('/api/correlations')
def api_correlations():
    """Get meme-coin correlations"""
    limit = request.args.get('limit', default=10, type=int)
    source = request.args.get('source', default=None)
    status = request.args.get('status', default=None)
    
    # Get correlations
    correlations = correlator.get_correlations(source, status, limit)
    
    return jsonify({
        "correlations": correlations,
        "count": len(correlations),
        "filters": {
            "source": source,
            "status": status,
            "limit": limit
        }
    })

@app.route('/api/scan/trending')
def api_scan_trending():
    """Trigger a scan for trending memes"""
    try:
        # Scan for trending memes
        memes = meme_scanner.scan_trending_memes()
        
        # Process each meme for keywords
        processed_memes = []
        for meme in memes:
            keywords = meme_scanner.extract_keywords(meme)
            meme["keywords"] = keywords
            processed_memes.append(meme)
        
        return jsonify({
            "success": True,
            "memes": processed_memes,
            "count": len(processed_memes),
            "scanned_at": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error scanning trending memes: {str(e)}")
        return jsonify({"error": f"Scan failed: {str(e)}"}), 500

@app.route('/api/scan/contracts')
def api_scan_contracts():
    """Trigger a scan for new contracts"""
    try:
        # Update blockchain contracts
        ethereum_updated = contract_monitor.update_ethereum_contracts()
        solana_updated = contract_monitor.update_solana_contracts()
        
        return jsonify({
            "success": True,
            "ethereum_updated": ethereum_updated,
            "solana_updated": solana_updated,
            "scanned_at": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error scanning contracts: {str(e)}")
        return jsonify({"error": f"Scan failed: {str(e)}"}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('error.html', error="Page Not Found", message="The requested page does not exist."), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('error.html', error="Server Error", message="An unexpected error occurred."), 500

# Run the app
if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    Path("web/templates").mkdir(parents=True, exist_ok=True)
    
    # Create static directory if it doesn't exist
    Path("web/static/js").mkdir(parents=True, exist_ok=True)
    Path("web/static/css").mkdir(parents=True, exist_ok=True)
    
    # Run the Flask app
    app.run(host=HOST, port=WEB_PORT, debug=True)
