// Search functionality
function setSearchTerm(term) {
    const searchInput = document.getElementById('searchInput');
    searchInput.value = term;
    searchInput.focus();
    // Trigger the search
    const event = new Event('input', { bubbles: true });
    searchInput.dispatchEvent(event);
}

// Clear search functionality
function clearSearch() {
    const searchInput = document.getElementById('searchInput');
    searchInput.value = '';
    searchInput.focus();
    // Trigger the search to show all results
    const event = new Event('input', { bubbles: true });
    searchInput.dispatchEvent(event);
}

// Initialize search functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearch');
    
    // Show/hide clear button based on input content
    function toggleClearButton() {
        if (searchInput.value.length > 0) {
            clearBtn.classList.add('show');
        } else {
            clearBtn.classList.remove('show');
        }
    }
    
    // Add event listeners
    searchInput.addEventListener('input', toggleClearButton);
    searchInput.addEventListener('focus', toggleClearButton);
    searchInput.addEventListener('blur', toggleClearButton);
    
    clearBtn.addEventListener('click', clearSearch);
    
    // Initial state
    toggleClearButton();
});

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
