// Search functionality
function setSearchTerm(term) {
    const searchInput = document.getElementById('searchInput');
    searchInput.value = term;
    searchInput.focus();
    // Trigger the search
    const event = new Event('input', { bubbles: true });
    searchInput.dispatchEvent(event);
}

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
