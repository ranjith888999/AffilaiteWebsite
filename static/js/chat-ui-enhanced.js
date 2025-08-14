// Enhanced Chat UI Interactions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize event listeners
    initChatFormListener();
    initSuggestionListeners();
    initActionButtonListeners();
    initVoiceInputButton();
    initScrollHandling();
    
    // Restore chat theme based on user preference
    applyThemeToChatUI();
});

// Apply the current theme to chat UI
function applyThemeToChatUI() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Additional theme-specific adjustments for chat UI
    if (currentTheme === 'dark' || currentTheme === 'night') {
        document.querySelector('.chat-container').classList.add('dark-theme');
    } else {
        document.querySelector('.chat-container').classList.remove('dark-theme');
    }
}

// Handle chat form submission
function initChatFormListener() {
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', function(event) {
            event.preventDefault();
            sendMessage();
        });
    }
}

// Handle suggestion clicks
function initSuggestionListeners() {
    const suggestions = document.querySelectorAll('.chat-suggestion');
    suggestions.forEach(suggestion => {
        suggestion.addEventListener('click', function() {
            const query = this.getAttribute('data-suggestion');
            if (query) {
                document.getElementById('userMessage').value = query;
                sendMessage();
            } else if (this.hasAttribute('onclick')) {
                // For backward compatibility with any remaining onclick attributes
                return;
            }
        });
    });
    
    // Help tags in the info panel
    const helpTags = document.querySelectorAll('.chat-help-tag');
    helpTags.forEach(tag => {
        tag.addEventListener('click', function() {
            const query = this.getAttribute('data-suggestion');
            if (query) {
                document.getElementById('userMessage').value = query;
                sendMessage();
                
                // Hide help info if it's showing
                const helpInfo = document.getElementById('chatHelpInfo');
                if (helpInfo && helpInfo.style.display !== 'none') {
                    helpInfo.style.display = 'none';
                }
            }
        });
    });
}

// Handle action buttons in the header
function initActionButtonListeners() {
    const actionButtons = document.querySelectorAll('.chat-actions button');
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            
            switch(action) {
                case 'maximize':
                    toggleChatMaximize();
                    break;
                case 'clear':
                    clearChat();
                    break;
                case 'help':
                    toggleHelpInfo();
                    break;
            }
        });
    });
}

// Toggle maximize/minimize chat
function toggleChatMaximize() {
    const chatContainer = document.querySelector('.chat-container');
    const maximizeBtn = document.getElementById('maximizeBtn');
    
    chatContainer.classList.toggle('maximized');
    
    if (chatContainer.classList.contains('maximized')) {
        maximizeBtn.innerHTML = '<i class="fas fa-compress"></i>';
        maximizeBtn.title = 'Minimize chat';
    } else {
        maximizeBtn.innerHTML = '<i class="fas fa-expand"></i>';
        maximizeBtn.title = 'Maximize chat';
    }
    
    // Scroll messages to bottom after resize
    scrollToBottom();
}

// Clear chat messages
function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        const messagesContainer = document.getElementById('chatMessages');
        
        // Keep only the welcome message
        const welcomeMessage = messagesContainer.querySelector('.message.bot-message:first-child');
        messagesContainer.innerHTML = '';
        
        if (welcomeMessage) {
            messagesContainer.appendChild(welcomeMessage);
        } else {
            // If no welcome message exists, create a new one
            addWelcomeMessage();
        }
        
        // Also clear session history on the server
        fetch('/api/chat/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
    }
}

// Add welcome message
function addWelcomeMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    const welcomeHtml = `
        <div class="message bot-message animate__animated animate__fadeInUp">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <p>👋 <strong>Welcome to DealsHub!</strong> I'm your personal shopping assistant.</p>
                    <p>I can help you find the best deals across:</p>
                    <ul>
                        <li>🛍️ <strong>Fashion</strong> - Clothing, shoes, accessories</li>
                        <li>🔌 <strong>Electronics</strong> - Gadgets, computers, phones</li>
                        <li>✈️ <strong>Travel</strong> - Hotels, flights, vacation packages</li>
                        <li>🍔 <strong>Food</strong> - Restaurant deals, delivery discounts</li>
                        <li>🏠 <strong>Home</strong> - Furniture, appliances, decor</li>
                    </ul>
                    <p>Just tell me what you're looking for or try one of the suggested questions below!</p>
                    <p><strong>💡 Pro tip:</strong> Try voice input by clicking the microphone icon!</p>
                </div>
                <div class="message-time">Just now</div>
            </div>
        </div>
    `;
    messagesContainer.innerHTML = welcomeHtml;
}

// Toggle help info panel
function toggleHelpInfo() {
    const helpInfo = document.getElementById('chatHelpInfo');
    if (helpInfo) {
        if (helpInfo.style.display === 'none' || getComputedStyle(helpInfo).display === 'none') {
            helpInfo.style.display = 'block';
            helpInfo.classList.add('animate__animated', 'animate__fadeIn');
        } else {
            helpInfo.classList.add('animate__animated', 'animate__fadeOut');
            helpInfo.addEventListener('animationend', () => {
                helpInfo.style.display = 'none';
                helpInfo.classList.remove('animate__animated', 'animate__fadeOut');
            }, { once: true });
        }
    }
}

// Initialize voice input button
function initVoiceInputButton() {
    const voiceButton = document.getElementById('voiceInputBtn');
    if (voiceButton) {
        voiceButton.addEventListener('click', function() {
            startVoiceInput();
        });
    }
    
    // Also add keyboard shortcut (Ctrl+Shift+V)
    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey && event.shiftKey && event.key === 'V') {
            event.preventDefault();
            startVoiceInput();
        }
    });
}

// Format bot response with HTML
function formatBotResponse(text) {
    if (!text) return '<p>I apologize, but I couldn\'t generate a response.</p>';
    
    // Replace newlines with paragraph breaks
    let formatted = text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
    
    // Wrap in paragraph tags if not already wrapped
    if (!formatted.startsWith('<p>')) {
        formatted = '<p>' + formatted;
    }
    if (!formatted.endsWith('</p>')) {
        formatted = formatted + '</p>';
    }
    
    // Format special sections
    // Bold text between ** **
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italics text between * *
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Coupon codes
    formatted = formatted.replace(/COUPON: ([A-Z0-9-_]+)/gi, 'COUPON: <span class="coupon-code" onclick="copyToClipboard(\'$1\')">$1 <i class="fas fa-copy"></i></span>');
    
    // Links
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Highlight deals
    formatted = formatted.replace(/(Deal:)(.*?)(\d+%\s*off|\$\d+\.\d+|\$\d+)/gi, '<span class="deal-highlight">$1$2<strong>$3</strong></span>');
    
    return formatted;
}

// Helper function to copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showTemporaryMessage('Copied to clipboard: ' + text, 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showTemporaryMessage('Failed to copy to clipboard', 'error');
    });
}

// Smooth scrolling for chat messages
function initScrollHandling() {
    const messagesContainer = document.getElementById('chatMessagesContainer');
    if (messagesContainer) {
        // Auto-scroll on new messages
        const observer = new MutationObserver(scrollToBottom);
        observer.observe(messagesContainer, { childList: true, subtree: true });
        
        // Initial scroll to bottom
        scrollToBottom();
    }
}

// Scroll to bottom of messages
function scrollToBottom() {
    const container = document.getElementById('chatMessagesContainer');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// Show typing indicator
function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    const typingIndicator = document.createElement('div');
    typingIndicator.classList.add('typing-indicator');
    typingIndicator.id = 'typingIndicator';
    typingIndicator.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <span>Thinking</span>
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    messagesContainer.appendChild(typingIndicator);
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Show a temporary notification
function showTemporaryMessage(message, type = 'info') {
    const notification = document.createElement('div');
    notification.classList.add('chat-notification', `notification-${type}`);
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Show with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Hide and remove after delay
    setTimeout(() => {
        notification.classList.remove('show');
        notification.addEventListener('transitionend', () => {
            notification.remove();
        }, { once: true });
    }, 3000);
}

// Main function to send messages
async function sendMessage() {
    const userMessageInput = document.getElementById('userMessage');
    const message = userMessageInput.value.trim();
    
    if (message === '') return;
    
    // Store last message for feedback
    window.lastUserMessage = message;
    
    // Display user message
    const chatMessages = document.getElementById('chatMessages');
    const userMessageElement = document.createElement('div');
    userMessageElement.className = 'message user-message animate__animated animate__fadeInUp';
    
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    userMessageElement.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-user"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble">
                <p>${message}</p>
            </div>
            <div class="message-time">${timestamp}</div>
        </div>
    `;
    
    chatMessages.appendChild(userMessageElement);
    
    // Clear input
    userMessageInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Scroll to bottom
    scrollToBottom();
    
    try {
        // Generate a session ID if not already set
        if (!window.sessionId) {
            window.sessionId = 'session_' + Math.random().toString(36).substring(2, 15);
        }
        
        // Send message to server
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: window.sessionId
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        hideTypingIndicator();
        
        // Handle the response regardless of success field
        // since the API might not include a success field
        if (data.response) {
            // Store last bot response for feedback
            window.lastBotResponse = data.response;
            
            // Display bot response
            const botMessageElement = document.createElement('div');
            botMessageElement.className = 'message bot-message animate__animated animate__fadeInUp';
            
            let formattedResponse = formatBotResponse(data.response);
            let feedbackHtml = '';
            
            // Add feedback options if enabled
            if (data.enable_feedback) {
                feedbackHtml = `
                    <div class="message-feedback">
                        <span>Was this helpful?</span>
                        <button class="feedback-btn" data-value="helpful" onclick="sendFeedback('helpful')">
                            <i class="fas fa-thumbs-up"></i>
                        </button>
                        <button class="feedback-btn" data-value="not_helpful" onclick="sendFeedback('not_helpful')">
                            <i class="fas fa-thumbs-down"></i>
                        </button>
                    </div>
                `;
            }
            
            botMessageElement.innerHTML = `
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-bubble">
                        ${formattedResponse}
                    </div>
                    <div class="message-time">${timestamp}</div>
                    ${feedbackHtml}
                </div>
            `;
            
            chatMessages.appendChild(botMessageElement);
            
            // Process and display offers if any
            if (data.offers && data.offers.length > 0) {
                try {
                    displayOffers(data.offers);
                } catch (offerError) {
                    console.error('Error displaying offers:', offerError);
                }
            }
            
            // Handle any campaigns if present
            if (data.campaigns && data.campaigns.length > 0) {
                try {
                    displayCampaigns(data.campaigns);
                } catch (campaignError) {
                    console.error('Error displaying campaigns:', campaignError);
                }
            }
        } else {
            // Display error message
            const errorMessageElement = document.createElement('div');
            errorMessageElement.className = 'message bot-message animate__animated animate__fadeInUp';
            
            // Use the error message from the response if available
            const errorMessage = data.error_message || data.error || 'Sorry, I encountered an error processing your request. Please try again.';
            
            errorMessageElement.innerHTML = `
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-bubble error">
                        <p>${errorMessage}</p>
                    </div>
                    <div class="message-time">${timestamp}</div>
                </div>
            `;
            
            chatMessages.appendChild(errorMessageElement);
            
            // Still display offers if they're available despite the error
            if (data.offers && data.offers.length > 0) {
                try {
                    displayOffers(data.offers);
                } catch (offerError) {
                    console.error('Error displaying offers:', offerError);
                }
            }
        }
        
        // Scroll to bottom after adding new messages
        scrollToBottom();
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Hide typing indicator
        hideTypingIndicator();
        
        // Display error message
        const errorMessageElement = document.createElement('div');
        errorMessageElement.className = 'message bot-message animate__animated animate__fadeInUp';
        
        errorMessageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble error">
                    <p>Sorry, I couldn't connect to the server. Please check your internet connection and try again.</p>
                </div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;
        
        chatMessages.appendChild(errorMessageElement);
        scrollToBottom();
    }
}
