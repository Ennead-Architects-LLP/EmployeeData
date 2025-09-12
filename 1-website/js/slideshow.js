// Background Slideshow Class
class BackgroundSlideshow {
    constructor() {
        this.slides = document.querySelectorAll('.slide');
        this.currentSlide = 0;
        this.slideInterval = 8000; // 8 seconds per slide
        this.interval = null;
        this.isPlaying = true;
        
        this.init();
    }

    init() {
        this.startSlideshow();
        
        // Pause on hover for better user experience
        document.addEventListener('mouseenter', () => {
            if (this.isPlaying) {
                this.pauseSlideshow();
            }
        });
        
        document.addEventListener('mouseleave', () => {
            if (this.isPlaying) {
                this.startSlideshow();
            }
        });
    }

    startSlideshow() {
        this.interval = setInterval(() => {
            this.nextSlide();
        }, this.slideInterval);
    }

    pauseSlideshow() {
        clearInterval(this.interval);
    }

    nextSlide() {
        this.slides[this.currentSlide].classList.remove('active');
        this.currentSlide = (this.currentSlide + 1) % this.slides.length;
        this.slides[this.currentSlide].classList.add('active');
    }
}

// Initialize slideshow when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new BackgroundSlideshow();
});
