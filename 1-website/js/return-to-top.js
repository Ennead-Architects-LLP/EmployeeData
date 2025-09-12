// Return to Top Button functionality
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Show/hide return to top button based on scroll position
window.addEventListener('scroll', function() {
    const returnToTopButton = document.getElementById('returnToTop');
    if (window.pageYOffset > 300) {
        returnToTopButton.classList.add('show');
    } else {
        returnToTopButton.classList.remove('show');
    }
});
