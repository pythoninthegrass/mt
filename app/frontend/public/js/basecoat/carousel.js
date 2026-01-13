(() => {
  const initCarousel = (carouselComponent) => {
    const slidesContainer = carouselComponent.querySelector('.carousel-slides');
    if (!slidesContainer) return;

    const slides = Array.from(carouselComponent.querySelectorAll('.carousel-item'));
    const prevButton = carouselComponent.querySelector('.carousel-prev');
    const nextButton = carouselComponent.querySelector('.carousel-next');
    const indicators = Array.from(carouselComponent.querySelectorAll('.carousel-indicators button'));

    const loop = carouselComponent.dataset.carouselLoop === 'true';
    const autoplayDelay = parseInt(carouselComponent.dataset.carouselAutoplay, 10);
    const orientation = carouselComponent.dataset.orientation || 'horizontal';

    let currentIndex = 0;
    let autoplayInterval = null;

    const getScrollAmount = () => {
      if (slides.length === 0) return 0;
      const firstSlide = slides[0];
      return orientation === 'vertical'
        ? firstSlide.offsetHeight + parseInt(getComputedStyle(slidesContainer).gap || 0)
        : firstSlide.offsetWidth + parseInt(getComputedStyle(slidesContainer).gap || 0);
    };

    const scrollToIndex = (index) => {
      const scrollAmount = getScrollAmount();
      if (orientation === 'vertical') {
        slidesContainer.scrollTo({ top: scrollAmount * index, behavior: 'smooth' });
      } else {
        slidesContainer.scrollTo({ left: scrollAmount * index, behavior: 'smooth' });
      }
      currentIndex = index;
      updateIndicators();
      updateButtonStates();
    };

    const updateIndicators = () => {
      indicators.forEach((indicator, index) => {
        const isActive = index === currentIndex;
        indicator.setAttribute('aria-current', isActive ? 'true' : 'false');
        indicator.setAttribute('aria-label', `Slide ${index + 1}${isActive ? ' (current)' : ''}`);
      });

      slides.forEach((slide, index) => {
        slide.setAttribute('aria-hidden', index === currentIndex ? 'false' : 'true');
      });
    };

    const updateButtonStates = () => {
      if (!prevButton || !nextButton) return;

      if (loop) {
        prevButton.disabled = false;
        nextButton.disabled = false;
      } else {
        prevButton.disabled = currentIndex === 0;
        nextButton.disabled = currentIndex === slides.length - 1;
      }
    };

    const goToPrevious = () => {
      if (currentIndex > 0) {
        scrollToIndex(currentIndex - 1);
      } else if (loop) {
        scrollToIndex(slides.length - 1);
      }
    };

    const goToNext = () => {
      if (currentIndex < slides.length - 1) {
        scrollToIndex(currentIndex + 1);
      } else if (loop) {
        scrollToIndex(0);
      }
    };

    const startAutoplay = () => {
      if (!autoplayDelay || autoplayDelay <= 0) return;

      autoplayInterval = setInterval(() => {
        goToNext();
      }, autoplayDelay);
    };

    const stopAutoplay = () => {
      if (autoplayInterval) {
        clearInterval(autoplayInterval);
        autoplayInterval = null;
      }
    };

    const detectCurrentSlide = () => {
      const scrollPosition = orientation === 'vertical'
        ? slidesContainer.scrollTop
        : slidesContainer.scrollLeft;
      const scrollAmount = getScrollAmount();
      const newIndex = Math.round(scrollPosition / scrollAmount);

      if (newIndex !== currentIndex && newIndex >= 0 && newIndex < slides.length) {
        currentIndex = newIndex;
        updateIndicators();
        updateButtonStates();
      }
    };

    // Previous/Next button handlers
    if (prevButton) {
      prevButton.addEventListener('click', () => {
        stopAutoplay();
        goToPrevious();
      });
    }

    if (nextButton) {
      nextButton.addEventListener('click', () => {
        stopAutoplay();
        goToNext();
      });
    }

    // Indicator click handlers
    indicators.forEach((indicator, index) => {
      indicator.addEventListener('click', () => {
        stopAutoplay();
        scrollToIndex(index);
      });
    });

    // Keyboard navigation
    carouselComponent.addEventListener('keydown', (event) => {
      const isVertical = orientation === 'vertical';
      const prevKey = isVertical ? 'ArrowUp' : 'ArrowLeft';
      const nextKey = isVertical ? 'ArrowDown' : 'ArrowRight';

      switch (event.key) {
        case prevKey:
          event.preventDefault();
          stopAutoplay();
          goToPrevious();
          break;
        case nextKey:
          event.preventDefault();
          stopAutoplay();
          goToNext();
          break;
        case 'Home':
          event.preventDefault();
          stopAutoplay();
          scrollToIndex(0);
          break;
        case 'End':
          event.preventDefault();
          stopAutoplay();
          scrollToIndex(slides.length - 1);
          break;
      }
    });

    // Detect scroll position changes (for touch/manual scrolling)
    let scrollTimeout;
    slidesContainer.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        detectCurrentSlide();
      }, 100);
    });

    // Pause autoplay on hover or focus
    if (autoplayDelay) {
      carouselComponent.addEventListener('mouseenter', stopAutoplay);
      carouselComponent.addEventListener('mouseleave', startAutoplay);
      carouselComponent.addEventListener('focusin', stopAutoplay);
      carouselComponent.addEventListener('focusout', startAutoplay);
    }

    // Initialize
    updateIndicators();
    updateButtonStates();

    if (autoplayDelay) {
      startAutoplay();
    }

    carouselComponent.dataset.carouselInitialized = true;
    carouselComponent.dispatchEvent(new CustomEvent('basecoat:initialized'));
  };

  if (window.basecoat) {
    window.basecoat.register('carousel', '.carousel:not([data-carousel-initialized])', initCarousel);
  }
})();
