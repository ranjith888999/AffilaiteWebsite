/**
 * Enhanced DealsHub AI Chat Interface
 * Provides ChatGPT-like conversational experience while maintaining original UI
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
        currentResponse: null
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
        console.log('🤖 Enhanced DealsHub AI Chat initialized');
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
            conversationHeader: document.getElementById('conversationHeader'),
            
            // States
            welcomeState: document.getElementById('welcomeState'),
            conversationState: document.getElementById('conversationState'),
            
            // Messages
            chatMessages: document.getElementById('chatMessages'),
            
            // Controls
            backToSearch: document.getElementById('backToSearch'),
            loadingIndicator: document.getElementById('loadingIndicator'),
            feedbackAlert: document.getElementById('feedbackAlert'),
            
            // Suggestion pills
            suggestionPills: document.querySelectorAll('.suggestion-pill'),
            
            // Voice button
            voiceBtn: document.getElementById('voiceBtn')
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
        // Store current query
        state.currentQuery = query;
        
        // Switch to conversation mode
        switchToConversationMode();
        
        // Add user message
        addMessageToConversation(query, 'user');
        
        // Perform search
        await performSearch(query);
    }

    /**
     * Perform the actual search
     */
    async function performSearch(query) {
        setLoading(true);
        
        try {
            const response = await fetch('/api/v2/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: query, 
                    session_id: state.sessionId 
                }),
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
        
        // Show conversation header and state
        elements.conversationHeader.style.display = 'flex';
        elements.conversationState.style.display = 'block';
        
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
        elements.welcomeState.style.display = 'block';
        
        // Hide conversation header and state
        elements.conversationHeader.style.display = 'none';
        elements.conversationState.style.display = 'none';
        
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
        messageDiv.className = `dealshub-message ${type}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (type === 'user') {
            messageContent.innerHTML = `<p>${text}</p>`;
        } else {
            messageContent.innerHTML = `<div class="bot-response">${text}</div>`;
        }
        
        messageDiv.appendChild(messageContent);
        elements.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        scrollToBottom();
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
                // Trigger form submission
                if (elements.dealshubForm) {
                    handleMainFormSubmit({ preventDefault: () => {} });
                }
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
     * Add greeting response with suggestions
     */
    function addGreetingResponse(response) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'dealshub-message bot-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
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
        messageContent.innerHTML = html;
        
        messageDiv.appendChild(messageContent);
        elements.chatMessages.appendChild(messageDiv);
        
        // Bind suggestion buttons
        messageDiv.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.dataset.query;
                elements.conversationInput.value = query;
                handleConversationSubmit({ preventDefault: () => {} });
            });
        });
        
        scrollToBottom();
    }

    /**
     * Add offers response with cards
     */
    function addOffersResponse(response) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'dealshub-message bot-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
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
        messageContent.innerHTML = html;
        
        messageDiv.appendChild(messageContent);
        elements.chatMessages.appendChild(messageDiv);
        
        // Bind feedback buttons
        bindOfferFeedbacks(messageDiv);
        
        scrollToBottom();
    }

    /**
     * Create HTML for an offer card
     */
    function createOfferCardHTML(offer) {
        const categories = offer.categories.map(cat => `<span class="offer-category">${cat}</span>`).join('');
        
        return `
            <div class="offer-card" data-offer-id="${offer.offer_id}">
                <a href="${offer.affiliate_url}" target="_blank" class="offer-image-container">
                    <img src="${offer.image_url}" alt="${offer.title}" class="offer-image" 
                         onerror="this.src='/images/placeholder.jpg'">
                    <span class="offer-campaign">${offer.campaign}</span>
                </a>
                <div class="offer-details">
                    <h3 class="offer-title">${offer.title}</h3>
                    ${offer.coupon_code ? `<div class="offer-coupon">Code: ${offer.coupon_code}</div>` : ''}
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
            loadingDiv.className = 'dealshub-message bot-message loading-message';
            loadingDiv.innerHTML = `
                <div class="message-content">
                    <div class="loading-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            `;
            elements.chatMessages.appendChild(loadingDiv);
            scrollToBottom();
            
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
    }

    /**
     * Scroll to bottom of conversation
     */
    function scrollToBottom() {
        setTimeout(() => {
            elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        }, 100);
    }

    // Public API
    return {
        init: init,
        startNewSession: startNewSession
    };
})();
