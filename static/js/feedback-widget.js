// Feedback Widget functionality
class FeedbackWidget {
    constructor() {
        this.selectedType = null;
        this.selectedRating = null;
        this.init();
    }

    init() {
        // Create the feedback widget HTML
        this.createWidget();
        // Attach event listeners
        this.attachEventListeners();
    }


    createWidget() {
        // Check if we're on the chat page
        const isOnChatPage = window.location.pathname === '/chat';
        
        // Detect if device is mobile based on viewport width (max-width: 480px)
        // const isMobileDevice = window.innerWidth <= 600;
        
        // // Set margin based on chat page and device type
        // let widgetStyle = '';
        // if (isOnChatPage) {
        //     const margin = isMobileDevice ? '20%' : '6%';
        //     widgetStyle = `style = "margin-bottom:${margin}"`;
        // }
        
        const widgetHTML = `
            <!-- Feedback Floating Button -->
            <div class="feedback-widget">
                <button class="feedback-fab" id="feedbackFab" aria-label="Give Feedback">
                    <i class="fas fa-comment-dots"></i>
                </button>
            </div>

            <!-- Feedback Modal -->
            <div class="feedback-modal" id="feedbackModal">
                <div class="feedback-modal-content">
                    <div class="feedback-modal-header">
                        <h2><i class="fas fa-comments"></i> Share Your Feedback</h2>
                        <button class="feedback-close-btn" id="feedbackCloseBtn">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="feedback-modal-body">
                        <div class="feedback-success-message" id="feedbackSuccessMsg">
                            <i class="fas fa-check-circle"></i> Thank you! Your feedback has been submitted successfully.
                        </div>
                        <div class="feedback-error-message" id="feedbackErrorMsg">
                            <i class="fas fa-exclamation-circle"></i> <span id="feedbackErrorText">Something went wrong. Please try again.</span>
                        </div>

                        <form id="feedbackForm">
                            <!-- Feedback Type -->
                            <div class="feedback-form-group">
                                <label>What type of feedback do you have? <span style="color: red;">*</span></label>
                                <div class="feedback-type-options">
                                    <button type="button" class="feedback-type-btn" data-type="bug">
                                        <i class="fas fa-bug"></i>
                                        <span>Bug</span>
                                    </button>
                                    <button type="button" class="feedback-type-btn" data-type="feature">
                                        <i class="fas fa-lightbulb"></i>
                                        <span>Feature</span>
                                    </button>
                                    <button type="button" class="feedback-type-btn" data-type="general">
                                        <i class="fas fa-comment"></i>
                                        <span>General</span>
                                    </button>
                                    <button type="button" class="feedback-type-btn" data-type="complaint">
                                        <i class="fas fa-exclamation-triangle"></i>
                                        <span>Issue</span>
                                    </button>
                                    <button type="button" class="feedback-type-btn" data-type="appreciation">
                                        <i class="fas fa-heart"></i>
                                        <span>Praise</span>
                                    </button>
                                </div>
                            </div>

                            <!-- Rating -->
                            <div class="feedback-form-group">
                                <label>How would you rate your experience?</label>
                                <div class="rating-stars" id="ratingStars">
                                    <i class="fas fa-star rating-star" data-rating="1"></i>
                                    <i class="fas fa-star rating-star" data-rating="2"></i>
                                    <i class="fas fa-star rating-star" data-rating="3"></i>
                                    <i class="fas fa-star rating-star" data-rating="4"></i>
                                    <i class="fas fa-star rating-star" data-rating="5"></i>
                                </div>
                            </div>

                            <!-- Name (Optional) -->
                            <div class="feedback-form-group">
                                <label for="feedbackName">Your Name (Optional)</label>
                                <input type="text" id="feedbackName" placeholder="Enter your name">
                            </div>

                            <!-- Email (Optional) -->
                            <div class="feedback-form-group">
                                <label for="feedbackEmail">Your Email (Optional)</label>
                                <input type="email" id="feedbackEmail" placeholder="your@email.com">
                            </div>

                            <!-- Message -->
                            <div class="feedback-form-group">
                                <label for="feedbackMessage">Your Feedback <span style="color: red;">*</span></label>
                                <textarea id="feedbackMessage" placeholder="Please share your thoughts, suggestions, or issues you've encountered..." required></textarea>
                            </div>

                            <!-- Submit Button -->
                            <button type="submit" class="feedback-submit-btn" id="feedbackSubmitBtn">
                                <i class="fas fa-paper-plane"></i> Submit Feedback
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // Append to body
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }

    attachEventListeners() {
        const fab = document.getElementById('feedbackFab');
        const modal = document.getElementById('feedbackModal');
        const closeBtn = document.getElementById('feedbackCloseBtn');
        const form = document.getElementById('feedbackForm');
        const typeButtons = document.querySelectorAll('.feedback-type-btn');
        const ratingStars = document.querySelectorAll('.rating-star');

        // Open modal
        fab.addEventListener('click', () => {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        });

        // Close modal
        closeBtn.addEventListener('click', () => this.closeModal());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal();
            }
        });

        // Feedback type selection
        typeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                typeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedType = btn.dataset.type;
            });
        });

        // Rating selection
        ratingStars.forEach((star, index) => {
            star.addEventListener('click', () => {
                this.selectedRating = index + 1;
                ratingStars.forEach((s, i) => {
                    if (i <= index) {
                        s.classList.add('active');
                    } else {
                        s.classList.remove('active');
                    }
                });
            });

            // Hover effect
            star.addEventListener('mouseenter', () => {
                ratingStars.forEach((s, i) => {
                    if (i <= index) {
                        s.style.color = '#ffc107';
                    } else {
                        s.style.color = '#ddd';
                    }
                });
            });
        });

        // Reset star colors on mouse leave
        document.getElementById('ratingStars').addEventListener('mouseleave', () => {
            ratingStars.forEach((s, i) => {
                if (this.selectedRating && i < this.selectedRating) {
                    s.style.color = '#ffc107';
                } else {
                    s.style.color = '#ddd';
                }
            });
        });

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitFeedback();
        });
    }

    closeModal() {
        const modal = document.getElementById('feedbackModal');
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    async submitFeedback() {
        const name = document.getElementById('feedbackName').value.trim();
        const email = document.getElementById('feedbackEmail').value.trim();
        const message = document.getElementById('feedbackMessage').value.trim();
        const submitBtn = document.getElementById('feedbackSubmitBtn');
        const successMsg = document.getElementById('feedbackSuccessMsg');
        const errorMsg = document.getElementById('feedbackErrorMsg');
        const errorText = document.getElementById('feedbackErrorText');

        // Hide previous messages
        successMsg.classList.remove('show');
        errorMsg.classList.remove('show');

        // Validation
        if (!this.selectedType) {
            this.showError('Please select a feedback type');
            return;
        }

        if (!message) {
            this.showError('Please enter your feedback message');
            return;
        }

        // Get browser info
        const browserInfo = this.getBrowserInfo();

        // Prepare data
        const feedbackData = {
            name: name || null,
            email: email || null,
            feedback_type: this.selectedType,
            page_url: window.location.href,
            rating: this.selectedRating || null,
            message: message,
            browser_info: browserInfo
        };

        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

        try {
            const response = await fetch('/api/feedback/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedbackData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Show success message
                successMsg.classList.add('show');
                
                // Reset form
                this.resetForm();

                // Close modal after 2 seconds
                setTimeout(() => {
                    this.closeModal();
                    successMsg.classList.remove('show');
                }, 2000);
            } else {
                this.showError(result.detail || 'Failed to submit feedback. Please try again.');
            }
        } catch (error) {
            console.error('Feedback submission error:', error);
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Feedback';
        }
    }

    showError(message) {
        const errorMsg = document.getElementById('feedbackErrorMsg');
        const errorText = document.getElementById('feedbackErrorText');
        errorText.textContent = message;
        errorMsg.classList.add('show');

        // Hide after 5 seconds
        setTimeout(() => {
            errorMsg.classList.remove('show');
        }, 5000);
    }

    resetForm() {
        document.getElementById('feedbackForm').reset();
        
        // Reset type selection
        document.querySelectorAll('.feedback-type-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        this.selectedType = null;

        // Reset rating
        document.querySelectorAll('.rating-star').forEach(star => {
            star.classList.remove('active');
            star.style.color = '#ddd';
        });
        this.selectedRating = null;
    }

    getBrowserInfo() {
        const ua = navigator.userAgent;
        let browserName = 'Unknown';
        let browserVersion = 'Unknown';

        // Detect browser
        if (ua.indexOf('Firefox') > -1) {
            browserName = 'Firefox';
            browserVersion = ua.match(/Firefox\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.indexOf('Chrome') > -1 && ua.indexOf('Edg') === -1) {
            browserName = 'Chrome';
            browserVersion = ua.match(/Chrome\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.indexOf('Safari') > -1 && ua.indexOf('Chrome') === -1) {
            browserName = 'Safari';
            browserVersion = ua.match(/Version\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.indexOf('Edg') > -1) {
            browserName = 'Edge';
            browserVersion = ua.match(/Edg\/([0-9.]+)/)?.[1] || 'Unknown';
        }

        const os = this.getOS();
        const screenResolution = `${window.screen.width}x${window.screen.height}`;

        return `${browserName} ${browserVersion} on ${os} (${screenResolution})`;
    }

    getOS() {
        const ua = navigator.userAgent;
        if (ua.indexOf('Win') > -1) return 'Windows';
        if (ua.indexOf('Mac') > -1) return 'MacOS';
        if (ua.indexOf('Linux') > -1) return 'Linux';
        if (ua.indexOf('Android') > -1) return 'Android';
        if (ua.indexOf('iOS') > -1) return 'iOS';
        return 'Unknown';
    }
}

// Initialize feedback widget when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new FeedbackWidget();
});
