/**
 * DealsHub AI Chat Interface
 * A stunning, modern chat interface for deal discovery
 */

window.DealsHubChat = (function() {
    'use strict';

    // State management
    let state = {
        sessionId: null,
        isLoading: false,
        isWelcomeVisible: true,
        messages: [],
        currentQuery: ''
    };

    // DOM elements
    let elements = {};

    /**
     * Initialize the DealsHub AI chat interface
     */
    function init() {
        cacheElements();
        bindEvents();
        generateSessionId();
        initializeAnimations();
        console.log('🤖 DealsHub AI Chat initialized');
    }

    /**
     * Cache DOM elements for performance
     */
    function cacheElements() {
        elements = {
            form: document.getElementById('dealshubForm'),
            input: document.getElementById('dealshubInput'),
            welcomeState: document.getElementById('welcomeState'),
            messagesContainer: document.getElementById('chatMessages'),
            loadingIndicator: document.getElementById('loadingIndicator'),
            suggestionPills: document.querySelectorAll('.suggestion-pill'),
            voiceBtn: document.getElementById('voiceBtn'),
            main: document.getElementById('dealshubMain'),
            featureItems: document.querySelectorAll('.feature-item'),
            sendBtn: document.querySelector('.dealshub-btn-send'),
            categoryBtn: document.querySelector('.dealshub-btn-category'),
            trendingBtn: document.querySelector('.dealshub-btn-trending')
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
            elements.input.addEventListener('focus', handleInputFocus);
            elements.input.addEventListener('blur', handleInputBlur);
        }

        // Suggestion pills
        elements.suggestionPills.forEach(pill => {
            pill.addEventListener('click', () => {
                const suggestion = pill.dataset.suggestion;
                if (suggestion) {
                    triggerSuggestion(suggestion);
                }
            });
        });

        // Feature items (clickable)
        elements.featureItems.forEach(item => {
            item.addEventListener('click', handleFeatureClick);
        });

        // Action buttons
        if (elements.voiceBtn) {
            elements.voiceBtn.addEventListener('click', handleVoiceInput);
        }

        if (elements.categoryBtn) {
            elements.categoryBtn.addEventListener('click', () => {
                triggerSuggestion('Show me all categories and popular deals');
            });
        }

        if (elements.trendingBtn) {
            elements.trendingBtn.addEventListener('click', () => {
                triggerSuggestion('What are the trending deals today?');
            });
        }

        // Global keyboard shortcuts
        document.addEventListener('keydown', handleGlobalKeyboard);
    }

    /**
     * Initialize entrance animations
     */
    function initializeAnimations() {
        // Stagger animation for suggestion pills
        setTimeout(() => {
            elements.suggestionPills.forEach((pill, index) => {
                pill.style.animationDelay = `${2.5 + index * 0.1}s`;
                pill.classList.add('animate-in');
            });
        }, 100);
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

        // Add floating effect to send button
        elements.sendBtn.style.transform = 'translateY(-4px) scale(0.95)';
        setTimeout(() => {
            elements.sendBtn.style.transform = '';
        }, 200);

        // Store current query
        state.currentQuery = message;

        // Transition to chat mode
        transitionToChat();

        // Add user message
        addMessage(message, 'user');

        // Clear input with animation
        clearInputWithAnimation();

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

        // Clear input on Escape
        if (event.key === 'Escape') {
            elements.input.value = '';
            elements.input.blur();
        }
    }

    /**
     * Handle global keyboard shortcuts
     */
    function handleGlobalKeyboard(event) {
        // Focus input on '/' key (like GitHub)
        if (event.key === '/' && event.target !== elements.input) {
            event.preventDefault();
            elements.input.focus();
        }

        // Clear chat on Ctrl+K or Cmd+K
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            clearChat();
        }
    }

    /**
     * Handle input changes with visual feedback
     */
    function handleInput(event) {
        const input = event.target;
        const container = input.closest('.dealshub-input-container');
        
        // Add visual feedback for typing
        if (input.value.length > 0) {
            container.classList.add('has-content');
        } else {
            container.classList.remove('has-content');
        }

        // Update send button state
        if (elements.sendBtn) {
            if (input.value.trim().length > 0) {
                elements.sendBtn.style.opacity = '1';
                elements.sendBtn.style.transform = 'scale(1)';
            } else {
                elements.sendBtn.style.opacity = '0.6';
                elements.sendBtn.style.transform = 'scale(0.9)';
            }
        }
    }

    /**
     * Handle input focus
     */
    function handleInputFocus() {
        const container = elements.input.closest('.dealshub-input-container');
        container.style.transform = 'translateY(-2px)';
    }

    /**
     * Handle input blur
     */
    function handleInputBlur() {
        const container = elements.input.closest('.dealshub-input-container');
        if (!container.matches(':focus-within')) {
            container.style.transform = '';
        }
    }

    /**
     * Handle feature item clicks
     */
    function handleFeatureClick(event) {
        const featureText = event.currentTarget.querySelector('span').textContent;
        
        // Add ripple effect
        createRippleEffect(event.currentTarget, event);
        
        // Trigger appropriate suggestion based on feature
        setTimeout(() => {
            switch (featureText) {
                case 'Smart Search':
                    triggerSuggestion('Help me find the best deals for electronics');
                    break;
                case 'Best Deals':
                    triggerSuggestion('Show me today\'s best deals and offers');
                    break;
                case 'Instant Results':
                    triggerSuggestion('Find me deals under $50');
                    break;
                case 'Personalized':
                    triggerSuggestion('Recommend deals based on my preferences');
                    break;
            }
        }, 200);
    }

    /**
     * Create ripple effect for interactive elements
     */
    function createRippleEffect(element, event) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(59, 130, 246, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
            z-index: 1;
        `;

        element.style.position = 'relative';
        element.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    /**
     * Trigger a suggestion with animation
     */
    function triggerSuggestion(suggestion) {
        elements.input.value = suggestion;
        
        // Add typing effect
        elements.input.style.transform = 'scale(1.02)';
        setTimeout(() => {
            elements.input.style.transform = '';
            handleSubmit();
        }, 150);
    }

    /**
     * Clear input with smooth animation
     */
    function clearInputWithAnimation() {
        elements.input.style.transform = 'scale(0.98)';
        elements.input.style.opacity = '0.7';
        
        setTimeout(() => {
            elements.input.value = '';
            elements.input.style.transform = '';
            elements.input.style.opacity = '';
        }, 200);
    }

    /**
     * Transition from welcome state to chat interface
     */
    function transitionToChat() {
        if (!state.isWelcomeVisible) return;

        state.isWelcomeVisible = false;
        
        // Animate welcome state out
        elements.welcomeState.style.transform = 'translateY(-30px) scale(0.95)';
        elements.welcomeState.style.opacity = '0';
        
        setTimeout(() => {
            elements.welcomeState.style.display = 'none';
            elements.messagesContainer.style.display = 'block';
            elements.messagesContainer.style.opacity = '0';
            elements.messagesContainer.style.transform = 'translateY(20px)';
            
            // Animate messages in
            setTimeout(() => {
                elements.messagesContainer.style.opacity = '1';
                elements.messagesContainer.style.transform = 'translateY(0)';
            }, 50);
        }, 300);
    }

    /**
     * Add a message to the chat with beautiful animations
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

        // Scroll to bottom with smooth animation
        setTimeout(() => {
            elements.messagesContainer.scrollTo({
                top: elements.messagesContainer.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }

    /**
     * Render a message with stunning animations
     */
    function renderMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `dealshub-message ${message.type}-message`;
        messageEl.dataset.messageId = message.id;

        const avatarIcon = message.type === 'user' 
            ? '<i class="fas fa-user"></i>'
            : '<i class="fas fa-percentage"></i>';

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

        // Add entrance animation
        messageEl.style.opacity = '0';
        messageEl.style.transform = 'translateY(20px)';
        
        elements.messagesContainer.appendChild(messageEl);

        // Trigger entrance animation
        setTimeout(() => {
            messageEl.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
            messageEl.style.opacity = '1';
            messageEl.style.transform = 'translateY(0)';
        }, 50);
    }

    /**
     * Format message content (handle markdown, links, etc.)
     */
    function formatMessageContent(content) {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code style="background: var(--dealshub-surface); padding: 2px 6px; border-radius: 4px; font-size: 0.9em;">$1</code>')
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
     * Show loading indicator with animation
     */
    function showLoading() {
        state.isLoading = true;
        elements.loadingIndicator.style.display = 'flex';
        elements.loadingIndicator.style.opacity = '0';
        elements.loadingIndicator.style.transform = 'scale(0.8)';
        
        setTimeout(() => {
            elements.loadingIndicator.style.transition = 'all 0.3s ease';
            elements.loadingIndicator.style.opacity = '1';
            elements.loadingIndicator.style.transform = 'scale(1)';
        }, 50);
    }

    /**
     * Hide loading indicator with animation
     */
    function hideLoading() {
        state.isLoading = false;
        elements.loadingIndicator.style.opacity = '0';
        elements.loadingIndicator.style.transform = 'scale(0.8)';
        
        setTimeout(() => {
            elements.loadingIndicator.style.display = 'none';
        }, 300);
    }

    /**
     * Send message to backend with error handling
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
            
            // Show beautiful error message
            addMessage(
                '🔥 Oops! I encountered an issue while searching for deals. Please try again or rephrase your query.',
                'assistant'
            );
        }
    }

    /**
     * Render offers with stunning cards
     */
    function renderOffers(offers) {
        const offersHtml = offers.map(offer => `
            <div class="offer-card" style="animation: fadeInUp 0.5s ease-out forwards;">
                <div class="offer-content">
                    <h4>${offer.title}</h4>
                    <p>${offer.description}</p>
                    <div class="offer-meta">
                        ${offer.commission ? `<span class="offer-commission"><i class="fas fa-percentage"></i> ${offer.commission}%</span>` : ''}
                        ${offer.category ? `<span class="offer-category"><i class="fas fa-tag"></i> ${offer.category}</span>` : ''}
                    </div>
                </div>
                <div class="offer-actions">
                    <a href="${offer.landing_page_url}" target="_blank" class="offer-link">
                        <span>View Deal</span>
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </div>
            </div>
        `).join('');

        addMessage(`🎯 Here are some amazing deals I found for you:<div class="offers-container">${offersHtml}</div>`, 'assistant');
    }

    /**
     * Handle voice input (with browser speech recognition)
     */
    function handleVoiceInput() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            showNotification('Voice recognition is not supported in your browser.', 'warning');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        // Visual feedback
        elements.voiceBtn.style.animation = 'pulse 1s infinite';
        elements.voiceBtn.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';

        recognition.onstart = () => {
            showNotification('🎤 Listening... Speak now!', 'info');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            elements.input.value = transcript;
            elements.input.focus();
            showNotification('✨ Voice input captured!', 'success');
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            showNotification('❌ Voice recognition failed. Please try again.', 'error');
        };

        recognition.onend = () => {
            elements.voiceBtn.style.animation = '';
            elements.voiceBtn.style.background = '';
        };

        recognition.start();
    }

    /**
     * Show beautiful notifications
     */
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `dealshub-notification ${type}`;
        notification.textContent = message;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--dealshub-surface);
            border: 1px solid var(--dealshub-border);
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: var(--dealshub-shadow-lg);
            z-index: 10000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 500;
            color: var(--dealshub-text);
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Animate out and remove
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    /**
     * Clear chat with confirmation
     */
    function clearChat() {
        if (state.messages.length === 0) return;

        if (confirm('Are you sure you want to clear the chat?')) {
            state.messages = [];
            elements.messagesContainer.innerHTML = '';
            elements.welcomeState.style.display = 'block';
            elements.messagesContainer.style.display = 'none';
            state.isWelcomeVisible = true;
            
            // Reset welcome state animation
            elements.welcomeState.style.opacity = '1';
            elements.welcomeState.style.transform = '';
            
            showNotification('Chat cleared successfully!', 'success');
        }
    }

    /**
     * Generate unique session ID
     */
    function generateSessionId() {
        state.sessionId = 'dealshub_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
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
        clearChat,
        triggerSuggestion
    };
})();

// CSS for ripple animation
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .animate-in {
        opacity: 0;
        animation: fadeInUp 0.5s ease-out forwards;
    }
`;
document.head.appendChild(rippleStyle);

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.DealsHubChat.init();
    });
} else {
    window.DealsHubChat.init();
}
