// Individual Employee Data Loader
// Loads employee data from individual JSON files instead of a big collected JSON

// Global variables
let allEmployees = [];
let filteredEmployees = [];
let computerData = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Load employee data from individual files
        await loadIndividualEmployeeData();
        
        // Load computer data
        await loadComputerData();
        
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
        
        // Get list of individual employee files from static JSON file
        const response = await fetch('assets/employee_files_list.json');
        if (!response.ok) {
            throw new Error('Failed to load employee files list');
        }
        
        const files = await response.json();
        console.log(`Found ${files.length} individual employee files`);
        
        // Load each individual employee file
        allEmployees = [];
        for (const filename of files) {
            try {
                const employeeResponse = await fetch(`assets/individual_employees/${filename}`);
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


async function loadComputerData() {
    try {
        const response = await fetch('assets/computer_data/all_computers.json');
        if (!response.ok) {
            throw new Error('Computer data not available');
        }
        computerData = await response.json();
        displayComputerData();
    } catch (error) {
        console.log('No computer data available yet');
        // Computer data is now integrated into individual employee cards, so no separate container needed
    }
}

// UI functions are handled by ui-manager.js and filters.js

// Search, filter, and rendering functions are handled by other modules

function displayComputerData() {
    const container = document.getElementById('computerDataContainer');
    
    if (!computerData || computerData.length === 0) {
        container.innerHTML = '<div class="no-data-message">No computer data available yet.</div>';
        return;
    }

    // Sort by timestamp (newest first)
    const sortedComputers = computerData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    let html = `
        <div class="computer-stats">
            <div class="stat-item">
                <span class="stat-number">${computerData.length}</span>
                <span class="stat-label">Total Submissions</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">${new Set(computerData.map(c => c.computer_name)).size}</span>
                <span class="stat-label">Unique Computers</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">${new Set(computerData.map(c => c.user)).size}</span>
                <span class="stat-label">Unique Users</span>
            </div>
        </div>
        <div class="computer-list">
    `;

    // Show last 10 submissions
    sortedComputers.slice(0, 10).forEach(computer => {
        const data = computer.data;
        const memoryGB = data['Total Physical Memory'] ? (data['Total Physical Memory'] / (1024**3)).toFixed(1) : 'Unknown';
        
        html += `
            <div class="computer-card">
                <div class="computer-header">
                    <h3>${data.Computername || 'Unknown'}</h3>
                    <span class="timestamp">${new Date(computer.timestamp).toLocaleString()}</span>
                </div>
                <div class="computer-details">
                    <div class="detail-row">
                        <span class="label">User:</span>
                        <span class="value">${data.Name || 'Unknown'} (${data.Username || 'Unknown'})</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">OS:</span>
                        <span class="value">${data.OS || 'Unknown'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Hardware:</span>
                        <span class="value">${data.Manufacturer || 'Unknown'} ${data.Model || 'Unknown'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">CPU:</span>
                        <span class="value">${data.CPU || 'Unknown'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">GPU:</span>
                        <span class="value">${data['GPU Name'] || 'Unknown'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Memory:</span>
                        <span class="value">${memoryGB} GB</span>
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

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
