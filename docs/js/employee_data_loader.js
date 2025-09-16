// Individual Employee Data Loader
// Loads employee data from individual JSON files instead of a big collected JSON

// Global variables
let allEmployees = [];
let filteredEmployees = [];
// Computer data is now embedded in individual employee data

// Determine the base path for assets (GitHub Pages vs local)
function getBasePath() {
    const isGitHubPages = window.location.hostname.includes('github.io');
    if (isGitHubPages) {
        // Extract repository name from the current path
        const pathParts = window.location.pathname.split('/').filter(part => part);
        const repoName = pathParts[0]; // First part after the domain
        
        // Check if we're in a subdirectory (like docs)
        if (pathParts.length > 1 && pathParts[1] === 'docs') {
            return `/${repoName}/docs/`;
        }
        return `/${repoName}/`;
    }
    return '';
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Only use merged employees.json; no fallbacks
        const mergedLoaded = await tryLoadMergedEmployees();
        if (!mergedLoaded) {
            showError('Data not found');
            return;
        }

        // Initialize UI (handled by ui-manager.js)
        if (typeof initializeUI === 'function') {
            initializeUI();
        }

        // Hide loading indicator
        document.getElementById('loadingIndicator').style.display = 'none';

    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Data not found');
    }
}

// Deprecated: individual loading and fallbacks removed by policy

async function tryLoadMergedEmployees() {
    const basePath = getBasePath();
    try {
        const url = `${basePath}docs/assets/employees.json`;
        console.log('Trying merged employees file:', url);
        const response = await fetch(url, { signal: AbortSignal.timeout(10000) });
        if (response.ok) {
            const data = await response.json();
            if (Array.isArray(data) && data.length > 0) {
                allEmployees = data;
                filteredEmployees = [...allEmployees];
                console.log(`Loaded ${allEmployees.length} employees from merged file`);
                return true;
            }
        } else {
            console.warn(`Merged employees.json not available: ${response.status} ${response.statusText}`);
        }
    } catch (e) {
        console.warn('Failed to load merged employees.json:', e?.message || e);
    }
    return false;
}

// Deprecated: legacy discovery removed by policy

// Deprecated: batch individual loading removed by policy

// Deprecated: all fallbacks removed by policy


// Computer data is now loaded directly from individual employee files
// No separate computer data loading needed

// UI functions are handled by ui-manager.js and filters.js

// Search, filter, and rendering functions are handled by other modules

// Computer data display is now handled within individual employee cards

// Utility functions
function setSearchTerm(term) {
    const searchInput = document.getElementById('searchInput');
    searchInput.value = term;
    searchInput.focus();
    handleSearch();
}

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

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showError(message) {
    const grid = document.getElementById('employeeGrid');
    grid.innerHTML = `<div class="error-message">${message}</div>`;
}

// Show/hide return to top button
window.addEventListener('scroll', function() {
    const returnToTop = document.getElementById('returnToTop');
    if (window.pageYOffset > 300) {
        returnToTop.classList.add('show');
    } else {
        returnToTop.classList.remove('show');
    }
});
