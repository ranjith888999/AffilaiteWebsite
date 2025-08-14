/**
 * Enhanced animations and interactions for the offers page
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add scroll reveal animation to offer cards
    const animateOnScroll = () => {
        const cards = document.querySelectorAll('.offer-card:not(.animated)');
        
        cards.forEach((card, index) => {
            const cardTop = card.getBoundingClientRect().top;
            const cardBottom = card.getBoundingClientRect().bottom;
            const windowHeight = window.innerHeight;
            
            if (cardTop < windowHeight - 100 && cardBottom > 0) {
                // Add a staggered animation delay based on card position
                setTimeout(() => {
                    card.classList.add('animate__animated', 'animate__fadeInUp', 'animated');
                }, index % 4 * 100); // Stagger by columns (assuming 4 cards per row)
            }
        });
    };
    
    // Run on initial load and scroll
    animateOnScroll();
    window.addEventListener('scroll', animateOnScroll);
    
    // Enhanced filter interactions
    const filters = document.querySelectorAll('.filter-group select, .search-box input');
    filters.forEach(filter => {
        filter.addEventListener('focus', function() {
            this.closest('.filter-group, .search-box').classList.add('active');
        });
        
        filter.addEventListener('blur', function() {
            this.closest('.filter-group, .search-box').classList.remove('active');
        });
    });
    
    // Add visual feedback when filters change
    const refreshIndicator = (element) => {
        const parent = element.closest('.filter-group, .search-box');
        parent.classList.add('refreshing');
        setTimeout(() => {
            parent.classList.remove('refreshing');
        }, 500);
    };
    
    // Apply the visual feedback to filter changes
    document.getElementById('categoryFilter').addEventListener('change', function() {
        refreshIndicator(this);
    });
    
    document.getElementById('campaignFilter').addEventListener('change', function() {
        refreshIndicator(this);
    });
    
    document.getElementById('couponFilter').addEventListener('change', function() {
        refreshIndicator(this.closest('label'));
    });
    
    // Enhance the search experience
    const searchInput = document.getElementById('searchInput');
    const searchIcon = searchInput.nextElementSibling;
    
    searchInput.addEventListener('focus', function() {
        searchIcon.classList.add('searching');
    });
    
    searchInput.addEventListener('blur', function() {
        searchIcon.classList.remove('searching');
    });
    
    // Add smooth scroll to top when changing pages
    const scrollToTop = () => {
        const scrollOptions = {
            top: 0,
            behavior: 'smooth'
        };
        window.scrollTo(scrollOptions);
    };
    
    // Expose functions to the global scope that might be called from the main script
    window.enhancedUI = {
        scrollToTop: scrollToTop,
        refreshIndicator: refreshIndicator
    };
});

// Enhance the original offer loading function to add animations
const originalLoadOffers = window.loadOffers;
if (typeof originalLoadOffers === 'function') {
    window.loadOffers = function() {
        const result = originalLoadOffers.apply(this, arguments);
        
        // Add a small delay to ensure DOM is updated
        setTimeout(() => {
            const cards = document.querySelectorAll('.offer-card:not(.animated)');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.classList.add('animate__animated', 'animate__fadeInUp', 'animated');
                }, index % 4 * 100);
            });
        }, 300);
        
        return result;
    };
}

// Enhance the pagination click to add smooth scrolling
document.addEventListener('click', function(e) {
    if (e.target.matches('.pagination-item') || e.target.closest('.pagination-item')) {
        if (window.enhancedUI && typeof window.enhancedUI.scrollToTop === 'function') {
            setTimeout(window.enhancedUI.scrollToTop, 100);
        }
    }
});
