// Authentication management
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    async init() {
        await this.checkAuthStatus();
        this.updateNavigation();
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/auth/user');
            const data = await response.json();
            
            if (data.authenticated) {
                this.currentUser = data.user;
            } else {
                this.currentUser = null;
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
            this.currentUser = null;
        }
    }

    updateNavigation() {
        const navAuth = document.getElementById('navAuth');
        
        if (this.currentUser) {
            // User is logged in
            navAuth.innerHTML = `
                <div class="user-menu">
                    <div class="user-avatar" onclick="toggleUserMenu()">
                        <img src="${this.currentUser.picture || '/static/images/default-avatar.svg'}" 
                             alt="${this.currentUser.name}" 
                             onerror="this.src='/static/images/default-avatar.svg'">
                        <span>${this.currentUser.name}</span>
                        <i class="fas fa-chevron-down"></i>
                    </div>
                    <div class="user-dropdown" id="userDropdown">
                        <div class="user-info">
                            <img src="${this.currentUser.picture || '/static/images/default-avatar.svg'}" 
                                 alt="${this.currentUser.name}"
                                 onerror="this.src='/static/images/default-avatar.svg'">
                            <div>
                                <div class="user-name">${this.currentUser.name}</div>
                                <div class="user-email">${this.currentUser.email}</div>
                            </div>
                        </div>
                        <div class="dropdown-divider"></div>
                        <a href="/profile" class="dropdown-item">
                            <i class="fas fa-user"></i> Profile
                        </a>
                        <a href="/admin/feedback" class="dropdown-item">
                            <i class="fas fa-chart-line"></i> Analytics
                        </a>
                        <div class="dropdown-divider"></div>
                        <a href="/auth/logout" class="dropdown-item logout">
                            <i class="fas fa-sign-out-alt"></i> Logout
                        </a>
                    </div>
                </div>
            `;
        } else {
            // User is not logged in - show beautiful Google sign-in button
            navAuth.innerHTML = `
                <div class="auth-buttons">
                    <button onclick="authManager.signInWithGoogle()" class="google-signin-btn">
                        <svg class="google-icon" viewBox="0 0 24 24">
                            <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        <span>Sign in with Google</span>
                    </button>
                </div>
            `;
        }
    }

    isAuthenticated() {
        return this.currentUser !== null;
    }

    getUser() {
        return this.currentUser;
    }

    // Fast Google sign-in with immediate feedback
    signInWithGoogle() {
        // Provide immediate visual feedback
        const button = document.querySelector('.google-signin-btn');
        if (button) {
            button.style.opacity = '0.7';
            button.style.transform = 'scale(0.98)';
            button.innerHTML = `
                <svg class="google-icon" viewBox="0 0 24 24" style="animation: spin 1s linear infinite;">
                    <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span>Redirecting...</span>
            `;
        }
        
        // Immediate redirect without any delays
        window.location.href = '/auth/login';
    }
}

// Toggle user menu dropdown
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('show');
}

// Show Google Sign-In popup (mimics Google's account picker)
function showGoogleSignInPopup() {
    // Create popup overlay
    const overlay = document.createElement('div');
    overlay.className = 'google-signin-overlay';
    overlay.innerHTML = `
        <div class="google-signin-popup">
            <div class="popup-header">
                <img src="https://accounts.google.com/ui/favicon.ico" alt="Google" class="google-icon">
                <h2>Sign in</h2>
                <button class="close-popup" onclick="closeGoogleSignInPopup()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="popup-content">
                <div class="signin-option" onclick="redirectToGoogleAuth()">
                    <div class="account-info">
                        <div class="account-avatar">
                            <i class="fas fa-user"></i>
                        </div>
                        <div class="account-details">
                            <div class="account-text">Use another account</div>
                            <div class="account-subtext">to continue to DealsHub</div>
                        </div>
                    </div>
                    <i class="fas fa-chevron-right"></i>
                </div>
                <div class="signin-divider"></div>
                <div class="signin-footer">
                    <p>To continue, Google will share your name, email address, and profile picture with DealsHub.</p>
                    <div class="footer-links">
                        <a href="https://policies.google.com/privacy" target="_blank">Privacy Policy</a>
                        <a href="https://policies.google.com/terms" target="_blank">Terms of Service</a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Add click outside to close
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            closeGoogleSignInPopup();
        }
    });
}

// Close Google Sign-In popup
function closeGoogleSignInPopup() {
    const overlay = document.querySelector('.google-signin-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Redirect to Google OAuth with account selection
function redirectToGoogleAuth() {
    window.location.href = '/auth/login';
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const userMenu = document.querySelector('.user-menu');
    const dropdown = document.getElementById('userDropdown');
    
    if (dropdown && !userMenu.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.authManager = new AuthManager();
});

// Export for use in other scripts
window.AuthManager = AuthManager;
