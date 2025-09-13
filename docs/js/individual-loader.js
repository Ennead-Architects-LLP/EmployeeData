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
        // Load employee data from individual files
        await loadIndividualEmployeeData();
        
        // Computer data is now loaded with individual employee data
        
        // Initialize UI (handled by ui-manager.js)
        if (typeof initializeUI === 'function') {
            initializeUI();
        }
        
        // Hide loading indicator
        document.getElementById('loadingIndicator').style.display = 'none';
        
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Failed to load data. Please refresh the page.');
    }
}

async function loadIndividualEmployeeData() {
    try {
        console.log('Loading individual employee data...');
        
        // Discover files dynamically by trying common patterns
        const files = await discoverEmployeeFiles();
        console.log(`Found ${files.length} individual employee files`);
        
        // Load each individual employee file
        allEmployees = [];
        for (const filename of files) {
            try {
                const employeeResponse = await fetch(`${getBasePath()}assets/individual_employees/${filename}`);
                if (employeeResponse.ok) {
                    const employeeData = await employeeResponse.json();
                    allEmployees.push(employeeData);
                }
            } catch (error) {
                console.warn(`Failed to load ${filename}:`, error);
            }
        }
        
        filteredEmployees = [...allEmployees];
        
        // Initialize fuzzy search with employee data
        if (typeof fuzzySearch !== 'undefined' && fuzzySearch.initialize) {
            fuzzySearch.initialize(allEmployees);
        }
        
        // Update header with employee count
        document.getElementById('mainTitle').innerHTML = `Ennead's People <span class="employee-count">(${allEmployees.length} employees)</span>`;
        
        // Update generation time
        const now = new Date();
        const formattedTime = now.toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, '').replace(/:/g, '-');
        document.getElementById('generatedTime').textContent = `Generated: ${formattedTime}`;
        document.getElementById('dataTime').textContent = `Data: ${formattedTime}`;
        
        console.log(`Successfully loaded ${allEmployees.length} employees from individual files`);
        
    } catch (error) {
        console.error('Error loading individual employee data:', error);
        throw new Error('Failed to load employee data');
    }
}

async function discoverEmployeeFiles() {
    console.log('Attempting to discover employee files dynamically...');
    const basePath = getBasePath();
    console.log('Base path:', basePath);
    console.log('Current URL:', window.location.href);
    console.log('Pathname:', window.location.pathname);
    
    try {
        // Try to load from the generated JSON file
        const url = `${basePath}employee_json_dir.json`;
        console.log('Attempting to fetch:', url);
        const response = await fetch(url);
        
        if (response.ok) {
            const data = await response.json();
            console.log(`Successfully loaded employee file list with ${data.total_count} files`);
            return data.employee_files;
        } else {
            console.error(`Failed to load employee_json_dir.json: ${response.status} ${response.statusText}`);
            console.error('Response URL:', response.url);
            throw new Error('Employee JSON directory file not available');
        }
    } catch (error) {
        console.log('Employee JSON directory file failed, trying fallback method...');
        
        // Fallback: try to load from old static file list
        try {
            const fallbackUrl = `${basePath}assets/employee_files_list.json`;
            console.log('Attempting fallback fetch:', fallbackUrl);
            const response = await fetch(fallbackUrl);
            if (response.ok) {
                const files = await response.json();
                console.log(`Loaded ${files.length} files from static list as fallback`);
                return files;
            } else {
                console.error(`Fallback also failed: ${response.status} ${response.statusText}`);
                console.error('Fallback URL:', fallbackUrl);
                console.error('Response URL:', response.url);
            }
        } catch (fallbackError) {
            console.error('Both JSON directory file and static list failed:', fallbackError);
        }
        
        // Last resort: return empty array
        console.warn('No file discovery method worked, returning empty array');
        return [];
    }
}


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
