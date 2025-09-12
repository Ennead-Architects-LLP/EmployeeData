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
        
        // Get list of individual employee files from assets directory
        const response = await fetch('assets/individual_employees/');
        if (!response.ok) {
            throw new Error('Failed to load employee directory');
        }
        
        // Parse directory listing (this is a simplified approach)
        // In a real implementation, you might need a server-side endpoint to list files
        const text = await response.text();
        const files = extractJsonFiles(text);
        
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
        
        // Fallback: try to load individual files directly from directory listing
        try {
            console.log('Trying fallback: loading individual files directly...');
            // Try to get directory listing again for fallback
            const fallbackResponse = await fetch('assets/individual_employees/');
            if (fallbackResponse.ok) {
                const fallbackText = await fallbackResponse.text();
                const fallbackFiles = extractJsonFiles(fallbackText);
                const employees = [];
                
                for (const filename of fallbackFiles) {
                    try {
                        const response = await fetch(`assets/individual_employees/${filename}`);
                        if (response.ok) {
                            const data = await response.json();
                            if (Array.isArray(data)) {
                                employees.push(...data);
                            } else {
                                employees.push(data);
                            }
                        }
                    } catch (error) {
                        console.warn(`Could not load fallback file ${filename}:`, error);
                    }
                }
                
                if (employees.length > 0) {
                    allEmployees = employees;
                    filteredEmployees = [...allEmployees];
                    console.log('Fallback: Loaded from individual files');
                } else {
                    throw new Error('No fallback data available');
                }
            } else {
                throw new Error('Could not access directory for fallback');
            }
        } catch (fallbackError) {
            throw new Error('Failed to load employee data from any source');
        }
    }
}

function extractJsonFiles(htmlText) {
    // Simple regex to extract .json filenames from directory listing
    const jsonFileRegex = /href="([^"]+\.json)"/g;
    const files = [];
    let match;
    
    while ((match = jsonFileRegex.exec(htmlText)) !== null) {
        files.push(match[1]);
    }
    
    return files;
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
        document.getElementById('computerDataContainer').innerHTML = 
            '<div class="no-data-message">No computer data available yet. Data will appear here when users submit their computer information.</div>';
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
