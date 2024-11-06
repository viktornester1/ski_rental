document.addEventListener('DOMContentLoaded', function() {
    const slides = [
        {
            image: '/static/images/hero/hero-ski-resort.jpg',
            title: 'Welcome to Alpine Ski Rental',
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
    let isChangingSlide = false; // Flag to prevent rapid clicks
    const heroSection = document.querySelector('.hero-section');

    function updateSlide() {
        const slide = slides[currentSlide];
        heroSection.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('${slide.image}')`;
        heroSection.querySelector('h1').textContent = slide.title;
        heroSection.querySelector('p').textContent = slide.subtitle;
    }

    function nextSlide() {
        if (isChangingSlide) return; // Prevent triggering while changing
        isChangingSlide = true;
        currentSlide = (currentSlide + 1) % slides.length;
        updateSlide();
        setTimeout(() => isChangingSlide = false, 500); // Allow next click after a delay
    }

    function prevSlide() {
        if (isChangingSlide) return; // Prevent triggering while changing
        isChangingSlide = true;
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        updateSlide();
        setTimeout(() => isChangingSlide = false, 500); // Allow previous click after a delay
    }

    // Auto-slide functionality
    function startSlideShow() {
        if (slideInterval) clearInterval(slideInterval);  // Ensure no interval is already running
        slideInterval = setInterval(nextSlide, 5000);  // Start interval for auto-sliding
    }

    function stopSlideShow() {
        clearInterval(slideInterval);  // Stop auto-sliding
    }

    // Create and append navigation buttons
    const prevButton = document.createElement('button');
    prevButton.innerHTML = '&#10094;';
    prevButton.className = 'slide-nav prev';
    prevButton.onclick = function() {
        stopSlideShow();  // Stop auto-sliding
        prevSlide();
        startSlideShow(); // Restart the timer
    };

    const nextButton = document.createElement('button');
    nextButton.innerHTML = '&#10095;';
    nextButton.className = 'slide-nav next';
    nextButton.onclick = function() {
        stopSlideShow();  // Stop auto-sliding
        nextSlide();
        startSlideShow(); // Restart the timer
    };

    heroSection.appendChild(prevButton);
    heroSection.appendChild(nextButton);

    // Start the automatic slideshow
    updateSlide();  // Ensure the first slide is displayed immediately
    startSlideShow(); // This line will ensure the slideshow starts on page load

    // Optional: Pause slideshow on hover
    heroSection.addEventListener('mouseenter', stopSlideShow);
    heroSection.addEventListener('mouseleave', startSlideShow);
});
