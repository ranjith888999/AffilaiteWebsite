// Script to fix section overlapping issues with fixed positioning
document.addEventListener('DOMContentLoaded', function() {
    // Get sections
    const categoriesSection = document.querySelector('.categories-section');
    const featuredOffersSection = document.querySelector('.featured-offers-section');
    // const spacer = document.querySelector('.section-spacer');
    
    if (categoriesSection && featuredOffersSection) {
        // Make sure the spacer exists
        // if (!spacer) {
        //     // Create a spacer element if it doesn't exist
        //     const newSpacer = document.createElement('div');
        //     newSpacer.className = 'section-spacer';
        //     categoriesSection.parentNode.insertBefore(newSpacer, featuredOffersSection);
        // // }
        
        // Calculate the categories section height to ensure proper spacing
        const categoriesHeight = categoriesSection.offsetHeight;
        console.log('Categories section height:', categoriesHeight);
        
        // Apply appropriate spacing based on height
        if (spacer) {
            spacer.style.height = '200px';
        }
        
        // Ensure featured offers section is properly separated
        featuredOffersSection.style.position = 'relative';
        featuredOffersSection.style.zIndex = '1';
        featuredOffersSection.style.marginTop = '50px';
        
        console.log('Applied fixed positioning overlap fix via JavaScript');
    }
    
    // Add scroll event listener to handle any dynamic changes
    window.addEventListener('scroll', function() {
        if (categoriesSection && featuredOffersSection && spacer) {
            const categoriesBottom = categoriesSection.getBoundingClientRect().bottom;
            const featuredTop = featuredOffersSection.getBoundingClientRect().top;
            
            // If they get too close, increase the spacer height
            if (featuredTop - categoriesBottom < 100) {
                spacer.style.height = '250px';
            }
        }
    });
});
