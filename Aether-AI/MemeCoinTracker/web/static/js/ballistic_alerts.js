/**
 * Ballistic Alerts - Real-time notification handler
 * Manages the display and interaction with meme-to-coin alerts
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const alertRefreshInterval = 30000; // 30 seconds
    const maxAlerts = 20;
    let alertData = [];
    let activeFilter = 'all';
    let websocketConnected = false;
    
    // Elements
    const alertContainer = document.getElementById('alert-container');
    const alertCounter = document.getElementById('alert-counter');
    const alertFilters = document.querySelectorAll('.alert-filter');
    const alertRefreshBtn = document.getElementById('refresh-alerts');
    const alertStatusIndicator = document.getElementById('alert-status');
    const analysisForm = document.getElementById('analysis-form');
    const analysisInput = document.getElementById('analysis-input');
    const analysisResults = document.getElementById('analysis-results');
    const scanTrendingBtn = document.getElementById('scan-trending');
    
    // Set up WebSocket connection
    function setupWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        const socket = new WebSocket(wsUrl);
        
        socket.onopen = function(e) {
            console.log("WebSocket connection established");
            websocketConnected = true;
            updateStatusIndicator();
        };
        
        socket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'new_alert') {
                    // Add new alert and refresh display
                    alertData.unshift(data.alert);
                    if (alertData.length > maxAlerts) {
                        alertData.pop();
                    }
                    renderAlerts();
                    showNotification('New Meme Coin Alert', `${data.alert.coin.name} (${data.alert.coin.symbol}) matched with ${data.alert.meme.platform} content`);
                }
            } catch (e) {
                console.error("Error processing WebSocket message:", e);
            }
        };
        
        socket.onclose = function(event) {
            console.log("WebSocket connection closed");
            websocketConnected = false;
            updateStatusIndicator();
            
            // Try to reconnect after a delay
            setTimeout(setupWebSocket, 5000);
        };
        
        socket.onerror = function(error) {
            console.error("WebSocket error:", error);
            websocketConnected = false;
            updateStatusIndicator();
        };
    }
    
    // Try to establish WebSocket connection
    setupWebSocket();
    
    // Update status indicator
    function updateStatusIndicator() {
        if (websocketConnected) {
            alertStatusIndicator.textContent = 'Connected';
            alertStatusIndicator.className = 'status-indicator connected';
        } else {
            alertStatusIndicator.textContent = 'Disconnected';
            alertStatusIndicator.className = 'status-indicator disconnected';
        }
    }
    
    // Fetch alerts from API
    function fetchAlerts() {
        fetch('/api/alerts')
            .then(response => response.json())
            .then(data => {
                alertData = data.alerts;
                renderAlerts();
                updateAlertCounter(data.total);
            })
            .catch(error => {
                console.error('Error fetching alerts:', error);
                alertContainer.innerHTML = `
                    <div class="alert-error">
                        <h3>Error Loading Alerts</h3>
                        <p>${error.message || 'Failed to load alerts. Please try again.'}</p>
                    </div>
                `;
            });
    }
    
    // Update alert counter
    function updateAlertCounter(count) {
        if (alertCounter) {
            alertCounter.textContent = count || 0;
        }
    }
    
    // Render alerts
    function renderAlerts() {
        if (!alertContainer) return;
        
        if (alertData.length === 0) {
            alertContainer.innerHTML = `
                <div class="alert-empty">
                    <h3>No Alerts Found</h3>
                    <p>No meme-to-coin alerts have been detected yet.</p>
                    <button id="scan-now-empty" class="btn primary">Scan Now</button>
                </div>
            `;
            
            // Attach event listener to the scan now button
            const scanNowBtn = document.getElementById('scan-now-empty');
            if (scanNowBtn) {
                scanNowBtn.addEventListener('click', scanTrending);
            }
            return;
        }
        
        let filteredAlerts = alertData;
        
        // Apply filter
        if (activeFilter !== 'all') {
            filteredAlerts = alertData.filter(alert => {
                if (activeFilter === 'high') {
                    return (alert.optimization?.optimized_score || 0) >= 0.7;
                } else if (activeFilter === 'medium') {
                    const score = alert.optimization?.optimized_score || 0;
                    return score >= 0.4 && score < 0.7;
                } else if (activeFilter === 'low') {
                    return (alert.optimization?.optimized_score || 0) < 0.4;
                }
                return true;
            });
        }
        
        if (filteredAlerts.length === 0) {
            alertContainer.innerHTML = `
                <div class="alert-empty">
                    <h3>No Matching Alerts</h3>
                    <p>No alerts match the current filter criteria.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        filteredAlerts.forEach(alert => {
            const optimizedScore = alert.optimization?.optimized_score || alert.match.score;
            const scoreClass = getScoreClass(optimizedScore);
            
            const memeTitle = alert.meme.title || alert.meme.text || 'Untitled Meme';
            const memeSource = alert.meme.platform ? `on ${alert.meme.platform}` : '';
            const coinSymbol = alert.coin.symbol ? `(${alert.coin.symbol})` : '';
            const matchKeyword = alert.match.keyword || '';
            const safetyScore = alert.safety.score || 0;
            const safetyClass = getScoreClass(safetyScore);
            
            html += `
                <div class="alert-card ${scoreClass}" data-id="${alert.id}">
                    <div class="alert-header">
                        <span class="alert-score ${scoreClass}">${(optimizedScore * 100).toFixed(0)}%</span>
                        <h3 class="alert-title">${alert.coin.name} ${coinSymbol}</h3>
                        <div class="alert-actions">
                            <button class="btn-icon view-alert" data-id="${alert.id}" title="View Details">
                                <i class="feather icon-eye"></i>
                            </button>
                            <button class="btn-icon dismiss-alert" data-id="${alert.id}" title="Dismiss Alert">
                                <i class="feather icon-x"></i>
                            </button>
                        </div>
                    </div>
                    <div class="alert-body">
                        <p class="alert-meme">
                            <strong>Meme:</strong> "${truncateText(memeTitle, 60)}" ${memeSource}
                        </p>
                        <p class="alert-match">
                            <strong>Match:</strong> "${matchKeyword}" with ${(alert.match.score * 100).toFixed(0)}% confidence
                        </p>
                        <div class="alert-metrics">
                            <div class="metric">
                                <span class="metric-label">Safety</span>
                                <div class="progress-bar">
                                    <div class="progress ${safetyClass}" style="width: ${safetyScore * 100}%"></div>
                                </div>
                            </div>
                            
                            <div class="metric">
                                <span class="metric-label">Sentiment</span>
                                <div class="progress-bar">
                                    <div class="progress ${getScoreClass((alert.optimization?.sentiment_score + 1) / 2 || 0.5)}" 
                                         style="width: ${((alert.optimization?.sentiment_score + 1) / 2 * 100) || 50}%"></div>
                                </div>
                            </div>
                            
                            <div class="metric">
                                <span class="metric-label">Virality</span>
                                <div class="progress-bar">
                                    <div class="progress ${getScoreClass(alert.optimization?.meme_virality || 0.5)}" 
                                         style="width: ${(alert.optimization?.meme_virality * 100) || 50}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="alert-footer">
                        <span class="alert-timestamp">${formatDate(alert.created_at)}</span>
                        <button class="btn analyze-coin" data-address="${alert.coin.address}" data-blockchain="${alert.coin.blockchain}">
                            Analyze Coin
                        </button>
                    </div>
                </div>
            `;
        });
        
        alertContainer.innerHTML = html;
        
        // Attach event listeners
        document.querySelectorAll('.view-alert').forEach(button => {
            button.addEventListener('click', () => viewAlertDetails(button.dataset.id));
        });
        
        document.querySelectorAll('.dismiss-alert').forEach(button => {
            button.addEventListener('click', () => dismissAlert(button.dataset.id));
        });
        
        document.querySelectorAll('.analyze-coin').forEach(button => {
            button.addEventListener('click', () => analyzeCoin(button.dataset.address, button.dataset.blockchain));
        });
    }
    
    // Helper function to get CSS class based on score
    function getScoreClass(score) {
        if (score >= 0.7) return 'high';
        if (score >= 0.4) return 'medium';
        return 'low';
    }
    
    // Helper function to truncate text
    function truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }
    
    // Helper function to format date
    function formatDate(dateString) {
        if (!dateString) return 'Unknown';
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return 'Invalid date';
        
        const now = new Date();
        const diffMinutes = Math.floor((now - date) / (1000 * 60));
        
        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        
        const diffHours = Math.floor(diffMinutes / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }
    
    // View alert details
    function viewAlertDetails(alertId) {
        fetch(`/api/alerts/${alertId}`)
            .then(response => response.json())
            .then(alert => {
                const modal = document.getElementById('alert-modal') || createAlertModal();
                
                const optimizedScore = alert.optimization?.optimized_score || alert.match.score;
                const scoreClass = getScoreClass(optimizedScore);
                
                // Format rejection reasons if available
                let rejectionReasons = '';
                if (alert.optimization?.rejection_reasons && alert.optimization.rejection_reasons.length > 0) {
                    rejectionReasons = `
                        <div class="alert-rejections">
                            <h4>Potential Issues</h4>
                            <ul>
                                ${alert.optimization.rejection_reasons.map(reason => `<li>${reason}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                // Format risk factors if available
                let riskFactors = '';
                if (alert.safety?.risk_factors && alert.safety.risk_factors.length > 0) {
                    riskFactors = `
                        <div class="alert-risks">
                            <h4>Risk Factors</h4>
                            <ul>
                                ${alert.safety.risk_factors.map(factor => `<li>${factor}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                // Prepare blockchain explorer link
                let explorerUrl = '#';
                if (alert.coin.blockchain === 'ethereum') {
                    explorerUrl = `https://etherscan.io/token/${alert.coin.address}`;
                } else if (alert.coin.blockchain === 'solana') {
                    explorerUrl = `https://explorer.solana.com/address/${alert.coin.address}`;
                }
                
                modal.querySelector('.modal-content').innerHTML = `
                    <div class="alert-detail">
                        <div class="alert-detail-header ${scoreClass}">
                            <h2>${alert.coin.name} (${alert.coin.symbol})</h2>
                            <span class="alert-score ${scoreClass}">${(optimizedScore * 100).toFixed(0)}%</span>
                        </div>
                        
                        <div class="alert-detail-body">
                            <div class="alert-section">
                                <h3>Meme Source</h3>
                                <p><strong>Platform:</strong> ${alert.meme.platform}</p>
                                <p><strong>Title:</strong> ${alert.meme.title || 'N/A'}</p>
                                <p><strong>Text:</strong> ${alert.meme.text || 'N/A'}</p>
                                ${alert.meme.url ? `<p><a href="${alert.meme.url}" target="_blank" rel="noopener">View Original Meme</a></p>` : ''}
                            </div>
                            
                            <div class="alert-section">
                                <h3>Coin Information</h3>
                                <p><strong>Name:</strong> ${alert.coin.name}</p>
                                <p><strong>Symbol:</strong> ${alert.coin.symbol}</p>
                                <p><strong>Blockchain:</strong> ${alert.coin.blockchain}</p>
                                <p><strong>Address:</strong> <a href="${explorerUrl}" target="_blank" rel="noopener">${truncateText(alert.coin.address, 20)}</a></p>
                                <p><strong>Created:</strong> ${formatDate(alert.coin.created_at)}</p>
                            </div>
                            
                            <div class="alert-section">
                                <h3>Match Details</h3>
                                <p><strong>Keyword:</strong> "${alert.match.keyword}"</p>
                                <p><strong>Match Type:</strong> ${alert.match.type}</p>
                                <p><strong>Raw Match Score:</strong> ${(alert.match.score * 100).toFixed(0)}%</p>
                                <p><strong>Optimized Score:</strong> ${(optimizedScore * 100).toFixed(0)}%</p>
                            </div>
                            
                            <div class="alert-section">
                                <h3>Safety Analysis</h3>
                                <p><strong>Safety Score:</strong> ${(alert.safety.score * 100).toFixed(0)}%</p>
                                ${riskFactors}
                            </div>
                            
                            ${rejectionReasons}
                        </div>
                        
                        <div class="alert-detail-footer">
                            <button class="btn secondary close-modal">Close</button>
                            <button class="btn primary analyze-detail-coin" data-address="${alert.coin.address}" data-blockchain="${alert.coin.blockchain}">
                                Advanced Analysis
                            </button>
                        </div>
                    </div>
                `;
                
                openModal(modal);
                
                // Attach event listeners
                modal.querySelector('.close-modal').addEventListener('click', () => closeModal(modal));
                modal.querySelector('.analyze-detail-coin').addEventListener('click', () => {
                    closeModal(modal);
                    analyzeCoin(alert.coin.address, alert.coin.blockchain);
                });
            })
            .catch(error => {
                console.error('Error fetching alert details:', error);
                showNotification('Error', 'Failed to load alert details', 'error');
            });
    }
    
    // Dismiss alert
    function dismissAlert(alertId) {
        if (!confirm('Are you sure you want to dismiss this alert?')) {
            return;
        }
        
        fetch(`/api/alerts/${alertId}/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'dismissed' })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove alert from data and re-render
                alertData = alertData.filter(alert => alert.id !== alertId);
                renderAlerts();
                updateAlertCounter(alertData.length);
                showNotification('Success', 'Alert dismissed successfully');
            } else {
                throw new Error(data.error || 'Failed to dismiss alert');
            }
        })
        .catch(error => {
            console.error('Error dismissing alert:', error);
            showNotification('Error', 'Failed to dismiss alert', 'error');
        });
    }
    
    // Analyze coin
    function analyzeCoin(address, blockchain) {
        if (!address) {
            showNotification('Error', 'No coin address provided', 'error');
            return;
        }
        
        // Show loading state
        const modal = document.getElementById('analysis-modal') || createAnalysisModal();
        modal.querySelector('.modal-content').innerHTML = `
            <div class="analysis-loading">
                <div class="spinner"></div>
                <h3>Analyzing Coin...</h3>
                <p>Performing comprehensive analysis of ${truncateText(address, 20)} on ${blockchain}</p>
            </div>
        `;
        
        openModal(modal);
        
        // Fetch analysis data
        fetch('/api/analyze/coin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ address, blockchain })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            const safety = data.safety;
            const safetyScore = safety.overall_score || 0;
            const safetyClass = getScoreClass(safetyScore);
            
            // Prepare blockchain explorer link
            let explorerUrl = '#';
            if (blockchain === 'ethereum') {
                explorerUrl = `https://etherscan.io/token/${address}`;
            } else if (blockchain === 'solana') {
                explorerUrl = `https://explorer.solana.com/address/${address}`;
            }
            
            // Format risk factors
            let riskFactorsList = '<p>No risk factors detected.</p>';
            if (safety.risk_factors && safety.risk_factors.length > 0) {
                riskFactorsList = `
                    <ul class="risk-factors-list">
                        ${safety.risk_factors.map(factor => `<li>${factor}</li>`).join('')}
                    </ul>
                `;
            }
            
            // Format detailed checks if available
            let detailedChecks = '';
            if (safety.detailed_checks) {
                detailedChecks = `
                    <div class="detailed-checks">
                        <h4>Detailed Security Checks</h4>
                        <ul>
                            ${Object.entries(safety.detailed_checks).map(([key, value]) => {
                                const isPass = typeof value === 'boolean' ? value : value > 0.5;
                                const statusClass = isPass ? 'check-pass' : 'check-fail';
                                const statusIcon = isPass ? 'check' : 'x';
                                const valueDisplay = typeof value === 'boolean' ? (value ? 'Pass' : 'Fail') : `${(value * 100).toFixed(0)}%`;
                                
                                return `
                                    <li class="check-item ${statusClass}">
                                        <i class="feather icon-${statusIcon}"></i>
                                        <span class="check-name">${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                        <span class="check-value">${valueDisplay}</span>
                                    </li>
                                `;
                            }).join('')}
                        </ul>
                    </div>
                `;
            }
            
            modal.querySelector('.modal-content').innerHTML = `
                <div class="coin-analysis">
                    <div class="analysis-header ${safetyClass}">
                        <h2>Coin Safety Analysis</h2>
                        <div class="safety-score ${safetyClass}">
                            <span class="score-value">${(safetyScore * 100).toFixed(0)}%</span>
                            <span class="score-label">Safety</span>
                        </div>
                    </div>
                    
                    <div class="analysis-body">
                        <div class="analysis-section">
                            <h3>Contract Information</h3>
                            <p><strong>Address:</strong> <a href="${explorerUrl}" target="_blank" rel="noopener">${address}</a></p>
                            <p><strong>Blockchain:</strong> ${blockchain}</p>
                            <p><strong>Analysis Time:</strong> ${formatDate(data.safety.timestamp)}</p>
                        </div>
                        
                        <div class="analysis-section">
                            <h3>Risk Assessment</h3>
                            <div class="risk-meter ${safetyClass}">
                                <div class="risk-label">Risk Level:</div>
                                <div class="risk-value">
                                    ${
                                        safetyScore > 0.7 ? 'Low Risk' :
                                        safetyScore > 0.4 ? 'Medium Risk' : 'High Risk'
                                    }
                                </div>
                            </div>
                            
                            <h4>Identified Risk Factors</h4>
                            ${riskFactorsList}
                        </div>
                        
                        ${detailedChecks}
                    </div>
                    
                    <div class="analysis-footer">
                        <p class="disclaimer">This analysis is provided for informational purposes only and should not be considered financial advice. Always do your own research before investing.</p>
                        <button class="btn secondary close-modal">Close</button>
                    </div>
                </div>
            `;
            
            // Attach event listeners
            modal.querySelector('.close-modal').addEventListener('click', () => closeModal(modal));
        })
        .catch(error => {
            console.error('Error analyzing coin:', error);
            
            modal.querySelector('.modal-content').innerHTML = `
                <div class="analysis-error">
                    <i class="feather icon-alert-triangle"></i>
                    <h3>Analysis Failed</h3>
                    <p>${error.message || 'Failed to analyze coin. Please try again.'}</p>
                    <button class="btn secondary close-modal">Close</button>
                </div>
            `;
            
            // Attach event listener
            modal.querySelector('.close-modal').addEventListener('click', () => closeModal(modal));
        });
    }
    
    // Scan for trending memes
    function scanTrending() {
        // Show loading state
        const scanBtn = document.getElementById('scan-trending');
        if (scanBtn) {
            scanBtn.disabled = true;
            scanBtn.innerHTML = '<span class="spinner-small"></span> Scanning...';
        }
        
        fetch('/api/scan/trending')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                showNotification('Scan Complete', `Found ${data.count} trending memes`);
                
                // Refresh alerts after scan
                fetchAlerts();
            })
            .catch(error => {
                console.error('Error scanning trending memes:', error);
                showNotification('Scan Failed', error.message || 'Failed to scan trending memes', 'error');
            })
            .finally(() => {
                // Reset button state
                if (scanBtn) {
                    scanBtn.disabled = false;
                    scanBtn.innerHTML = 'Scan Trending Memes';
                }
            });
    }
    
    // Analyze content for meme coin potential
    function analyzeContent(content) {
        if (!content.trim()) {
            showNotification('Error', 'Please enter content to analyze', 'warning');
            return;
        }
        
        // Show loading state
        const results = document.getElementById('analysis-results');
        if (results) {
            results.innerHTML = `
                <div class="analysis-loading">
                    <div class="spinner"></div>
                    <p>Analyzing content...</p>
                </div>
            `;
        }
        
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            const sentimentScore = data.sentiment_score;
            const sentimentClass = sentimentScore > 0.05 ? 'positive' : sentimentScore < -0.05 ? 'negative' : 'neutral';
            const sentimentText = sentimentScore > 0.05 ? 'Positive' : sentimentScore < -0.05 ? 'Negative' : 'Neutral';
            
            // Render keywords
            let keywordsHtml = '<p>No keywords extracted.</p>';
            if (data.keywords && data.keywords.length > 0) {
                keywordsHtml = `
                    <div class="keyword-list">
                        ${data.keywords.map(keyword => `<span class="keyword-tag">${keyword}</span>`).join('')}
                    </div>
                `;
            }
            
            // Render potential matches
            let matchesHtml = '<p>No potential coin matches found.</p>';
            if (data.potential_matches && data.potential_matches.length > 0) {
                matchesHtml = `
                    <div class="matches-list">
                        ${data.potential_matches.map(match => {
                            const matchScore = match.match_score;
                            const matchClass = getScoreClass(matchScore);
                            const safetyScore = match.safety?.overall_score || 0;
                            const safetyClass = getScoreClass(safetyScore);
                            
                            return `
                                <div class="match-item ${matchClass}">
                                    <div class="match-header">
                                        <h4>${match.name} (${match.symbol})</h4>
                                        <span class="match-score ${matchClass}">${(matchScore * 100).toFixed(0)}%</span>
                                    </div>
                                    <div class="match-body">
                                        <p><strong>Match Keyword:</strong> "${match.match_keyword}"</p>
                                        <p><strong>Blockchain:</strong> ${match.blockchain}</p>
                                        <div class="match-metrics">
                                            <div class="metric">
                                                <span class="metric-label">Safety</span>
                                                <div class="progress-bar">
                                                    <div class="progress ${safetyClass}" style="width: ${safetyScore * 100}%"></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="match-footer">
                                        <button class="btn small analyze-coin" data-address="${match.address}" data-blockchain="${match.blockchain}">
                                            Analyze
                                        </button>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }
            
            // Update results
            if (results) {
                results.innerHTML = `
                    <div class="analysis-results-container">
                        <div class="analysis-section">
                            <h3>Content Analysis</h3>
                            <div class="analysis-summary">
                                <div class="analysis-metric">
                                    <span class="metric-label">Sentiment</span>
                                    <span class="metric-value ${sentimentClass}">${sentimentText} (${sentimentScore.toFixed(2)})</span>
                                </div>
                                <div class="analysis-metric">
                                    <span class="metric-label">Virality Potential</span>
                                    <span class="metric-value ${getScoreClass(data.viral_score)}">${(data.viral_score * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                            <div class="extracted-keywords">
                                <h4>Extracted Keywords</h4>
                                ${keywordsHtml}
                            </div>
                        </div>
                        
                        <div class="analysis-section">
                            <h3>Potential Coin Matches</h3>
                            ${matchesHtml}
                        </div>
                    </div>
                `;
                
                // Attach event listeners to analyze buttons
                results.querySelectorAll('.analyze-coin').forEach(button => {
                    button.addEventListener('click', () => {
                        analyzeCoin(button.dataset.address, button.dataset.blockchain);
                    });
                });
            }
        })
        .catch(error => {
            console.error('Error analyzing content:', error);
            
            if (results) {
                results.innerHTML = `
                    <div class="analysis-error">
                        <i class="feather icon-alert-triangle"></i>
                        <h3>Analysis Failed</h3>
                        <p>${error.message || 'Failed to analyze content. Please try again.'}</p>
                    </div>
                `;
            }
        });
    }
    
    // Create alert modal if it doesn't exist
    function createAlertModal() {
        const modal = document.createElement('div');
        modal.id = 'alert-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-container">
                <div class="modal-header">
                    <h2>Alert Details</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-content">
                    <!-- Content will be dynamically populated -->
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Attach event listener to close button
        modal.querySelector('.modal-close').addEventListener('click', () => closeModal(modal));
        modal.querySelector('.modal-overlay').addEventListener('click', () => closeModal(modal));
        
        return modal;
    }
    
    // Create analysis modal if it doesn't exist
    function createAnalysisModal() {
        const modal = document.createElement('div');
        modal.id = 'analysis-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-container">
                <div class="modal-header">
                    <h2>Coin Analysis</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-content">
                    <!-- Content will be dynamically populated -->
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Attach event listener to close button
        modal.querySelector('.modal-close').addEventListener('click', () => closeModal(modal));
        modal.querySelector('.modal-overlay').addEventListener('click', () => closeModal(modal));
        
        return modal;
    }
    
    // Open modal
    function openModal(modal) {
        if (!modal) return;
        modal.classList.add('open');
        document.body.classList.add('modal-open');
    }
    
    // Close modal
    function closeModal(modal) {
        if (!modal) return;
        modal.classList.remove('open');
        document.body.classList.remove('modal-open');
    }
    
    // Show notification
    function showNotification(title, message, type = 'success') {
        // Create notification container if it doesn't exist
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            document.body.appendChild(container);
        }
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="feather icon-${type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'alert-triangle'}"></i>
            </div>
            <div class="notification-content">
                <h4>${title}</h4>
                <p>${message}</p>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        // Add to container
        container.appendChild(notification);
        
        // Add event listener to close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.add('closing');
            setTimeout(() => {
                container.removeChild(notification);
            }, 300);
        });
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (container.contains(notification)) {
                notification.classList.add('closing');
                setTimeout(() => {
                    if (container.contains(notification)) {
                        container.removeChild(notification);
                    }
                }, 300);
            }
        }, 5000);
    }
    
    // Event listeners
    if (alertFilters) {
        alertFilters.forEach(filter => {
            filter.addEventListener('click', () => {
                // Remove active class from all filters
                alertFilters.forEach(f => f.classList.remove('active'));
                
                // Add active class to clicked filter
                filter.classList.add('active');
                
                // Update active filter
                activeFilter = filter.dataset.filter;
                
                // Re-render alerts
                renderAlerts();
            });
        });
    }
    
    if (alertRefreshBtn) {
        alertRefreshBtn.addEventListener('click', fetchAlerts);
    }
    
    if (scanTrendingBtn) {
        scanTrendingBtn.addEventListener('click', scanTrending);
    }
    
    if (analysisForm) {
        analysisForm.addEventListener('submit', (e) => {
            e.preventDefault();
            analyzeContent(analysisInput.value);
        });
    }
    
    // Load icons (Feather Icons)
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof feather !== 'undefined') {
            feather.replace();
        } else {
            console.warn('Feather Icons not loaded');
        }
    });
    
    // Initial data load
    fetchAlerts();
    
    // Set up interval to refresh alerts
    setInterval(fetchAlerts, alertRefreshInterval);
});
