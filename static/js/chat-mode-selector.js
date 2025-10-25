// Chat Mode Selector - Handles switching between Coupons and Compare modes
class ChatModeSelector {
    constructor() {
        this.currentMode = 'coupons';
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const modeRadios = document.querySelectorAll('input[name="chatMode"]');
        
        modeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.handleModeChange(e.target.value);
            });
        });
    }

    handleModeChange(mode) {
        this.currentMode = mode;

        if (mode === 'coupons') {
            this.enableCouponsMode();
        } else if (mode === 'compare') {
            this.showComingSoonMode();
        }
    }

    enableCouponsMode() {
        // Re-enable search functionality
        const searchInput = document.getElementById('dealshubInput');
        const conversationInput = document.getElementById('conversationInput');
        const form = document.getElementById('dealshubForm');
        const conversationForm = document.getElementById('conversationForm');

        if (searchInput) {
            searchInput.disabled = false;
            searchInput.placeholder = 'Ask about deals, products, brands, or categories...';
            searchInput.style.opacity = '1';
        }

        if (conversationInput) {
            conversationInput.disabled = false;
            conversationInput.placeholder = 'Ask me anything...';
            conversationInput.style.opacity = '1';
        }

        if (form) {
            form.style.opacity = '1';
            form.style.pointerEvents = 'auto';
        }

        if (conversationForm) {
            conversationForm.style.opacity = '1';
            conversationForm.style.pointerEvents = 'auto';
        }

        // Hide coming soon message if it exists
        const comingSoonMsg = document.getElementById('comingSoonMessage');
        if (comingSoonMsg) {
            comingSoonMsg.style.display = 'none';
        }

        // Show welcome section
        const welcomeState = document.getElementById('welcomeState');
        if (welcomeState) {
            welcomeState.style.display = 'flex';
        }
    }

    showComingSoonMode() {
        // Disable search functionality
        const searchInput = document.getElementById('dealshubInput');
        const conversationInput = document.getElementById('conversationInput');
        const form = document.getElementById('dealshubForm');
        const conversationForm = document.getElementById('conversationForm');

        if (searchInput) {
            searchInput.disabled = true;
            searchInput.placeholder = 'Compare feature coming soon...';
            searchInput.style.opacity = '0.5';
        }

        if (conversationInput) {
            conversationInput.disabled = true;
            conversationInput.placeholder = 'Compare feature coming soon...';
            conversationInput.style.opacity = '0.5';
        }

        if (form) {
            form.style.opacity = '0.5';
            form.style.pointerEvents = 'none';
        }

        if (conversationForm) {
            conversationForm.style.opacity = '0.5';
            conversationForm.style.pointerEvents = 'none';
        }

        // Show or create coming soon message
        let comingSoonMsg = document.getElementById('comingSoonMessage');
        
        if (!comingSoonMsg) {
            comingSoonMsg = document.createElement('div');
            comingSoonMsg.id = 'comingSoonMessage';
            comingSoonMsg.className = 'coming-soon-message';
            comingSoonMsg.innerHTML = `
                <div class="coming-soon-content">
                    <div class="coming-soon-icon">
                        <i class="fas fa-rocket"></i>
                    </div>
                    <h2>Compare Feature Coming Soon</h2>
                    <p>We're working hard to bring you the ability to compare prices across multiple platforms like Amazon, Flipkart, and more!</p>
                    <div class="feature-benefits">
                        <div class="benefit">
                            <i class="fas fa-balance-scale"></i>
                            <span>Side-by-side price comparison</span>
                        </div>
                        <div class="benefit">
                            <i class="fas fa-link"></i>
                            <span>Direct links to best deals</span>
                        </div>
                        <div class="benefit">
                            <i class="fas fa-star"></i>
                            <span>Ratings & reviews</span>
                        </div>
                    </div>
                    <p class="coming-soon-message-subtitle">Stay tuned for this exciting feature!</p>
                </div>
            `;

            const welcomeState = document.getElementById('welcomeState');
            if (welcomeState) {
                welcomeState.parentNode.insertBefore(comingSoonMsg, welcomeState.nextSibling);
            }
        }

        // Hide welcome section
        const welcomeState = document.getElementById('welcomeState');
        if (welcomeState) {
            welcomeState.style.display = 'none';
        }

        // Show coming soon message
        comingSoonMsg.style.display = 'flex';
    }

    getCurrentMode() {
        return this.currentMode;
    }
}

// Initialize Chat Mode Selector when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatModeSelector = new ChatModeSelector();
});
