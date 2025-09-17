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

        // Initialize fuzzy search with employee data
        if (typeof fuzzySearch !== 'undefined' && fuzzySearch.initialize) {
            fuzzySearch.initialize(allEmployees);
            console.log('Fuzzy search initialized with', allEmployees.length, 'employees');
        }
        
        // Initialize UI (handled by ui-manager.js)
        if (typeof initializeUI === 'function') {
            initializeUI();
        }
        
        // Set up search event listener
        const searchInput = document.getElementById('searchInput');
        if (searchInput && typeof handleSearch === 'function') {
            searchInput.addEventListener('input', handleSearch);
            console.log('Search event listener attached');
        }

        // Update header information
        updateHeaderInfo();
        
        // Hide loading indicator
        document.getElementById('loadingIndicator').style.display = 'none';

    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Data not found');
    }
}

// Deprecated: individual loading and fallbacks removed by policy

async function tryLoadMergedEmployees() {
    // Always use a relative path from docs root so it works locally and on GitHub Pages
    // docs/index.html -> assets/employees.json
    const url = 'assets/employees.json';
    try {
        console.log('Trying merged employees file:', url);
        const response = await fetch(url, { signal: AbortSignal.timeout(10000) });
        if (response.ok) {
            const data = await response.json();
            // Handle both old array format and new dictionary format
            if (Array.isArray(data) && data.length > 0) {
                // Old format: array of employees
                allEmployees = data;
                filteredEmployees = [...allEmployees];
                console.log(`Loaded ${allEmployees.length} employees from merged file (array format)`);
                return true;
            } else if (typeof data === 'object' && data !== null && !Array.isArray(data)) {
                // New format: dictionary of employees
                allEmployees = Object.values(data);
                filteredEmployees = [...allEmployees];
                console.log(`Loaded ${allEmployees.length} employees from merged file (dictionary format)`);
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

// Update header information
function updateHeaderInfo() {
    const now = new Date();
    const generatedTime = now.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
    });
    
    // Try to get the last modified time of the employees.json file
    // For now, we'll use the current time as data time
    const dataTime = now.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Update the header elements
    const generatedTimeElement = document.getElementById('generatedTime');
    const dataTimeElement = document.getElementById('dataTime');
    
    if (generatedTimeElement) {
        generatedTimeElement.textContent = `Generated: ${generatedTime}`;
    }
    
    if (dataTimeElement) {
        dataTimeElement.textContent = `Data: ${dataTime}`;
    }
}
