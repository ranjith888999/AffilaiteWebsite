/**
 * Perplexity-Style Chat Interface
 * Handles the clean, modern chat UI similar to Perplexity Pro
 */

window.PerplexityChat = (function() {
    'use strict';

    // State management
    let state = {
        sessionId: null,
        isLoading: false,
        isWelcomeVisible: true,
        messages: []
    };

    // DOM elements
    let elements = {};

    /**
     * Initialize the chat interface
     */
    function init() {
        cacheElements();
        bindEvents();
        generateSessionId();
        console.log('🚀 Perplexity Chat initialized');
    }

    /**
     * Cache DOM elements for performance
     */
    function cacheElements() {
        elements = {
            form: document.getElementById('perplexityForm'),
            input: document.getElementById('perplexityInput'),
            welcomeState: document.getElementById('welcomeState'),
            messagesContainer: document.getElementById('chatMessages'),
            loadingIndicator: document.getElementById('loadingIndicator'),
            suggestionPills: document.querySelectorAll('.suggestion-pill'),
            voiceBtn: document.getElementById('voiceBtn'),
            main: document.getElementById('perplexityMain')
        };
    }

    /**
     * Bind event listeners
     */
    function bindEvents() {
        // Form submission
        if (elements.form) {
            elements.form.addEventListener('submit', handleSubmit);
        }

        // Input events
        if (elements.input) {
            elements.input.addEventListener('keydown', handleKeyDown);
            elements.input.addEventListener('input', handleInput);
        }

        // Suggestion pills
        elements.suggestionPills.forEach(pill => {
            pill.addEventListener('click', () => {
                const suggestion = pill.dataset.suggestion;
                if (suggestion) {
                    elements.input.value = suggestion;
                    handleSubmit();
                }
            });
        });

        // Voice input (placeholder)
        if (elements.voiceBtn) {
            elements.voiceBtn.addEventListener('click', handleVoiceInput);
        }
    }

    /**
     * Handle form submission
     */
    function handleSubmit(event) {
        if (event) {
            event.preventDefault();
        }

        const message = elements.input.value.trim();
        if (!message || state.isLoading) {
            return;
        }

        // Hide welcome state and show chat
        transitionToChat();

        // Add user message
        addMessage(message, 'user');

        // Clear input
        elements.input.value = '';

        // Show loading and send message
        showLoading();
        sendMessage(message);
    }

    /**
     * Handle keyboard shortcuts
     */
    function handleKeyDown(event) {
        // Submit on Enter (without Shift)
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSubmit();
        }
    }

    /**
     * Handle input changes
     */
    function handleInput(event) {
        // Auto-resize could be implemented here if needed
        const input = event.target;
        
        // Add visual feedback for typing
        if (input.value.length > 0) {
            input.parentElement.classList.add('has-content');
        } else {
            input.parentElement.classList.remove('has-content');
        }
    }

    /**
     * Transition from welcome state to chat interface
     */
    function transitionToChat() {
        if (!state.isWelcomeVisible) return;

        state.isWelcomeVisible = false;
        
        // Fade out welcome state
        elements.welcomeState.style.opacity = '0';
        elements.welcomeState.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            elements.welcomeState.style.display = 'none';
            elements.messagesContainer.style.display = 'block';
            elements.messagesContainer.style.opacity = '1';
        }, 300);
    }

    /**
     * Add a message to the chat
     */
    function addMessage(content, type = 'assistant', timestamp = null) {
        const message = {
            id: Date.now(),
            content,
            type,
            timestamp: timestamp || new Date().toISOString()
        };

        state.messages.push(message);
        renderMessage(message);

        // Scroll to bottom
        setTimeout(() => {
            elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
        }, 100);
    }

    /**
     * Render a message in the chat
     */
    function renderMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `perplexity-message ${message.type}-message`;
        messageEl.dataset.messageId = message.id;

        const avatarIcon = message.type === 'user' 
            ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/></svg>'
            : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

        const timeStr = formatTimestamp(message.timestamp);

        messageEl.innerHTML = `
            <div class="message-avatar">
                <div class="avatar-icon ${message.type}">
                    ${avatarIcon}
                </div>
            </div>
            <div class="message-content">
                <div class="message-text">${formatMessageContent(message.content)}</div>
                <div class="message-timestamp">${timeStr}</div>
            </div>
        `;

        elements.messagesContainer.appendChild(messageEl);
    }

    /**
     * Format message content (handle markdown, links, etc.)
     */
    function formatMessageContent(content) {
        // Basic markdown support
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    /**
     * Format timestamp for display
     */
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return date.toLocaleDateString();
    }

    /**
     * Show loading indicator
     */
    function showLoading() {
        state.isLoading = true;
        elements.loadingIndicator.style.display = 'flex';
    }

    /**
     * Hide loading indicator
     */
    function hideLoading() {
        state.isLoading = false;
        elements.loadingIndicator.style.display = 'none';
    }

    /**
     * Send message to backend
     */
    async function sendMessage(message) {
        try {
            const response = await fetch('/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: state.sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            hideLoading();
            
            if (data.response) {
                addMessage(data.response, 'assistant');
            }

            // Handle offers if present
            if (data.offers && data.offers.length > 0) {
                renderOffers(data.offers);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            hideLoading();
            
            // Show error message
            addMessage(
                'Sorry, I encountered an error while processing your request. Please try again.',
                'assistant'
            );
        }
    }

    /**
     * Render offers in the chat
     */
    function renderOffers(offers) {
        const offersHtml = offers.map(offer => `
            <div class="offer-card">
                <div class="offer-content">
                    <h4>${offer.title}</h4>
                    <p>${offer.description}</p>
                    ${offer.commission ? `<span class="offer-commission">Commission: ${offer.commission}%</span>` : ''}
                    ${offer.category ? `<span class="offer-category">${offer.category}</span>` : ''}
                </div>
                <div class="offer-actions">
                    <a href="${offer.landing_page_url}" target="_blank" class="offer-link">
                        View Deal
                    </a>
                </div>
            </div>
        `).join('');

        addMessage(`Here are some relevant deals I found:<div class="offers-container">${offersHtml}</div>`, 'assistant');
    }

    /**
     * Handle voice input (placeholder)
     */
    function handleVoiceInput() {
        console.log('Voice input clicked - feature coming soon!');
        
        // Placeholder animation
        elements.voiceBtn.style.transform = 'scale(0.95)';
        setTimeout(() => {
            elements.voiceBtn.style.transform = 'scale(1)';
        }, 150);

        // TODO: Implement actual voice recognition
        alert('Voice input feature coming soon!');
    }

    /**
     * Generate unique session ID
     */
    function generateSessionId() {
        state.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Public API
     */
    return {
        init,
        addMessage,
        sendMessage: (msg) => {
            elements.input.value = msg;
            handleSubmit();
        },
        clearChat: () => {
            state.messages = [];
            elements.messagesContainer.innerHTML = '';
            elements.welcomeState.style.display = 'block';
            elements.messagesContainer.style.display = 'none';
            state.isWelcomeVisible = true;
        }
    };
})();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.PerplexityChat.init();
    });
} else {
    window.PerplexityChat.init();
}
