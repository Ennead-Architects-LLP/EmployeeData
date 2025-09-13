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
        
        // Load employee files in batches to avoid rate limiting
        allEmployees = [];
        await loadEmployeeFilesInBatches(files);
        
        // If individual loading failed or loaded very few employees, try fallback
        if (allEmployees.length < files.length * 0.5) {
            console.warn(`Only loaded ${allEmployees.length}/${files.length} employees. Trying fallback method...`);
            await loadEmployeeDataFallback();
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
        
        console.log(`Successfully loaded ${allEmployees.length} employees`);
        
    } catch (error) {
        console.error('Error loading individual employee data:', error);
        console.log('Attempting fallback loading...');
        try {
            await loadEmployeeDataFallback();
            filteredEmployees = [...allEmployees];
        } catch (fallbackError) {
            console.error('Fallback loading also failed:', fallbackError);
            throw new Error('Failed to load employee data');
        }
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

async function loadEmployeeFilesInBatches(files, batchSize = 10, delayBetweenBatches = 100) {
    const basePath = getBasePath();
    
    for (let i = 0; i < files.length; i += batchSize) {
        const batch = files.slice(i, i + batchSize);
        console.log(`Loading batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(files.length / batchSize)} (${batch.length} files)`);
        
        // Load batch concurrently
        const batchPromises = batch.map(async (filename) => {
            try {
                const employeeResponse = await fetch(`${basePath}assets/individual_employees/${filename}`, {
                    // Add timeout to prevent hanging requests
                    signal: AbortSignal.timeout(5000)
                });
                if (employeeResponse.ok) {
                    const employeeData = await employeeResponse.json();
                    return employeeData;
                } else {
                    console.warn(`Failed to load ${filename}: ${employeeResponse.status}`);
                    return null;
                }
            } catch (error) {
                console.warn(`Failed to load ${filename}:`, error.message);
                return null;
            }
        });
        
        // Wait for batch to complete
        const batchResults = await Promise.all(batchPromises);
        
        // Add successful results to allEmployees
        batchResults.forEach(employee => {
            if (employee) {
                allEmployees.push(employee);
            }
        });
        
        // Add delay between batches to avoid rate limiting
        if (i + batchSize < files.length) {
            await new Promise(resolve => setTimeout(resolve, delayBetweenBatches));
        }
    }
    
    console.log(`Successfully loaded ${allEmployees.length}/${files.length} employee files`);
}

async function loadEmployeeDataFallback() {
    console.log('Attempting fallback loading method...');
    const basePath = getBasePath();
    
    // Try to load from a consolidated file if it exists
    try {
        // First try to load from a single consolidated JSON file
        const consolidatedResponse = await fetch(`${basePath}assets/consolidated_employees.json`, {
            signal: AbortSignal.timeout(10000)
        });
        
        if (consolidatedResponse.ok) {
            const consolidatedData = await consolidatedResponse.json();
            allEmployees = consolidatedData.employees || consolidatedData;
            console.log(`Loaded ${allEmployees.length} employees from consolidated file`);
            return;
        }
    } catch (error) {
        console.log('Consolidated file not available:', error.message);
    }
    
    // Fallback: Load a smaller subset of critical employees
    console.log('Loading critical employee subset...');
    const criticalEmployees = [
        'Adriana_Burton.json',
        'Aidan_Kim.json',
        'Aislinn_Weidele.json',
        'Akil_Matthews.json',
        'Alex_O\'Briant.json',
        'Alfonso_Gorini.json',
        'Amber_Kulikauskas.json',
        'Amy_Mielke.json',
        'Ana_Guillandeaux.json',
        'Annie_Durden.json'
    ];
    
    allEmployees = [];
    for (const filename of criticalEmployees) {
        try {
            const response = await fetch(`${basePath}assets/individual_employees/${filename}`, {
                signal: AbortSignal.timeout(3000)
            });
            if (response.ok) {
                const employeeData = await response.json();
                allEmployees.push(employeeData);
            }
        } catch (error) {
            console.warn(`Failed to load critical employee ${filename}:`, error.message);
        }
    }
    
    console.log(`Fallback loaded ${allEmployees.length} critical employees`);
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
