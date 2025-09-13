// Background Slideshow Class
class BackgroundSlideshow {
    constructor() {
        this.slides = document.querySelectorAll('.slide');
        this.currentSlide = 0;
        this.slideInterval = 8000; // 8 seconds per slide
        this.interval = null;
        this.isPlaying = true;
        
        // Determine the base path for assets (GitHub Pages vs local)
        this.basePath = this.getBasePath();
        
        this.init();
    }

    getBasePath() {
        const isGitHubPages = window.location.hostname.includes('github.io');
        return isGitHubPages ? '/EmployeeData/' : '';
    }

    init() {
        this.loadSlideshowImages();
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

    loadSlideshowImages() {
        // Use original architectural building images for slideshow
        const slideImages = [
            'https://static.designboom.com/wp-content/uploads/2022/07/new-milwaukee-public-museum-by-ennead-architects-and-kahler-slater-designboom-02.jpg',
            'https://www.archpaper.com/wp-content/uploads/2021/07/01_Shanghai-Astronomy-Museum_Aerial_Photo-by-ArchExists-1-scaled.jpg',
            'https://archinect.gumlet.io/uploads/77/7716e6676923bf8785e6b1c7dbf79493.jpg?auto=compress%2Cformat',
            'https://visualatelier8.com/wp-content/uploads/2019/03/Yangtze-River-Estuary-Chinese-Sturgeon-Nature-Preserve-Ennead-Visual-Atelier-8-Architecture-11.jpg',
            'https://images.adsttc.com/media/images/57c9/46c4/e58e/cebf/2400/0027/medium_jpg/ACLS_NW_Corner.jpg?1472808637'
        ];

        this.slides.forEach((slide, index) => {
            if (slideImages[index]) {
                const imageUrl = slideImages[index];
                
                // Preload image to check if it exists
                const img = new Image();
                img.onload = () => {
                    slide.style.backgroundImage = `url('${imageUrl}')`;
                };
                img.onerror = () => {
                    // Fallback to a subtle gradient if external image fails
                    slide.style.backgroundImage = 'linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%)';
                };
                img.src = imageUrl;
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
