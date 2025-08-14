// Enhanced Image Loading Handler with Local Image Support
(function() {
    'use strict';
    
    // Configuration
    const PLACEHOLDER_URL = '/static/images/placeholder.jpg';
    const DOWNLOADED_IMAGES_BASE = '/static/images/downloaded/';
    const RETRY_ATTEMPTS = 1; // Reduced since we have local images
    const RETRY_DELAY = 500;
    
    // Image loading utilities
    class ImageHandler {
        constructor() {
            this.loadingImages = new Set();
            this.failedImages = new Set();
            this.localImageCache = new Set();
            this.init();
        }
        
        init() {
            // Handle existing images on page load
            document.addEventListener('DOMContentLoaded', () => {
                this.loadLocalImageList();
                this.handleAllImages();
            });
            
            // Handle dynamically added images
            this.observeImageAdditions();
        }
        
        async loadLocalImageList() {
            // Try to get list of available local images
            try {
                const response = await fetch('/api/local-images');
                if (response.ok) {
                    const localImages = await response.json();
                    this.localImageCache = new Set(localImages);
                    console.log(`📷 Loaded ${localImages.length} local images`);
                }
            } catch (e) {
                console.log('📷 Could not load local image list, using standard fallback');
            }
        }
        
        handleAllImages() {
            const images = document.querySelectorAll('.offer-image img, img[data-src]');
            images.forEach(img => this.handleSingleImage(img));
        }
        
        handleSingleImage(img, retryCount = 0) {
            const container = img.closest('.offer-image');
            let originalSrc = img.src || img.dataset.src;
            
            if (!originalSrc || this.loadingImages.has(img)) {
                return;
            }
            
            this.loadingImages.add(img);
            
            // Add loading state
            if (container) {
                container.classList.add('loading');
                container.classList.remove('error');
            }
            
            // Check if this is already a local image path
            if (originalSrc.includes('/static/images/downloaded/') || 
                originalSrc.includes('/static/images/placeholder.jpg')) {
                this.loadDirectly(img, originalSrc, container);
                return;
            }
            
            // For external URLs, try local version first, then original, then placeholder
            this.tryImageSources(img, originalSrc, container, retryCount);
        }
        
        tryImageSources(img, originalSrc, container, retryCount = 0) {
            // 1. Try to find local downloaded version
            // 2. Try original URL (if retry count allows)
            // 3. Fall back to placeholder
            
            const testImg = new Image();
            
            testImg.onload = () => {
                this.onImageLoad(img, testImg.src, container);
            };
            
            testImg.onerror = () => {
                this.onImageError(img, originalSrc, container, retryCount);
            };
            
            // For now, just try the original source (database should already have local paths)
            const cleanSrc = this.cleanImageUrl(originalSrc);
            testImg.src = cleanSrc;
        }
        
        loadDirectly(img, src, container) {
            // For local images, load directly
            const testImg = new Image();
            
            testImg.onload = () => {
                this.onImageLoad(img, src, container);
            };
            
            testImg.onerror = () => {
                // Local image failed, use placeholder
                this.onImageLoad(img, PLACEHOLDER_URL, container);
            };
            
            testImg.src = src;
        }
        
        onImageLoad(img, src, container) {
            this.loadingImages.delete(img);
            
            // Set the actual image source
            img.src = src;
            img.classList.add('loaded');
            
            if (container) {
                container.classList.remove('loading', 'error');
            }
            
            console.log('✅ Image loaded successfully:', src);
        }
        
        onImageError(img, originalSrc, container, retryCount) {
            this.loadingImages.delete(img);
            
            // Try retry with original URL if we haven't tried it yet
            if (retryCount < RETRY_ATTEMPTS && !originalSrc.includes('placeholder.jpg')) {
                console.warn(`⚠️ Image failed, retrying (${retryCount + 1}/${RETRY_ATTEMPTS}):`, originalSrc);
                setTimeout(() => {
                    this.handleSingleImage(img, retryCount + 1);
                }, RETRY_DELAY);
                return;
            }
            
            // Fall back to placeholder
            if (!originalSrc.includes('placeholder.jpg')) {
                console.warn('❌ Image failed, using placeholder:', originalSrc);
                img.src = PLACEHOLDER_URL;
                img.onerror = null; // Prevent infinite loop
                
                if (container) {
                    container.classList.remove('loading');
                }
            } else {
                // Even placeholder failed
                console.error('❌ Placeholder image failed to load');
                this.failedImages.add(img);
                
                if (container) {
                    container.classList.remove('loading');
                    container.classList.add('error');
                }
            }
        }
        
        cleanImageUrl(url) {
            if (!url) return PLACEHOLDER_URL;
            
            // Remove cache-busting parameters that might cause server issues
            return url.split('?')[0];
        }
        
        observeImageAdditions() {
            // Use MutationObserver to handle dynamically added images
            if ('MutationObserver' in window) {
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === 1) { // Element node
                                // Check if the node itself is an image
                                if (node.tagName === 'IMG') {
                                    this.handleSingleImage(node);
                                }
                                // Check for images within the added node
                                const images = node.querySelectorAll?.('img');
                                if (images) {
                                    images.forEach(img => this.handleSingleImage(img));
                                }
                            }
                        });
                    });
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            }
        }
        
        // Public method to manually handle images
        refreshImages() {
            this.handleAllImages();
        }
        
        // Public method to preload placeholder
        preloadPlaceholder() {
            const img = new Image();
            img.src = PLACEHOLDER_URL;
            console.log('📷 Preloading placeholder image');
        }
    }
    
    // Initialize the image handler
    const imageHandler = new ImageHandler();
    
    // Preload placeholder immediately
    imageHandler.preloadPlaceholder();
    
    // Export to global scope for manual use
    window.ImageHandler = ImageHandler;
    window.imageHandler = imageHandler;
    
    // Utility function for templates
    window.handleOfferImages = function() {
        imageHandler.refreshImages();
    };
    
    console.log('🎨 Enhanced image handler with local support initialized');
})();
