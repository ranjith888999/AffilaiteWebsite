// Enhanced offer display function with better error handling
function displayOffers(offers) {
    try {
        // Validation
        if (!offers || !Array.isArray(offers) || offers.length === 0) {
            console.log('No offers to display or invalid offers data');
            return;
        }
        
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) {
            console.error('Chat messages container not found');
            return;
        }
        
        const offersDiv = document.createElement('div');
        offersDiv.className = 'message bot-message offers-message animate__animated animate__fadeInUp';
        
        const currentTime = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        // Start with header only
        offersDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <h4>🛍️ Found ${offers.length} Offers for You:</h4>
                    <div class="offers-grid" id="offersGrid-${Date.now()}">
                    </div>
                </div>
                <div class="message-time">${currentTime}</div>
            </div>
        `;
        
        // Add to DOM first for faster visible rendering
        messagesContainer.appendChild(offersDiv);
        scrollToBottom();
        
        // Get the grid element to append offers to
        const offersGrid = offersDiv.querySelector('.offers-grid');
        if (!offersGrid) {
            console.error('Offers grid not found');
            return;
        }
        
        // Use requestAnimationFrame for smoother rendering
        requestAnimationFrame(() => {
            try {
                // Process offers in batches to avoid UI blocking
                const processBatch = (offers, startIndex, batchSize) => {
                    const endIndex = Math.min(startIndex + batchSize, offers.length);
                    
                    for (let i = startIndex; i < endIndex; i++) {
                        try {
                            appendSingleOffer(offers[i], offersGrid);
                        } catch (offerError) {
                            console.error(`Error rendering offer at index ${i}:`, offerError);
                            // Continue with next offer instead of failing entire batch
                        }
                    }
                    
                    // Process next batch if needed
                    if (endIndex < offers.length) {
                        setTimeout(() => {
                            processBatch(offers, endIndex, batchSize);
                        }, 50);
                    }
                    
                    scrollToBottom();
                };
                
                // Start processing in batches of 2
                processBatch(offers, 0, 2);
                
            } catch (batchError) {
                console.error('Error processing offer batches:', batchError);
            }
        });
    } catch (error) {
        console.error('Error in displayOffers:', error);
    }
}

// Render a single offer with better error handling
function appendSingleOffer(offer, container) {
    // Validate offer object
    if (!offer || typeof offer !== 'object') {
        console.error('Invalid offer object:', offer);
        return;
    }
    
    // Safe access to properties with defaults
    const safeGet = (obj, path, defaultValue) => {
        try {
            const value = path.split('.').reduce((o, key) => o && o[key], obj);
            return (value !== undefined && value !== null) ? value : defaultValue;
        } catch (e) {
            return defaultValue;
        }
    };
    
    // Extract values safely
    const id = safeGet(offer, 'id', 0);
    const title = safeGet(offer, 'title', 'Special Offer');
    const description = safeGet(offer, 'description', 'Great deal available!').substring(0, 100) + '...';
    const imageUrl = safeGet(offer, 'image_url', '/static/images/placeholder_small.jpg');
    const couponCode = safeGet(offer, 'coupon_code', '').trim();
    const affiliateUrl = safeGet(offer, 'affiliate_url', '#').trim() || '#';
    const websiteUrl = safeGet(offer, 'website_url', affiliateUrl).trim() || affiliateUrl;
    const similarity = Math.round((safeGet(offer, 'similarity', 0) * 100)) || 0;
    const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    const offerCard = document.createElement('div');
    offerCard.className = 'offer-card';
    
    offerCard.innerHTML = `
        <div class="offer-image">
            <img src="${imageUrl}" 
                 alt="${title}" 
                 loading="lazy"
                 onerror="this.onerror=null; this.src='/static/images/placeholder_small.jpg';">
            ${similarity > 70 ? '<div class="relevance-badge">🎯 ' + similarity + '% match</div>' : ''}
        </div>
        <div class="offer-content">
            <h5>${title}</h5>
            <p class="offer-description">${description}</p>
            
            ${couponCode ? `<div class="coupon-section">
                <span class="coupon-label">💰 Coupon Code:</span>
                <div class="coupon-code-container">
                    <code class="coupon-code">${couponCode}</code>
                    <button class="copy-btn coupon-copy" onclick="copyToClipboard('${couponCode}', 'coupon')" title="Copy coupon code">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
            </div>` : ''}
            
            <div class="offer-links">
                ${affiliateUrl && affiliateUrl !== '#' ? `<a href="${affiliateUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm" onclick="event.stopPropagation();">
                    <i class="fas fa-external-link-alt"></i> Get Deal
                </a>` : ''}
            </div>
                    
            <div class="offer-feedback" data-offer-id="${id}" data-timestamp="${timestamp}">
                <button class="feedback-btn like-btn" onclick="submitOfferFeedback('like', ${id}, '${timestamp}')" title="Like this offer">
                    <i class="fas fa-thumbs-up"></i>
                </button>
                <button class="feedback-btn dislike-btn" onclick="submitOfferFeedback('dislike', ${id}, '${timestamp}')" title="Dislike this offer">
                    <i class="fas fa-thumbs-down"></i>
                </button>
                <button class="feedback-btn feedback-btn-text" onclick="openOfferFeedbackModal(${id}, '${title.replace(/'/g, "\\'")}', '${timestamp}')" title="Provide feedback on this offer">
                    <i class="fas fa-comment"></i>
                </button>
            </div>
        </div>
    `;
    
    container.appendChild(offerCard);
}
