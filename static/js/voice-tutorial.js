/**
 * Voice-to-Text Feature Tutorial
 * Shows a step-by-step guide for the first-time users
 */

document.addEventListener('DOMContentLoaded', function() 
    {
    // Only show tutorial if user hasn't seen it before
    if (!localStorage.getItem('voice_tutorial_seen')) {
        // Wait a bit to let the page load fully
        setTimeout(showVoiceTutorial, 1500);
    }
});

function showVoiceTutorial() {
    // Check if we're on the chat page
    const chatContainer = document.querySelector('.chat-container');
    if (!chatContainer) return;
    
    // Create tutorial overlay
    const tutorialOverlay = document.createElement('div');
    // tutorialOverlay.className = 'voice-tutorial-overlay';
    
    // Tutorial content
    tutorialOverlay.innerHTML = `
        <div class="voice-tutorial-container">
            <div class="voice-tutorial-header">
                <h2>New Feature: Voice Input!</h2>
                <button class="close-tutorial-btn" id="closeTutorialBtn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="voice-tutorial-content">
                <div class="tutorial-step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <h3>Click the microphone icon</h3>
                        <p>Find the microphone icon in the chat input area and click it to start voice input.</p>
                        <div class="step-image">
                            <i class="fas fa-microphone"></i>
                        </div>
                    </div>
                </div>
                <div class="tutorial-step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <h3>Start speaking</h3>
                        <p>When the microphone turns red and pulses, start speaking clearly.</p>
                        <div class="step-image">
                            <i class="fas fa-microphone" style="color: #e74c3c;"></i>
                        </div>
                    </div>
                </div>
                <div class="tutorial-step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <h3>Automatic sending</h3>
                        <p>When you finish speaking and pause, your message will be sent automatically!</p>
                        <div class="step-image">
                            <i class="fas fa-paper-plane"></i>
                        </div>
                    </div>
                </div>
                <div class="tutorial-keyboard">
                    <h3>Keyboard Shortcut</h3>
                    <div class="keyboard-shortcut">
                        <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd>
                    </div>
                    <p>Press this shortcut when the chat input is focused to toggle voice input.</p>
                </div>
            </div>
            <div class="voice-tutorial-footer">
                <button class="tutorial-btn" id="gotItBtn">Got it!</button>
                <button class="tutorial-btn tutorial-btn-secondary" id="tryNowBtn">Try it now</button>
            </div>
        </div>
    `;
    
    // Add to body
    document.body.appendChild(tutorialOverlay);
    
    // Add event listeners
    document.getElementById('closeTutorialBtn').addEventListener('click', closeTutorial);
    document.getElementById('gotItBtn').addEventListener('click', closeTutorial);
    document.getElementById('tryNowBtn').addEventListener('click', function() {
        closeTutorial();
        // Start voice input
        if (typeof startVoiceInput === 'function') {
            setTimeout(startVoiceInput, 300);
        }
    });
    
    // Mark as seen
    localStorage.setItem('voice_tutorial_seen', 'true');
}

function closeTutorial() {
    // const tutorialOverlay = document.querySelector('.voice-tutorial-overlay');
    // if (tutorialOverlay) {
    //     tutorialOverlay.classList.add('closing');
    //     setTimeout(() => {
    //         tutorialOverlay.remove();
    //     }, 300);
    // }
}
