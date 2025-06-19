document.addEventListener('DOMContentLoaded', function() {
    const slides = [
        {
            image: '/static/images/hero/hero-ski-resort.jpg',
            title: 'Welcome to Alpine Ski Shop',
            subtitle: 'Your premier destination for quality ski equipment'
        },
        {
            image: '/static/images/hero/hero-equipment.jpg',
            title: 'Expert Equipment Selection',
            subtitle: 'Find your perfect match with our professional staff'
        },
        {
            image: '/static/images/hero/hero-skiing.jpg',
            title: 'Prime Locations',
            subtitle: 'Conveniently located near major ski resorts'
        }
    ];

    let currentSlide = 0;
    let slideInterval;
    let isChangingSlide = false;
    let isHovered = false;
    const SLIDE_DURATION = 6000; // 6 seconds between slides
    const FADE_OUT_DURATION = 400; // 400ms for fade out
    const TRANSITION_DURATION = 1000; // 1s for full transition

    // Get DOM elements
    const heroSection = document.querySelector('.hero-section');
    const heroContent = heroSection?.querySelector('.hero-content');
    const ctaButton = heroContent?.querySelector('.cta-button');

    // Safety check for required elements
    if (!heroSection || !heroContent) {
        console.error('Required hero elements not found');
        return;
    }

    // Handle initial CTA button animation
    if (ctaButton) {
        // Start the animation after a small delay
        setTimeout(() => {
            ctaButton.classList.add('animate-in');
            // After animation completes, switch to permanent visible state
            setTimeout(() => {
                ctaButton.classList.remove('animate-in');
                ctaButton.classList.add('visible');
            }, 600); // Match the animation duration
        }, 100);
    }

    function preloadImages() {
        slides.forEach(slide => {
            const img = new Image();
            img.src = slide.image;
        });
    }

    function safelyUpdateContent(slide) {
        try {
            const titleEl = heroContent.querySelector('h1');
            const subtitleEl = heroContent.querySelector('p');
            
            if (titleEl && subtitleEl) {
                titleEl.textContent = slide.title;
                subtitleEl.textContent = slide.subtitle;
            }
            
            heroSection.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('${slide.image}')`;
            return true;
        } catch (error) {
            console.error('Error updating slide content:', error);
            return false;
        }
    }

    function updateSlide() {
        if (isChangingSlide) return;
        isChangingSlide = true;

        // Start fade out
        heroContent.classList.remove('active');
        
        // Wait for content to fade out
        const fadeOutTimer = setTimeout(() => {
            const slide = slides[currentSlide];
            
            // Update content
            if (safelyUpdateContent(slide)) {
                // Add initial-load class only on first load
                if (!heroContent.classList.contains('initial-load')) {
                    heroContent.classList.add('initial-load');
                }
                
                // Trigger fade in
                heroContent.classList.add('active');
            }
            
            // Reset changing flag after transition completes
            const transitionTimer = setTimeout(() => {
                isChangingSlide = false;
                // Restart slideshow if not hovered
                if (!isHovered) {
                    startSlideShow();
                }
            }, TRANSITION_DURATION);

            // Cleanup timer if component unmounts
            return () => clearTimeout(transitionTimer);
        }, FADE_OUT_DURATION);

        // Cleanup timer if component unmounts
        return () => clearTimeout(fadeOutTimer);
    }

    function nextSlide() {
        if (isChangingSlide) return;
        stopSlideShow();
        currentSlide = (currentSlide + 1) % slides.length;
        updateSlide();
    }

    function prevSlide() {
        if (isChangingSlide) return;
        stopSlideShow();
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        updateSlide();
    }

    function startSlideShow() {
        if (slideInterval) clearInterval(slideInterval);
        if (!isHovered) {
            slideInterval = setInterval(nextSlide, SLIDE_DURATION);
        }
    }

    function stopSlideShow() {
        if (slideInterval) {
            clearInterval(slideInterval);
            slideInterval = null;
        }
    }

    // Create and append navigation buttons
    const prevButton = document.createElement('button');
    prevButton.innerHTML = '&#10094;';
    prevButton.className = 'slide-nav prev';
    prevButton.onclick = function(e) {
        e.preventDefault();
        prevSlide();
    };

    const nextButton = document.createElement('button');
    nextButton.innerHTML = '&#10095;';
    nextButton.className = 'slide-nav next';
    nextButton.onclick = function(e) {
        e.preventDefault();
        nextSlide();
    };

    heroSection.appendChild(prevButton);
    heroSection.appendChild(nextButton);

    // Initialize slider
    preloadImages();
    heroContent.classList.add('initial-load');
    heroContent.classList.add('active');
    updateSlide();
    startSlideShow();

    // Handle hover events
    heroSection.addEventListener('mouseenter', () => {
        isHovered = true;
        stopSlideShow();
    });

    heroSection.addEventListener('mouseleave', () => {
        isHovered = false;
        startSlideShow();
    });

    // Handle visibility change
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopSlideShow();
        } else if (!isHovered) {
            startSlideShow();
        }
    });

    // Cleanup on page unload
    window.addEventListener('unload', () => {
        stopSlideShow();
    });
});
