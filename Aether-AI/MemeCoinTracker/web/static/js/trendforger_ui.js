/**
 * TrendForger UI - Creator dashboard and influencer tweet tracker
 * Manages the display and interaction with the TrendForger service
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const tweetRefreshInterval = 30000; // 30 seconds
    const maxTweets = 10;
    let tweetData = [];
    let tokenData = [];
    let websocketConnected = false;
    let chartInstances = {};
    
    // Elements
    const tweetContainer = document.getElementById('tweet-container');
    const tweetRefreshBtn = document.getElementById('refresh-tweets');
    const webSocketStatus = document.getElementById('websocket-status');
    const createTokenForm = document.getElementById('create-token-form');
    const tokenContainer = document.getElementById('token-container');
    const contentAnalysisForm = document.getElementById('content-analysis-form');
    const analysisInput = document.getElementById('content-input');
    const analysisResults = document.getElementById('analysis-results');
    const viralityChart = document.getElementById('virality-chart');
    
    // Setup WebSocket connection
    function setupWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        const socket = new WebSocket(wsUrl);
        
        socket.onopen = function(e) {
            console.log("WebSocket connection established");
            websocketConnected = true;
            updateSocketStatus();
        };
        
        socket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'new_tweet') {
                    // Handle new tweet notification
                    tweetData.unshift(data.tweet);
                    if (tweetData.length > maxTweets) {
                        tweetData.pop();
                    }
                    renderTweets();
                    showNotification('New Tweet Detected', `New tweet from @${data.tweet.author} analyzed`);
                }
                
                if (data.type === 'token_created') {
                    // Handle new token creation notification
                    tokenData.unshift(data.token);
                    renderTokens();
                    showNotification('Token Created', `${data.token.name} (${data.token.symbol}) successfully created`);
                }
            } catch (e) {
                console.error("Error processing WebSocket message:", e);
            }
        };
        
        socket.onclose = function(event) {
            console.log("WebSocket connection closed");
            websocketConnected = false;
            updateSocketStatus();
            
            // Try to reconnect after a delay
            setTimeout(setupWebSocket, 5000);
        };
        
        socket.onerror = function(error) {
            console.error("WebSocket error:", error);
            websocketConnected = false;
            updateSocketStatus();
        };
    }
    
    // Try to establish WebSocket connection
    setupWebSocket();
    
    // Update WebSocket status indicator
    function updateSocketStatus() {
        if (!webSocketStatus) return;
        
        if (websocketConnected) {
            webSocketStatus.innerHTML = '<i class="feather icon-check-circle"></i> Connected';
            webSocketStatus.className = 'status-indicator connected';
        } else {
            webSocketStatus.innerHTML = '<i class="feather icon-x-circle"></i> Disconnected';
            webSocketStatus.className = 'status-indicator disconnected';
        }
    }
    
    // Fetch tweets from API
    function fetchTweets() {
        fetch('/api/tweets')
            .then(response => response.json())
            .then(data => {
                tweetData = data;
                renderTweets();
            })
            .catch(error => {
                console.error('Error fetching tweets:', error);
                if (tweetContainer) {
                    tweetContainer.innerHTML = `
                        <div class="error-message">
                            <i class="feather icon-alert-triangle"></i>
                            <p>Failed to load tweets: ${error.message || 'Unknown error'}</p>
                        </div>
                    `;
                }
            });
    }
    
    // Fetch tokens from API
    function fetchTokens() {
        fetch('/api/tokens')
            .then(response => response.json())
            .then(data => {
                tokenData = data;
                renderTokens();
            })
            .catch(error => {
                console.error('Error fetching tokens:', error);
                if (tokenContainer) {
                    tokenContainer.innerHTML = `
                        <div class="error-message">
                            <i class="feather icon-alert-triangle"></i>
                            <p>Failed to load tokens: ${error.message || 'Unknown error'}</p>
                        </div>
                    `;
                }
            });
    }
    
    // Fetch influencers list
    function fetchInfluencers() {
        fetch('/api/influencers')
            .then(response => response.json())
            .then(data => {
                renderInfluencers(data);
            })
            .catch(error => {
                console.error('Error fetching influencers:', error);
                const influencerContainer = document.getElementById('influencer-list');
                if (influencerContainer) {
                    influencerContainer.innerHTML = `
                        <div class="error-message">
                            <i class="feather icon-alert-triangle"></i>
                            <p>Failed to load influencers: ${error.message || 'Unknown error'}</p>
                        </div>
                    `;
                }
            });
    }
    
    // Render tweets
    function renderTweets() {
        if (!tweetContainer) return;
        
        if (!tweetData || tweetData.length === 0) {
            tweetContainer.innerHTML = `
                <div class="empty-state">
                    <i class="feather icon-twitter"></i>
                    <h3>No Tweets Found</h3>
                    <p>No influential tweets have been detected yet.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        tweetData.forEach(tweet => {
            const tweetId = tweet.tweet_id || tweet.id;
            const author = tweet.author;
            const content = tweet.content;
            const createdAt = formatDate(tweet.created_at);
            const sentimentScore = tweet.sentiment_score || 0;
            const viralScore = tweet.viral_score || 0;
            
            // Determine sentiment class
            const sentimentClass = sentimentScore > 0.2 ? 'positive' : sentimentScore < -0.2 ? 'negative' : 'neutral';
            const viralClass = viralScore > 0.7 ? 'high' : viralScore > 0.4 ? 'medium' : 'low';
            
            // Format keywords
            let keywordsHtml = '';
            if (tweet.keywords && tweet.keywords.length > 0) {
                keywordsHtml = `
                    <div class="tweet-keywords">
                        ${tweet.keywords.map(keyword => 
                            `<span class="keyword-tag">${keyword}</span>`
                        ).join('')}
                    </div>
                `;
            }
            
            html += `
                <div class="tweet-card" data-id="${tweetId}">
                    <div class="tweet-header">
                        <div class="tweet-author">
                            <i class="feather icon-twitter"></i>
                            <span>@${author}</span>
                        </div>
                        <div class="tweet-time">${createdAt}</div>
                    </div>
                    <div class="tweet-body">
                        <p class="tweet-content">${content}</p>
                        ${keywordsHtml}
                    </div>
                    <div class="tweet-metrics">
                        <div class="metric">
                            <span class="metric-label">Sentiment</span>
                            <div class="progress-bar">
                                <div class="progress ${sentimentClass}" style="width: ${((sentimentScore + 1) / 2 * 100).toFixed(0)}%"></div>
                            </div>
                            <span class="metric-value ${sentimentClass}">${sentimentScore.toFixed(2)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Viral Potential</span>
                            <div class="progress-bar">
                                <div class="progress ${viralClass}" style="width: ${(viralScore * 100).toFixed(0)}%"></div>
                            </div>
                            <span class="metric-value ${viralClass}">${(viralScore * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                    <div class="tweet-actions">
                        <button class="btn analyze-tweet" data-content="${encodeURIComponent(content)}">
                            <i class="feather icon-search"></i> Analyze
                        </button>
                        <button class="btn create-token-btn" data-content="${encodeURIComponent(content)}">
                            <i class="feather icon-dollar-sign"></i> Create Token
                        </button>
                    </div>
                </div>
            `;
        });
        
        tweetContainer.innerHTML = html;
        
        // Attach event listeners
        document.querySelectorAll('.analyze-tweet').forEach(button => {
            button.addEventListener('click', () => {
                const content = decodeURIComponent(button.dataset.content);
                analyzeContent(content);
                
                // Scroll to analysis section
                const analysisSection = document.getElementById('content-analysis-section');
                if (analysisSection) {
                    analysisSection.scrollIntoView({ behavior: 'smooth' });
                }
                
                // Set content in the form
                if (analysisInput) {
                    analysisInput.value = content;
                }
            });
        });
        
        document.querySelectorAll('.create-token-btn').forEach(button => {
            button.addEventListener('click', () => {
                const content = decodeURIComponent(button.dataset.content);
                showCreateTokenModal(content);
            });
        });
    }
    
    // Render tokens
    function renderTokens() {
        if (!tokenContainer) return;
        
        if (!tokenData || tokenData.length === 0) {
            tokenContainer.innerHTML = `
                <div class="empty-state">
                    <i class="feather icon-dollar-sign"></i>
                    <h3>No Tokens Created</h3>
                    <p>You haven't created any tokens yet.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        tokenData.forEach(token => {
            const marketCap = token.market_cap ? `$${formatNumber(token.market_cap)}` : 'N/A';
            const explorerUrl = token.blockchain === 'ethereum' 
                ? `https://etherscan.io/token/${token.address}`
                : `https://explorer.solana.com/address/${token.address}`;
            
            html += `
                <div class="token-card" data-id="${token.id}">
                    <div class="token-header">
                        <h3 class="token-name">${token.name} <span class="token-symbol">${token.symbol}</span></h3>
                        <div class="token-blockchain">${token.blockchain}</div>
                    </div>
                    <div class="token-body">
                        <div class="token-info">
                            <div class="info-item">
                                <span class="info-label">Creator</span>
                                <span class="info-value">${token.creator}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Created</span>
                                <span class="info-value">${formatDate(token.created_at)}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Market Cap</span>
                                <span class="info-value">${marketCap}</span>
                            </div>
                        </div>
                        <div class="token-address">
                            <span class="address-label">Address</span>
                            <span class="address-value">${truncateText(token.address, 16)}</span>
                        </div>
                    </div>
                    <div class="token-actions">
                        <a href="${explorerUrl}" target="_blank" class="btn secondary">
                            <i class="feather icon-external-link"></i> Explorer
                        </a>
                        <button class="btn primary track-royalties" data-address="${token.address}" data-blockchain="${token.blockchain}">
                            <i class="feather icon-bar-chart-2"></i> Track Royalties
                        </button>
                    </div>
                </div>
            `;
        });
        
        tokenContainer.innerHTML = html;
        
        // Attach event listeners
        document.querySelectorAll('.track-royalties').forEach(button => {
            button.addEventListener('click', () => {
                const address = button.dataset.address;
                const blockchain = button.dataset.blockchain;
                showRoyaltyTrackingModal(address, blockchain);
            });
        });
    }
    
    // Render influencers
    function renderInfluencers(influencers) {
        const influencerContainer = document.getElementById('influencer-list');
        if (!influencerContainer) return;
        
        if (!influencers || influencers.length === 0) {
            influencerContainer.innerHTML = `
                <div class="empty-state">
                    <i class="feather icon-users"></i>
                    <h3>No Influencers</h3>
                    <p>No influencers are being tracked.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        influencers.forEach(influencer => {
            html += `
                <div class="influencer-card">
                    <div class="influencer-info">
                        <h3 class="influencer-name">${influencer.name}</h3>
                        <div class="influencer-handle">@${influencer.twitter_handle}</div>
                    </div>
                    <div class="influencer-actions">
                        <a href="https://twitter.com/${influencer.twitter_handle}" target="_blank" class="btn secondary small">
                            <i class="feather icon-twitter"></i> View Profile
                        </a>
                    </div>
                </div>
            `;
        });
        
        influencerContainer.innerHTML = html;
    }
    
    // Analyze content for meme coin potential
    function analyzeContent(content) {
        if (!content || !content.trim()) {
            showNotification('Error', 'Please enter content to analyze', 'error');
            return;
        }
        
        // Show loading state
        if (analysisResults) {
            analysisResults.innerHTML = `
                <div class="loading-indicator">
                    <div class="spinner"></div>
                    <p>Analyzing content...</p>
                </div>
            `;
        }
        
        // Send analysis request
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: content })
        })
        .then(response => response.json())
        .then(data => {
            renderAnalysisResults(data);
            updateViralityChart(data);
        })
        .catch(error => {
            console.error('Error analyzing content:', error);
            if (analysisResults) {
                analysisResults.innerHTML = `
                    <div class="error-message">
                        <i class="feather icon-alert-triangle"></i>
                        <p>Analysis failed: ${error.message || 'Unknown error'}</p>
                    </div>
                `;
            }
        });
    }
    
    // Render analysis results
    function renderAnalysisResults(data) {
        if (!analysisResults) return;
        
        const sentimentScore = data.sentiment_score || 0;
        const viralScore = data.viral_score || 0;
        
        // Determine classes based on scores
        const sentimentClass = sentimentScore > 0.2 ? 'positive' : sentimentScore < -0.2 ? 'negative' : 'neutral';
        const viralClass = viralScore > 0.7 ? 'high' : viralScore > 0.4 ? 'medium' : 'low';
        
        // Format keywords
        let keywordsHtml = '<p>No keywords extracted.</p>';
        if (data.keywords && data.keywords.length > 0) {
            keywordsHtml = `
                <div class="keyword-cloud">
                    ${data.keywords.map(keyword => 
                        `<span class="keyword-tag">${keyword}</span>`
                    ).join('')}
                </div>
            `;
        }
        
        // Format potential matches
        let matchesHtml = '<p>No potential coin matches found.</p>';
        if (data.potential_matches && data.potential_matches.length > 0) {
            matchesHtml = `
                <div class="match-list">
                    ${data.potential_matches.map(match => {
                        const matchScore = match.match_score || 0;
                        const matchClass = matchScore > 0.7 ? 'high' : matchScore > 0.4 ? 'medium' : 'low';
                        
                        return `
                            <div class="match-item ${matchClass}">
                                <div class="match-header">
                                    <h4>${match.name} (${match.symbol})</h4>
                                    <span class="match-score ${matchClass}">${(matchScore * 100).toFixed(0)}%</span>
                                </div>
                                <div class="match-body">
                                    <p><strong>Keyword:</strong> ${match.match_keyword}</p>
                                    <p><strong>Blockchain:</strong> ${match.blockchain}</p>
                                </div>
                                <div class="match-footer">
                                    <a href="${match.blockchain === 'ethereum' ? 'https://etherscan.io/token/' : 'https://explorer.solana.com/address/'}${match.address}" 
                                       target="_blank" class="btn secondary small">
                                        <i class="feather icon-external-link"></i> Explorer
                                    </a>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }
        
        analysisResults.innerHTML = `
            <div class="analysis-container">
                <div class="analysis-section">
                    <h3>Content Analysis</h3>
                    <div class="score-summary">
                        <div class="score-item ${sentimentClass}">
                            <span class="score-label">Sentiment</span>
                            <span class="score-value">${sentimentScore.toFixed(2)}</span>
                            <span class="score-description">
                                ${sentimentScore > 0.2 ? 'Positive' : sentimentScore < -0.2 ? 'Negative' : 'Neutral'}
                            </span>
                        </div>
                        <div class="score-item ${viralClass}">
                            <span class="score-label">Viral Potential</span>
                            <span class="score-value">${(viralScore * 100).toFixed(0)}%</span>
                            <span class="score-description">
                                ${viralScore > 0.7 ? 'High' : viralScore > 0.4 ? 'Medium' : 'Low'}
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="analysis-section">
                    <h3>Extracted Keywords</h3>
                    ${keywordsHtml}
                </div>
                
                <div class="analysis-section">
                    <h3>Potential Coin Matches</h3>
                    ${matchesHtml}
                </div>
                
                <div class="analysis-actions">
                    <button class="btn primary create-token-from-analysis">
                        <i class="feather icon-dollar-sign"></i> Create Token
                    </button>
                </div>
            </div>
        `;
        
        // Attach event listeners
        const createTokenBtn = analysisResults.querySelector('.create-token-from-analysis');
        if (createTokenBtn) {
            createTokenBtn.addEventListener('click', () => {
                showCreateTokenModal(data.content, data.keywords);
            });
        }
    }
    
    // Update virality chart
    function updateViralityChart(data) {
        if (!viralityChart) return;
        
        // Destroy existing chart if it exists
        if (chartInstances.virality) {
            chartInstances.virality.destroy();
        }
        
        // Prepare factors that contribute to virality
        const viralFactors = {
            'Sentiment': (data.sentiment_score + 1) / 2, // Convert -1:1 to 0:1
            'Keyword Strength': data.keywords ? Math.min(data.keywords.length / 10, 1) : 0,
            'Content Quality': Math.random() * 0.3 + 0.5, // Placeholder, would be calculated in real implementation
            'Influencer Impact': 0.7, // Placeholder
            'Timing': Math.random() * 0.3 + 0.6 // Placeholder
        };
        
        // Create chart data
        const chartData = {
            labels: Object.keys(viralFactors),
            datasets: [
                {
                    label: 'Virality Factors',
                    data: Object.values(viralFactors),
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                    pointRadius: 4
                }
            ]
        };
        
        // Create chart
        chartInstances.virality = new Chart(viralityChart, {
            type: 'radar',
            data: chartData,
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Score: ${(context.raw * 100).toFixed(0)}%`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Show create token modal
    function showCreateTokenModal(content, keywords) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('create-token-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'create-token-modal';
            modal.className = 'modal';
            
            document.body.appendChild(modal);
        }
        
        // Generate token name and symbol from content or keywords
        let suggestedName = '';
        let suggestedSymbol = '';
        
        if (keywords && keywords.length > 0) {
            // Use first keyword as base for name
            suggestedName = keywords[0].charAt(0).toUpperCase() + keywords[0].slice(1);
            
            // If there's a second keyword, add it
            if (keywords.length > 1) {
                suggestedName += keywords[1].charAt(0).toUpperCase() + keywords[1].slice(1);
            }
            
            // Generate symbol from name
            suggestedSymbol = suggestedName.replace(/[aeiou]/gi, '').substring(0, 4).toUpperCase();
            if (suggestedSymbol.length < 3) {
                suggestedSymbol = suggestedName.substring(0, 4).toUpperCase();
            }
            
            // Add "Coin" to name
            suggestedName += " Coin";
        } else if (content) {
            // Extract words from content
            const words = content.split(/\s+/).filter(word => word.length > 3);
            if (words.length > 0) {
                suggestedName = words[0].charAt(0).toUpperCase() + words[0].slice(1);
                suggestedSymbol = suggestedName.substring(0, 3).toUpperCase();
                suggestedName += " Token";
            } else {
                suggestedName = "Meme Token";
                suggestedSymbol = "MEME";
            }
        } else {
            suggestedName = "Meme Token";
            suggestedSymbol = "MEME";
        }
        
        // Populate modal content
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-container">
                <div class="modal-header">
                    <h2>Create New Token</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-content">
                    <form id="token-creation-form">
                        <div class="form-group">
                            <label for="token-name">Token Name</label>
                            <input type="text" id="token-name" name="token-name" value="${suggestedName}" required>
                        </div>
                        <div class="form-group">
                            <label for="token-symbol">Token Symbol</label>
                            <input type="text" id="token-symbol" name="token-symbol" value="${suggestedSymbol}" required>
                        </div>
                        <div class="form-group">
                            <label for="token-creator">Creator Name</label>
                            <input type="text" id="token-creator" name="token-creator" required>
                        </div>
                        <div class="form-group">
                            <label for="token-supply">Initial Supply</label>
                            <input type="number" id="token-supply" name="token-supply" value="1000000" required>
                        </div>
                        <div class="form-group">
                            <label for="token-description">Description</label>
                            <textarea id="token-description" name="token-description" rows="3">${content || 'A new meme token'}</textarea>
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn secondary close-modal">Cancel</button>
                            <button type="submit" class="btn primary">Create Token</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        // Show modal
        modal.classList.add('open');
        document.body.classList.add('modal-open');
        
        // Focus on first input
        setTimeout(() => {
            modal.querySelector('#token-name').focus();
        }, 100);
        
        // Attach event listeners
        modal.querySelector('.modal-close').addEventListener('click', () => closeModal(modal));
        modal.querySelector('.modal-overlay').addEventListener('click', () => closeModal(modal));
        modal.querySelector('.close-modal').addEventListener('click', () => closeModal(modal));
        
        const form = modal.querySelector('#token-creation-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const tokenData = {
                name: form.querySelector('#token-name').value,
                symbol: form.querySelector('#token-symbol').value,
                creator: form.querySelector('#token-creator').value,
                initial_supply: parseInt(form.querySelector('#token-supply').value),
                description: form.querySelector('#token-description').value
            };
            
            createToken(tokenData, modal);
        });
    }
    
    // Show royalty tracking modal
    function showRoyaltyTrackingModal(address, blockchain) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('royalty-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'royalty-modal';
            modal.className = 'modal';
            
            document.body.appendChild(modal);
        }
        
        // Show loading state
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-container">
                <div class="modal-header">
                    <h2>Royalty Tracking</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-content">
                    <div class="loading-indicator">
                        <div class="spinner"></div>
                        <p>Loading royalty data...</p>
                    </div>
                </div>
            </div>
        `;
        
        // Show modal
        modal.classList.add('open');
        document.body.classList.add('modal-open');
        
        // Attach close event listeners
        modal.querySelector('.modal-close').addEventListener('click', () => closeModal(modal));
        modal.querySelector('.modal-overlay').addEventListener('click', () => closeModal(modal));
        
        // In a real implementation, we would fetch royalty data from the API
        // For this demo, we'll simulate it
        setTimeout(() => {
            const royaltyData = simulateRoyaltyData(address, blockchain);
            renderRoyaltyData(modal, royaltyData);
        }, 1500);
    }
    
    // Create token
    function createToken(tokenData, modal) {
        // Show loading state in the modal
        modal.querySelector('.form-actions').innerHTML = `
            <div class="loading-indicator">
                <div class="spinner"></div>
                <p>Creating token...</p>
            </div>
        `;
        
        // Disable form inputs
        const inputs = modal.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.disabled = true;
        });
        
        // Create token via API
        fetch('/api/tokens', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tokenData)
        })
        .then(response => response.json())
        .then(data => {
            // Add the new token to the token data and re-render
            tokenData.unshift(data);
            renderTokens();
            
            // Close the modal
            closeModal(modal);
            
            // Show success notification
            showNotification('Token Created', `${data.name} (${data.symbol}) has been successfully created!`);
        })
        .catch(error => {
            console.error('Error creating token:', error);
            
            // Show error state in the modal
            modal.querySelector('.form-actions').innerHTML = `
                <div class="error-message">
                    <i class="feather icon-alert-triangle"></i>
                    <p>Failed to create token: ${error.message || 'Unknown error'}</p>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn secondary close-modal">Cancel</button>
                    <button type="submit" class="btn primary">Try Again</button>
                </div>
            `;
            
            // Re-enable form inputs
            inputs.forEach(input => {
                input.disabled = false;
            });
            
            // Reattach event listeners
            modal.querySelector('.close-modal').addEventListener('click', () => closeModal(modal));
        });
    }
    
    // Simulate royalty data for demo
    function simulateRoyaltyData(address, blockchain) {
        // Create a deterministic seed based on the address
        const seed = parseInt(address.substring(2, 10), 16);
        const random = (min, max) => {
            const x = Math.sin(seed + tokenData.length) * 10000;
            return min + (x - Math.floor(x)) * (max - min);
        };
        
        // Generate mock royalty data
        const totalTransactions = Math.floor(random(50, 500));
        const totalVolume = random(10000, 1000000);
        const royaltyRate = 0.03; // 3%
        const totalRoyalties = totalVolume * royaltyRate;
        
        // Generate daily data for the chart
        const days = 7;
        const dailyData = [];
        
        let cumulativeRoyalties = 0;
        for (let i = 0; i < days; i++) {
            const dailyVolume = totalVolume / days * random(0.5, 1.5);
            const dailyRoyalty = dailyVolume * royaltyRate;
            cumulativeRoyalties += dailyRoyalty;
            
            const date = new Date();
            date.setDate(date.getDate() - (days - i - 1));
            
            dailyData.push({
                date: date.toISOString().split('T')[0],
                volume: dailyVolume,
                royalty: dailyRoyalty,
                cumulative: cumulativeRoyalties
            });
        }
        
        // Generate mock transactions
        const transactions = [];
        for (let i = 0; i < 5; i++) {
            const amount = random(1000, 10000);
            const royalty = amount * royaltyRate;
            
            const date = new Date();
            date.setHours(date.getHours() - i);
            
            transactions.push({
                tx_hash: `0x${Math.floor(random(0, 0xffffffffffff)).toString(16).padStart(12, '0')}`,
                timestamp: date.toISOString(),
                amount: amount,
                royalty_amount: royalty,
                from: `0x${Math.floor(random(0, 0xffffffffffff)).toString(16).padStart(12, '0')}`,
                to: `0x${Math.floor(random(0, 0xffffffffffff)).toString(16).padStart(12, '0')}`
            });
        }
        
        return {
            token_address: address,
            blockchain: blockchain,
            period_start: dailyData[0].date,
            period_end: dailyData[dailyData.length - 1].date,
            total_transactions: totalTransactions,
            total_volume: totalVolume,
            total_royalties: totalRoyalties,
            royalty_rate: royaltyRate,
            daily_data: dailyData,
            transactions: transactions
        };
    }
    
    // Render royalty data in the modal
    function renderRoyaltyData(modal, data) {
        const content = modal.querySelector('.modal-content');
        
        // Format the data
        const formattedTotalVolume = formatCurrency(data.total_volume);
        const formattedTotalRoyalties = formatCurrency(data.total_royalties);
        const royaltyRate = (data.royalty_rate * 100).toFixed(1) + '%';
        
        content.innerHTML = `
            <div class="royalty-container">
                <div class="royalty-summary">
                    <div class="summary-item">
                        <span class="summary-label">Total Volume</span>
                        <span class="summary-value">${formattedTotalVolume}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Royalty Rate</span>
                        <span class="summary-value">${royaltyRate}</span>
                    </div>
                    <div class="summary-item highlight">
                        <span class="summary-label">Total Royalties</span>
                        <span class="summary-value">${formattedTotalRoyalties}</span>
                    </div>
                </div>
                
                <div class="royalty-chart-container">
                    <canvas id="royalty-chart"></canvas>
                </div>
                
                <div class="royalty-transactions">
                    <h3>Recent Transactions</h3>
                    <div class="transaction-list">
                        ${data.transactions.map(tx => `
                            <div class="transaction-item">
                                <div class="transaction-header">
                                    <span class="transaction-hash">${truncateText(tx.tx_hash, 8)}</span>
                                    <span class="transaction-time">${formatDate(tx.timestamp)}</span>
                                </div>
                                <div class="transaction-body">
                                    <div class="transaction-addresses">
                                        <span class="address-from">${truncateText(tx.from, 8)}</span>
                                        <i class="feather icon-arrow-right"></i>
                                        <span class="address-to">${truncateText(tx.to, 8)}</span>
                                    </div>
                                    <div class="transaction-amounts">
                                        <span class="amount-label">Amount:</span>
                                        <span class="amount-value">${formatCurrency(tx.amount)}</span>
                                        <span class="royalty-label">Royalty:</span>
                                        <span class="royalty-value">${formatCurrency(tx.royalty_amount)}</span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="royalty-actions">
                    <a href="${data.blockchain === 'ethereum' ? 'https://etherscan.io/token/' : 'https://explorer.solana.com/address/'}${data.token_address}" 
                       target="_blank" class="btn secondary">
                        <i class="feather icon-external-link"></i> View on Explorer
                    </a>
                    <button class="btn primary close-modal">Close</button>
                </div>
            </div>
        `;
        
        // Reattach close event listener
        modal.querySelector('.close-modal').addEventListener('click', () => closeModal(modal));
        
        // Create chart
        setTimeout(() => {
            const chartCanvas = document.getElementById('royalty-chart');
            if (chartCanvas) {
                const ctx = chartCanvas.getContext('2d');
                
                // Prepare chart data
                const labels = data.daily_data.map(d => d.date);
                const volumeData = data.daily_data.map(d => d.volume);
                const royaltyData = data.daily_data.map(d => d.royalty);
                const cumulativeData = data.daily_data.map(d => d.cumulative);
                
                const chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Daily Volume',
                                data: volumeData,
                                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                                borderColor: 'rgba(54, 162, 235, 1)',
                                borderWidth: 1,
                                yAxisID: 'y'
                            },
                            {
                                label: 'Daily Royalties',
                                data: royaltyData,
                                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                                borderColor: 'rgba(75, 192, 192, 1)',
                                borderWidth: 1,
                                yAxisID: 'y'
                            },
                            {
                                label: 'Cumulative Royalties',
                                data: cumulativeData,
                                type: 'line',
                                fill: false,
                                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                                borderColor: 'rgba(255, 99, 132, 1)',
                                borderWidth: 2,
                                pointRadius: 3,
                                yAxisID: 'y1'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: {
                                    display: true,
                                    text: 'Daily Values'
                                }
                            },
                            y1: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                                title: {
                                    display: true,
                                    text: 'Cumulative Royalties'
                                },
                                grid: {
                                    drawOnChartArea: false
                                }
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        let label = context.dataset.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        if (context.parsed.y !== null) {
                                            label += formatCurrency(context.parsed.y);
                                        }
                                        return label;
                                    }
                                }
                            }
                        }
                    }
                });
            }
        }, 100);
    }
    
    // Close modal
    function closeModal(modal) {
        if (!modal) return;
        modal.classList.remove('open');
        document.body.classList.remove('modal-open');
    }
    
    // Helper function to format dates
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
    
    // Helper function to truncate text
    function truncateText(text, maxLength) {
        if (!text) return '';
        
        if (text.length <= maxLength) return text;
        
        const start = text.substring(0, maxLength / 2);
        const end = text.substring(text.length - maxLength / 2);
        
        return `${start}...${end}`;
    }
    
    // Helper function to format numbers
    function formatNumber(num) {
        if (num === null || num === undefined) return 'N/A';
        
        if (num >= 1000000) {
            return `${(num / 1000000).toFixed(2)}M`;
        } else if (num >= 1000) {
            return `${(num / 1000).toFixed(2)}K`;
        } else {
            return num.toFixed(2);
        }
    }
    
    // Helper function to format currency
    function formatCurrency(amount) {
        if (amount === null || amount === undefined) return 'N/A';
        
        if (amount >= 1000000) {
            return `$${(amount / 1000000).toFixed(2)}M`;
        } else if (amount >= 1000) {
            return `$${(amount / 1000).toFixed(2)}K`;
        } else {
            return `$${amount.toFixed(2)}`;
        }
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
    if (tweetRefreshBtn) {
        tweetRefreshBtn.addEventListener('click', fetchTweets);
    }
    
    if (contentAnalysisForm) {
        contentAnalysisForm.addEventListener('submit', (e) => {
            e.preventDefault();
            analyzeContent(analysisInput.value);
        });
    }
    
    if (createTokenForm) {
        createTokenForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const name = document.getElementById('token-name').value;
            const symbol = document.getElementById('token-symbol').value;
            const creator = document.getElementById('token-creator').value;
            const supply = document.getElementById('token-supply').value;
            const description = document.getElementById('token-description').value;
            
            if (!name || !symbol || !creator || !supply) {
                showNotification('Error', 'Please fill in all required fields', 'error');
                return;
            }
            
            const tokenData = {
                name: name,
                symbol: symbol,
                creator: creator,
                initial_supply: parseInt(supply),
                description: description
            };
            
            // Create the token
            fetch('/api/tokens', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(tokenData)
            })
            .then(response => response.json())
            .then(data => {
                // Add the new token to our data and re-render
                tokenData.unshift(data);
                renderTokens();
                
                // Clear the form
                createTokenForm.reset();
                
                // Show success notification
                showNotification('Success', `Token ${data.name} (${data.symbol}) created successfully`);
            })
            .catch(error => {
                console.error('Error creating token:', error);
                showNotification('Error', `Failed to create token: ${error.message}`, 'error');
            });
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
    fetchTweets();
    fetchTokens();
    fetchInfluencers();
    
    // Set up interval to refresh tweets
    setInterval(fetchTweets, tweetRefreshInterval);
});
