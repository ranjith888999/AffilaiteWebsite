/**
 * Enhanced DealsHub AI Chat Interface - Modern UI
 * Provides ChatGPT-like conversational experience with stunning modern design
 */

window.EnhancedDealsHubChat = (function() {
    'use strict';

    // State management
    let state = {
        sessionId: null,
        isLoading: false,
        isInConversation: false,
        messages: [],
        currentQuery: '',
        currentResponse: null,
        userData: null  // Store user information for personalization
    };

    // DOM elements
    let elements = {};

    /**
     * Initialize the Enhanced DealsHub AI chat interface
     */
    function init() {
        cacheElements();
        bindEvents();
        generateSessionId();
        fetchUserData();  // Fetch logged-in user information
        console.log('🤖 Enhanced DealsHub AI Chat (Modern UI) initialized');
    }

    /**
     * Fetch current user data for personalization
     */
    async function fetchUserData() {
        try {
            const response = await fetch('/auth/user');
            if (response.ok) {
                const data = await response.json();
                if (data.authenticated && data.user) {
                    state.userData = {
                        name: data.user.name,
                        email: data.user.email,
                        first_name: data.user.name ? data.user.name.split(' ')[0] : null
                    };
                    console.log('👤 User authenticated:', state.userData.first_name);
                }
            }
        } catch (error) {
            console.log('User not authenticated or error fetching user data');
        }
    }

    /**
     * Cache DOM elements for performance
     */
    function cacheElements() {
        elements = {
            // Main form and input
            dealshubForm: document.getElementById('dealshubForm'),
            dealshubInput: document.getElementById('dealshubInput'),
            
            // Conversation form and input
            conversationForm: document.getElementById('conversationForm'),
            conversationInput: document.getElementById('conversationInput'),
            
            // Headers
            mainHeader: document.getElementById('mainHeader'),
            
            // States
            welcomeState: document.getElementById('welcomeState'),
            conversationState: document.getElementById('conversationState'),
            modeSelectionSection: document.getElementById('modeSelectionSection'),
            
            // Messages
            chatMessages: document.getElementById('chatMessages'),
            
            // Controls
            floatingControls: document.getElementById('floatingControls'),
            backToSearch: document.getElementById('backToSearch'),
            loadingIndicator: document.getElementById('loadingIndicator'),
            feedbackAlert: document.getElementById('feedbackAlert'),
            
            // Action cards and suggestion pills
            actionCards: document.querySelectorAll('.action-card'),
            suggestionPills: document.querySelectorAll('.suggestion-pill'),
            
            // Voice button
            voiceBtn: document.getElementById('voiceBtn'),
            
            // Fullscreen button
            fullscreenToggle: document.getElementById('fullscreenToggle')
        };
    }

    /**
     * Bind event listeners
     */
    function bindEvents() {
        // Main form submission
        if (elements.dealshubForm) {
            elements.dealshubForm.addEventListener('submit', handleMainFormSubmit);
        }
        
        // Conversation form submission
        if (elements.conversationForm) {
            elements.conversationForm.addEventListener('submit', handleConversationSubmit);
        }
        
        // Back to search button
        if (elements.backToSearch) {
            elements.backToSearch.addEventListener('click', backToSearchMode);
        }
        
        // Action cards
        elements.actionCards.forEach(card => {
            card.addEventListener('click', () => {
                const query = card.dataset.query;
                if (query) {
                    elements.dealshubInput.value = query;
                    handleSearch(query);
                }
            });
        });
        
        // Suggestion pills
        elements.suggestionPills.forEach(pill => {
            pill.addEventListener('click', () => {
                const query = pill.dataset.query;
                if (query) {
                    elements.dealshubInput.value = query;
                    handleSearch(query);
                }
            });
        });
        
        // Voice button (placeholder)
        if (elements.voiceBtn) {
            elements.voiceBtn.addEventListener('click', handleVoiceInput);
        }
        
        // Fullscreen toggle
        if (elements.fullscreenToggle) {
            elements.fullscreenToggle.addEventListener('click', toggleFullscreen);
        }
        
        // Listen for fullscreen changes to update the icon
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement) {
                const icon = elements.fullscreenToggle.querySelector('i');
                icon.classList.remove('fa-compress');
                icon.classList.add('fa-expand');
                elements.fullscreenToggle.title = "Toggle Fullscreen";
            }
        });
    }

    /**
     * Generate unique session ID
     */
    function generateSessionId() {
        state.sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Handle main form submission
     */
    async function handleMainFormSubmit(e) {
        e.preventDefault();
        const query = elements.dealshubInput.value.trim();
        if (!query) return;
        
        await handleSearch(query);
    }

    /**
     * Handle conversation form submission
     */
    async function handleConversationSubmit(e) {
        e.preventDefault();
        const query = elements.conversationInput.value.trim();
        if (!query) return;
        
        // Store current query for potential reuse
        state.currentQuery = query;
        
        // Add user message to conversation
        addMessageToConversation(query, 'user');
        elements.conversationInput.value = '';
        
        await performSearch(query);
    }

    /**
     * Handle search and switch to conversation mode
     */
    async function handleSearch(query) {
        state.currentQuery = query;
        
        // Switch to conversation mode
        switchToConversationMode();
        
        // Add user message
        addMessageToConversation(query, 'user');
        
        // Perform search
        await performSearch(query);
    }

    /**
     * Toggle fullscreen mode
     */
    function toggleFullscreen() {
        const chatSection = document.querySelector('.modern-chat-section');
        const icon = elements.fullscreenToggle.querySelector('i');

        if (!document.fullscreenElement) {
            chatSection.requestFullscreen().catch(err => {
                alert(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
            });
            icon.classList.remove('fa-expand');
            icon.classList.add('fa-compress');
            elements.fullscreenToggle.title = "Exit Fullscreen";
        } else {
            document.exitFullscreen();
            icon.classList.remove('fa-compress');
            icon.classList.add('fa-expand');
            elements.fullscreenToggle.title = "Toggle Fullscreen";
        }
    }

    /**
     * Perform the actual search
     */
    async function performSearch(query) {
        setLoading(true);
        
        try {
            // Prepare request body with user information for personalization
            const requestBody = { 
                message: query, 
                session_id: state.sessionId 
            };
            
            // Add user info if available for personalized responses
            if (state.userData && state.userData.first_name) {
                requestBody.user_info = {
                    name: state.userData.name,
                    first_name: state.userData.first_name,
                    email: state.userData.email
                };
            }
            
            const response = await fetch('/api/v2/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody),
            });

            if (!response.ok) {
                throw new Error('Failed to get a response from the server.');
            }

            const data = await response.json();
            state.currentResponse = data;
            
            console.log('Response received:', data.response.type);
            
            // Handle different response types
            if (data.response.type === 'limit_reached' || data.response.conversation_limit_reached) {
                // Conversation limit reached - show modal popup
                console.log('Showing conversation limit modal');
                // Prevent any further UI updates while modal is shown
                state.isLoading = false;
                setLoading(false);
                showConversationLimitModal(data.response.message);
                return; // Exit early to prevent any other processing
            } else if (data.response.type === 'greeting') {
                addGreetingResponse(data.response);
            } else if (data.response.type === 'offers') {
                addOffersResponse(data.response);
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            addMessageToConversation('Sorry, I encountered an error. Please try again.', 'bot');
        } finally {
            setLoading(false);
        }
    }

    /**
     * Switch from welcome to conversation mode
     */
    function switchToConversationMode() {
        // Hide main header and welcome state
        elements.mainHeader.style.display = 'none';
        elements.welcomeState.style.display = 'none';
        
        // Hide mode selection section during conversation (especially important on mobile)
        if (elements.modeSelectionSection) {
            elements.modeSelectionSection.style.display = 'none';
            elements.modeSelectionSection.style.visibility = 'hidden';
            elements.modeSelectionSection.classList.add('hidden-during-conversation');
        }
        
        // Show conversation state and floating controls
        elements.conversationState.style.display = 'flex';
        if (elements.floatingControls) {
            elements.floatingControls.style.display = 'flex';
        }
        
        state.isInConversation = true;
        
        // Focus on conversation input
        setTimeout(() => {
            elements.conversationInput.focus();
        }, 100);
    }

    /**
     * Switch back to search mode
     */
    function backToSearchMode() {
        // Generate a new session ID for fresh conversation
        generateSessionId();
        console.log('🔄 New session started:', state.sessionId);
        
        // Show main header and welcome state
        elements.mainHeader.style.display = 'flex';
        elements.welcomeState.style.display = 'flex';
        
        // Show mode selection section again
        if (elements.modeSelectionSection) {
            elements.modeSelectionSection.style.display = 'flex';
            elements.modeSelectionSection.style.visibility = 'visible';
            elements.modeSelectionSection.classList.remove('hidden-during-conversation');
        }
        
        // Hide conversation state and floating controls
        elements.conversationState.style.display = 'none';
        if (elements.floatingControls) {
            elements.floatingControls.style.display = 'none';
        }
        
        state.isInConversation = false;
        
        // Clear conversation and messages array
        elements.chatMessages.innerHTML = '';
        state.messages = [];
        elements.dealshubInput.value = '';
        elements.dealshubInput.focus();
    }

    /**
     * Add a message to the conversation
     */
    function addMessageToConversation(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;
        
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        
        if (type === 'user') {
            messageBubble.textContent = text;
        } else {
            messageBubble.innerHTML = text;
        }
        
        messageDiv.appendChild(messageBubble);
        elements.chatMessages.appendChild(messageDiv);
        
        // Scroll to show the new message
        scrollToLatestMessage(messageDiv);
    }

    /**
     * Add greeting response with suggestions
     */
    function addGreetingResponse(response) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message bot-message';
        
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        
        let html = `<div class="bot-greeting">
            <p>${response.message}</p>
        `;
        
        if (response.suggestions && response.suggestions.length > 0) {
            html += '<div class="conversation-suggestions">';
            response.suggestions.forEach(suggestion => {
                html += `<button class="suggestion-btn" data-query="${suggestion}">${suggestion}</button>`;
            });
            html += '</div>';
        }
        
        html += '</div>';
        messageBubble.innerHTML = html;
        
        messageDiv.appendChild(messageBubble);
        elements.chatMessages.appendChild(messageDiv);
        
        // Bind suggestion buttons
        messageDiv.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.dataset.query;
                elements.conversationInput.value = query;
                handleConversationSubmit({ preventDefault: () => {} });
            });
        });
        
        // Scroll to show the bot response
        scrollToLatestMessage(messageDiv);
    }

    /**
     * Show conversation limit modal popup
     */
    function showConversationLimitModal(message) {
        // Remove any existing modal first
        const existingModal = document.getElementById('conversationLimitModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Create modal overlay
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'conversation-limit-modal-overlay';
        modalOverlay.id = 'conversationLimitModal';
        
        const modalContent = `
            <div class="conversation-limit-modal">
                <div class="modal-icon">
                    <i class="fas fa-info-circle"></i>
                </div>
                <h3 class="modal-title">Conversation Limit Reached</h3>
                <p class="modal-message">${message}</p>
                <div class="modal-actions">
                    <button class="modal-btn modal-btn-primary" id="startNewConversationBtn">
                        <i class="fas fa-plus-circle"></i> OK - Start New Conversation
                    </button>
                </div>
            </div>
        `;
        
        modalOverlay.innerHTML = modalContent;
        document.body.appendChild(modalOverlay);
        
        // Use setTimeout to ensure DOM is ready
        setTimeout(() => {
            const okButton = document.getElementById('startNewConversationBtn');
            if (okButton) {
                okButton.addEventListener('click', function handleOkClick() {
                    // Get the last user query before closing modal
                    const lastQuery = state.currentQuery || elements.conversationInput?.value || '';
                    
                    console.log('OK button clicked, last query:', lastQuery);
                    
                    // Close modal
                    modalOverlay.remove();
                    
                    // Start new conversation
                    startNewConversationWithQuery(lastQuery);
                }, { once: true }); // Use once option to prevent multiple triggers
            } else {
                console.error('OK button not found in modal');
            }
        }, 100);
        
        // Prevent closing by clicking overlay
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                // Don't allow closing by clicking outside - just log for debugging
                console.log('Clicked outside modal, not closing');
                e.stopPropagation();
            }
        });
        
        console.log('Modal displayed successfully');
    }

    /**
     * Start a new conversation with the last query
     */
    function startNewConversationWithQuery(query) {
        // Generate new session ID
        generateSessionId();
        console.log('🔄 Starting new conversation with session:', state.sessionId);
        
        // Reset to welcome state first
        backToSearchMode();
        
        // If there was a query, automatically submit it in the new conversation
        if (query && query.trim()) {
            setTimeout(() => {
                elements.dealshubInput.value = query;
                handleSearch(query);
            }, 300);
        }
    }

    /**
     * Add conversation limit reached message (deprecated - keeping for compatibility)
     */
    function addConversationLimitMessage(message) {
        // Now just shows modal instead
        showConversationLimitModal(message);
    }

    /**
     * Start a new conversation session (exposed for button click)
     */
    function startNewSession() {
        backToSearchMode();
    }

    /**
     * Add offers response with modern cards
     */
    function addOffersResponse(response) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message bot-message';
        
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        
        let html = `<div class="bot-offers-response">
            <p class="response-message">${response.message}</p>
        `;
        
        if (response.offers && response.offers.length > 0) {
            html += '<div class="offers-grid">';
            response.offers.forEach(offer => {
                html += createOfferCardHTML(offer);
            });
            html += '</div>';
        }
        
        html += '</div>';
        messageBubble.innerHTML = html;
        
        messageDiv.appendChild(messageBubble);
        elements.chatMessages.appendChild(messageDiv);
        
        // Bind feedback buttons
        bindOfferFeedbacks(messageDiv);
        
        // Bind copy coupon buttons
        messageDiv.querySelectorAll('.copy-coupon').forEach(btn => {
            btn.addEventListener('click', async () => {
                const couponCode = btn.dataset.coupon;
                try {
                    await navigator.clipboard.writeText(couponCode);
                    btn.classList.add('copied');
                    btn.querySelector('i').className = 'fas fa-check';
                    setTimeout(() => {
                        btn.classList.remove('copied');
                        btn.querySelector('i').className = 'far fa-copy';
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy:', err);
                }
            });
        });

        // Bind description expand/collapse buttons
        messageDiv.querySelectorAll('.expand-description').forEach(btn => {
            btn.addEventListener('click', () => {
                const description = btn.closest('.offer-description');
                description.classList.toggle('collapsed');
            });
        });
        
        // Scroll to show the bot response with offers
        scrollToLatestMessage(messageDiv);
    }

    /**
     * Create HTML for a modern offer card
     */
    function createOfferCardHTML(offer) {
        const categories = offer.categories.map(cat => `<span class="offer-category">${cat}</span>`).join('');
        
        const description = offer.description || '';
        const isLongDescription = description.split(' ').length > 10; // Roughly 2 lines
        
        return `
            <div class="offer-card" data-offer-id="${offer.offer_id}">
                <a href="${offer.affiliate_url}" target="_blank" class="offer-image-container" style="display: contents;">
                    <img src="${offer.image_url}" alt="${offer.title}" class="offer-image" 
                         onerror="this.src='/static/images/placeholder.jpg'">
                    <span class="offer-campaign">${offer.campaign}</span>
                </a>
                <div class="offer-details">
                    <h3 class="offer-title">${offer.title}</h3>
                    ${offer.coupon_code ? 
                        `<div class="offer-coupon">
                            <span class="coupon-code">${offer.coupon_code}</span>
                            <button class="copy-coupon" data-coupon="${offer.coupon_code}" title="Copy coupon code">
                                <i class="far fa-copy"></i>
                            </button>
                        </div>` : 
                        '<div class="no-coupon">No Coupon Code Required</div>'
                    }
                    <div class="offer-description ${isLongDescription ? 'expandable collapsed' : ''}">
                        <p>${description}</p>
                        ${isLongDescription ? 
                            `<button class="expand-description">
                                <span class="more-text">More</span>
                                <span class="less-text">Less</span>
                                <i class="fas fa-chevron-down"></i>
                            </button>` : ''
                        }
                    </div>
                    <div class="offer-categories">${categories}</div>
                </div>
                <div class="offer-actions">
                    <div class="feedback-buttons">
                        <button class="feedback-like" title="Like this offer">
                            <i class="fas fa-thumbs-up"></i>
                        </button>
                        <button class="feedback-dislike" title="Dislike this offer">
                            <i class="fas fa-thumbs-down"></i>
                        </button>
                    </div>
                    <a href="${offer.affiliate_url}" target="_blank" class="get-deal-btn">
                        Get Deal <i class="fas fa-external-link-alt"></i>
                    </a>
                </div>
            </div>
        `;
    }

    /**
     * Bind feedback events for offers
     */
    function bindOfferFeedbacks(container) {
        container.querySelectorAll('.feedback-like, .feedback-dislike').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                
                const card = btn.closest('.offer-card');
                const offerId = parseInt(card.dataset.offerId);
                const feedbackType = btn.classList.contains('feedback-like') ? 'like' : 'dislike';
                
                await handleFeedback(offerId, feedbackType, card);
            });
        });
    }

    /**
     * Handle feedback submission
     */
    async function handleFeedback(offerId, feedbackType, card) {
        try {
            await fetch('/api/v2/chat/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: state.sessionId,
                    user_message: state.currentQuery,
                    bot_response: JSON.stringify(state.currentResponse),
                    feedback_type: feedbackType,
                    offer_id: offerId,
                }),
            });

            showFeedbackAlert();
            
            // Update UI to show feedback was given
            const likeBtn = card.querySelector('.feedback-like');
            const dislikeBtn = card.querySelector('.feedback-dislike');
            likeBtn.classList.remove('liked', 'disliked');
            dislikeBtn.classList.remove('liked', 'disliked');

            if (feedbackType === 'like') {
                likeBtn.classList.add('liked');
            } else {
                dislikeBtn.classList.add('disliked');
            }

        } catch (error) {
            console.error('Feedback error:', error);
        }
    }

    /**
     * Show/hide loading indicator
     */
    function setLoading(isLoading) {
        state.isLoading = isLoading;
        elements.loadingIndicator.style.display = isLoading ? 'flex' : 'none';
        
        if (isLoading && state.isInConversation) {
            // Add loading message to conversation
            const loadingDiv = document.createElement('div');
            // loadingDiv.className = 'chat-message bot-message loading-message';
            // loadingDiv.innerHTML = `
            //     <div class="message-bubble">
            //         <div class="loading-animation">
            //             <div class="loading-dots">
            //                 <span></span><span></span><span></span>
            //             </div>
            //             <span>Finding deals...</span>
            //         </div>
            //     </div>
            // `;
            elements.chatMessages.appendChild(loadingDiv);
            // Don't scroll for loading indicator
            // scrollToLatestMessage(loadingDiv);
            
            // Remove loading message when done
            setTimeout(() => {
                if (!isLoading && loadingDiv.parentNode) {
                    loadingDiv.remove();
                }
            }, 100);
        }
    }

    /**
     * Show feedback alert
     */
    function showFeedbackAlert() {
        elements.feedbackAlert.style.display = 'block';
        setTimeout(() => {
            elements.feedbackAlert.style.display = 'none';
        }, 2000);
    }

    /**
     * Handle voice input (placeholder)
     */
    function handleVoiceInput() {
        // Placeholder for voice functionality
        console.log('Voice input not implemented yet');
        
        // Visual feedback
        elements.voiceBtn.style.background = 'var(--secondary-gradient)';
        setTimeout(() => {
            elements.voiceBtn.style.background = '';
        }, 200);
    }

    /**
     * Scroll to show the latest message
     * This ensures users can see both their question and the bot's answer
     */
    function scrollToLatestMessage(messageElement) {
        if (!messageElement) return;
        
        setTimeout(() => {
            const container = elements.chatMessages;
            
            // For bot messages, we want to show both the user's question and the bot's answer
            // Get all messages to find the previous user message
            const allMessages = container.querySelectorAll('.chat-message');
            const messageIndex = Array.from(allMessages).indexOf(messageElement);
            
            // If this is a bot message and there's a user message before it
            if (messageElement.classList.contains('bot-message') && messageIndex > 0) {
                const previousMessage = allMessages[messageIndex - 1];
                if (previousMessage.classList.contains('user-message')) {
                    // Scroll to show the user's question at the top, which will also show the bot's answer
                    previousMessage.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'start',
                        inline: 'nearest'
                    });
                    return;
                }
            }
            
            // For user messages or standalone bot messages, scroll normally
            messageElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start',
                inline: 'nearest'
            });
        }, 100);
    }

    // Public API
    return {
        init: init,
        startNewSession: startNewSession
    };
})();

// Add loading dots animation styles if not already present
if (!document.querySelector('#loading-dots-style')) {
    const style = document.createElement('style');
    style.id = 'loading-dots-style';
    style.textContent = `
        .loading-animation {
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-secondary);
        }
        
        .loading-dots {
            display: flex;
            gap: 4px;
        }
        
        .loading-dots span {
            width: 8px;
            height: 8px;
            background: var(--border-focus);
            border-radius: 50%;
            animation: loadingDots 1.5s infinite;
        }
        
        .loading-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .loading-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes loadingDots {
            0%, 60%, 100% {
                opacity: 0.3;
                transform: scale(0.8);
            }
            30% {
                opacity: 1;
                transform: scale(1.2);
            }
        }
    `;
    document.head.appendChild(style);
}
