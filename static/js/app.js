
        // Function to toggle project expansion
        function toggleProjects(projectId) {
            const projectList = document.getElementById(projectId);
            const expandIcon = document.getElementById('icon_' + projectId);
            
            if (projectList.style.display === 'none') {
                projectList.style.display = 'block';
                expandIcon.classList.add('expanded');
            } else {
                projectList.style.display = 'none';
                expandIcon.classList.remove('expanded');
            }
        }

        // Function to set search term from suggestions
        function setSearchTerm(term) {
            const searchInput = document.getElementById('searchInput');
            searchInput.value = term;
            searchInput.focus();
            // Trigger the search
            const event = new Event('input', { bubbles: true });
            searchInput.dispatchEvent(event);
        }

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

        document.addEventListener('DOMContentLoaded', function() {
            // Initialize background slideshow
            new BackgroundSlideshow();
            
            const searchInput = document.getElementById('searchInput');
            const clearAllButton = document.getElementById('clearAllFilters');
            const departmentFilter = document.getElementById('departmentFilter');
            const membershipFilter = document.getElementById('membershipFilter');
            const officeLocationFilter = document.getElementById('officeLocationFilter');
            const sortBy = document.getElementById('sortBy');
            const employeeCards = document.getElementById('employeeCards');
            const resultsCount = document.getElementById('resultsCount');
            
            let allCards = Array.from(document.querySelectorAll('.employee-card'));
            
            function filterAndSearch() {
                const searchTerm = searchInput.value.toLowerCase();
                const selectedDepartment = departmentFilter.value;
                const selectedMembership = membershipFilter.value;
                const selectedOfficeLocation = officeLocationFilter.value;
                const sortOption = sortBy.value;
                
                let filteredCards = allCards.filter(card => {
                    const searchableText = card.getAttribute('data-searchable').toLowerCase();
                    const department = card.getAttribute('data-department');
                    const memberships = card.getAttribute('data-memberships').toLowerCase();
                    const officeLocation = card.getAttribute('data-office-location');
                    
                    const matchesSearch = searchableText.includes(searchTerm);
                    const matchesDepartment = !selectedDepartment || department === selectedDepartment;
                    const matchesMembership = !selectedMembership || memberships.includes(selectedMembership.toLowerCase());
                    const matchesOfficeLocation = !selectedOfficeLocation || officeLocation === selectedOfficeLocation;
                    
                    return matchesSearch && matchesDepartment && matchesMembership && matchesOfficeLocation;
                });
                
                // Sort cards
                filteredCards.sort((a, b) => {
                    switch(sortOption) {
                        case 'name':
                            return a.querySelector('.employee-name').textContent.localeCompare(b.querySelector('.employee-name').textContent);
                        case 'position':
                            return a.querySelector('.employee-position').textContent.localeCompare(b.querySelector('.employee-position').textContent);
                        case 'years':
                            const yearsA = parseInt(a.querySelector('.years')?.textContent.match(/\d+/)?.[0] || '0');
                            const yearsB = parseInt(b.querySelector('.years')?.textContent.match(/\d+/)?.[0] || '0');
                            return yearsB - yearsA;
                        case 'department':
                            const deptA = a.getAttribute('data-department') || '';
                            const deptB = b.getAttribute('data-department') || '';
                            return deptA.localeCompare(deptB);
                        default:
                            return 0;
                    }
                });
                
                // Update display
                allCards.forEach(card => {
                    if (filteredCards.includes(card)) {
                        card.classList.remove('hidden');
                        card.classList.add('fade-in');
                    } else {
                        card.classList.add('hidden');
                        card.classList.remove('fade-in');
                    }
                });
                
                // Update results count
                resultsCount.textContent = `${filteredCards.length} employee${filteredCards.length !== 1 ? 's' : ''} found`;
            }
            
            // Event listeners
            searchInput.addEventListener('input', filterAndSearch);
            
            clearAllButton.addEventListener('click', function() {
                searchInput.value = '';
                departmentFilter.value = '';
                membershipFilter.value = '';
                officeLocationFilter.value = '';
                sortBy.value = 'name';
                filterAndSearch();
            });
            
            departmentFilter.addEventListener('change', filterAndSearch);
            membershipFilter.addEventListener('change', filterAndSearch);
            officeLocationFilter.addEventListener('change', filterAndSearch);
            sortBy.addEventListener('change', filterAndSearch);
            
            // Initial filter
            filterAndSearch();
            
            // Return to Top Button functionality
            const returnToTopButton = document.getElementById('returnToTop');
            
            // Show/hide button based on scroll position
            window.addEventListener('scroll', function() {
                if (window.pageYOffset > 300) {
                    returnToTopButton.classList.add('show');
                } else {
                    returnToTopButton.classList.remove('show');
                }
            });
        });
        
        // Function to scroll to top
        function scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
        