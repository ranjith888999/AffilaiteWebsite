// Theme Management
document.addEventListener('DOMContentLoaded', function() {
    initializeThemeSystem();
});

function initializeThemeSystem() {
    // Get theme buttons
    const lightBtn = document.getElementById('theme-light');
    const darkBtn = document.getElementById('theme-dark');
    const nightBtn = document.getElementById('theme-night');
    const offWhiteBtn = document.getElementById('theme-off-white');
    
    // Check if a theme is saved in localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    } else {
        // Default to light theme if no theme is saved
        applyTheme('light');
    }
    
    // Add event listeners to theme buttons
    if (lightBtn) {
        lightBtn.addEventListener('click', function() {
            applyTheme('light');
        });
    }
    
    if (darkBtn) {
        darkBtn.addEventListener('click', function() {
            applyTheme('dark');
        });
    }
    
    if (nightBtn) {
        nightBtn.addEventListener('click', function() {
            applyTheme('night');
        });
    }
    
    if (offWhiteBtn) {
        offWhiteBtn.addEventListener('click', function() {
            applyTheme('off-white');
        });
    }
    
    // Also check for system preference
    const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");
    
    // Only apply system preference if no theme is saved
    if (!savedTheme) {
        if (prefersDarkScheme.matches) {
            applyTheme('dark');
        } else {
            applyTheme('light');
        }
    }
    
    // Listen for changes in system preference
    prefersDarkScheme.addEventListener('change', function(e) {
        // Only apply if user hasn't explicitly set a theme
        if (!localStorage.getItem('theme')) {
            if (e.matches) {
                applyTheme('dark');
            } else {
                applyTheme('light');
            }
        }
    });
}

function applyTheme(theme) {
    // Remove existing theme
    document.body.removeAttribute('data-theme');
    
    // Add new theme
    if (theme !== 'light') {
        document.body.setAttribute('data-theme', theme);
    }
    
    // Save to localStorage
    localStorage.setItem('theme', theme);
    
    // Update active state on buttons
    updateActiveThemeButton(theme);
    
    // Force a small timeout to ensure all styles are properly applied
    setTimeout(() => {
        // Apply any additional theme-specific styles
        applyAdditionalThemeStyles(theme);
        
        // Dispatch a custom event for components that need to react to theme change
        const event = new CustomEvent('themeChanged', { detail: { theme } });
        document.dispatchEvent(event);
        
        console.log(`Theme changed to: ${theme}`);
    }, 50);
}

function updateActiveThemeButton(theme) {
    // Remove active class from all buttons
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to the selected theme button
    const activeBtn = document.getElementById(`theme-${theme}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
}

function applyAdditionalThemeStyles(theme) {
    // Apply specific overrides based on theme if needed
    if (theme === 'dark') {
        // Ensure navbar colors are correctly applied
        document.querySelectorAll('.nav-link').forEach(link => {
            link.style.color = 'var(--nav-text)';
        });
    } else if (theme === 'night') {
        // Apply specific night mode adjustments
        document.querySelectorAll('.nav-link').forEach(link => {
            link.style.color = 'var(--nav-text)';
        });
    } else {
        // Light theme - reset any specific overrides
        document.querySelectorAll('.nav-link').forEach(link => {
            link.style.color = '';
        });
    }
    
    // Force updating inputs and form elements
    document.querySelectorAll('input, textarea, select').forEach(el => {
        el.style.backgroundColor = 'var(--input-bg)';
        el.style.color = 'var(--input-text)';
        el.style.borderColor = 'var(--input-border-color)';
    });
    
    // Force updating cards
    document.querySelectorAll('.card, .offer-card').forEach(el => {
        el.style.backgroundColor = 'var(--card-bg)';
        el.style.color = 'var(--text-color)';
        el.style.boxShadow = 'var(--card-shadow)';
    });
}
