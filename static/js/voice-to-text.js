/**
 * Voice to Text functionality for Chat
 * Enhances the chat experience with speech recognition
 */

let recognition;
let isListening = false;
let voiceInputTimeout;
const LISTENING_TIMEOUT = 10000; // 10 seconds timeout

// Initialize speech recognition
function initializeSpeechRecognition() {
    // Check browser support
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.warn('Speech recognition not supported in this browser');
        
        // Hide the voice input button if not supported
        const voiceInputBtn = document.getElementById('voiceInputBtn');
        if (voiceInputBtn) {
            voiceInputBtn.style.display = 'none';
        }
        return;
    }

    // Create speech recognition instance
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    
    // Configure recognition
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US'; // Default language
    
    // Handle results
    recognition.onresult = function(event) {
        const transcript = Array.from(event.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('');
        
        // Update input field with transcript
        const userMessageInput = document.getElementById('userMessage');
        if (userMessageInput) {
            userMessageInput.value = transcript;
            
            // Visual feedback to show processing
            userMessageInput.classList.add('voice-processing');
            setTimeout(() => {
                userMessageInput.classList.remove('voice-processing');
            }, 300);
        }
    };
    
    // Handle end of speech
    recognition.onend = function() {
        stopListening();
        clearTimeout(voiceInputTimeout);
        
        // If the transcript is ready, automatically send the message
        const userMessageInput = document.getElementById('userMessage');
        if (userMessageInput && userMessageInput.value.trim().length > 0) {
            // Optional: Small delay before sending for better UX
            setTimeout(() => {
                // Get the existing sendMessage function from the chat page
                if (typeof sendMessage === 'function') {
                    sendMessage();
                }
            }, 500);
        }
    };
    
    // Handle errors
    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        stopListening();
        clearTimeout(voiceInputTimeout);
        
        // Show error notification
        showNotification('Speech recognition error: ' + event.error, 'error');
    };
}

// Start listening for voice input
function startVoiceInput() {
    if (isListening) {
        stopListening();
        return;
    }
    
    // Initialize if not already done
    if (!recognition) {
        initializeSpeechRecognition();
        
        // Check if initialization failed
        if (!recognition) return;
    }
    
    try {
        recognition.start();
        isListening = true;
        
        // Update UI to show listening state
        const voiceInputBtn = document.getElementById('voiceInputBtn');
        if (voiceInputBtn) {
            voiceInputBtn.classList.add('listening');
            voiceInputBtn.querySelector('i').className = 'fas fa-stop';
            voiceInputBtn.setAttribute('title', 'Stop voice input');
        }
        
        // Show listening notification
        showNotification('Listening... Speak now', 'info');
        
        // Set timeout to automatically stop if no speech detected
        clearTimeout(voiceInputTimeout);
        voiceInputTimeout = setTimeout(() => {
            if (isListening) {
                stopListening();
                showNotification('Listening timeout. Please try again.', 'info');
            }
        }, LISTENING_TIMEOUT);
        
    } catch (error) {
        console.error('Error starting speech recognition:', error);
        showNotification('Could not start voice input', 'error');
    }
}

// Stop listening for voice input
function stopListening() {
    if (!isListening) return;
    
    try {
        recognition.stop();
    } catch (error) {
        console.error('Error stopping speech recognition:', error);
    }
    
    isListening = false;
    
    // Update UI to show stopped state
    const voiceInputBtn = document.getElementById('voiceInputBtn');
    if (voiceInputBtn) {
        voiceInputBtn.classList.remove('listening');
        voiceInputBtn.querySelector('i').className = 'fas fa-microphone';
        voiceInputBtn.setAttribute('title', 'Voice input');
    }
}

// Helper function to show notifications
function showNotification(message, type = 'info') {
    // Check if notification container exists, create if not
    let notificationContainer = document.querySelector('.notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.className = 'notification-container';
        document.body.appendChild(notificationContainer);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add to container
    notificationContainer.appendChild(notification);
    
    // Remove after timeout
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize speech recognition
    initializeSpeechRecognition();
    
    // Add event listener to voice input button
    const voiceInputBtn = document.getElementById('voiceInputBtn');
    if (voiceInputBtn) {
        voiceInputBtn.addEventListener('click', startVoiceInput);
    }
    
    // Support for keyboard shortcut to activate voice input
    document.addEventListener('keydown', function(event) {
        // Only activate when in chat page and input is focused
        const userMessageInput = document.getElementById('userMessage');
        if (userMessageInput && document.activeElement === userMessageInput) {
            // Ctrl+Shift+V to toggle voice input
            if (event.ctrlKey && event.shiftKey && event.key === 'V') {
                event.preventDefault();
                startVoiceInput();
            }
        }
    });
});
