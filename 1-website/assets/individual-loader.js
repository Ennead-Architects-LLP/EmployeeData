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
        
        // Initialize UI
        initializeUI();
        
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
        
        // Get list of individual employee files
        const response = await fetch('individual_employees/');
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
                const employeeResponse = await fetch(`individual_employees/${filename}`);
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
        
        // Fallback: try to load a few individual files if index fails
        try {
            console.log('Trying fallback: loading individual files directly...');
            // Try to load a few known employee files as fallback
            const fallbackFiles = ['index.json', 'Sen_Zhang.json', 'Adriana_Burton.json'];
            const employees = [];
            
            for (const filename of fallbackFiles) {
                try {
                    const response = await fetch(`individual_employees/${filename}`);
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
        const response = await fetch('computer_data/all_computers.json');
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

function initializeUI() {
    // Populate filters
    populateFilters();
    
    // Render employees
    renderEmployees();
    
    // Setup search and filters
    setupEventListeners();
}

function populateFilters() {
    // Get unique locations and departments
    const locations = [...new Set(allEmployees.map(emp => emp.office_location).filter(Boolean))].sort();
    const departments = [...new Set(allEmployees.map(emp => emp.department).filter(Boolean))].sort();
    
    // Populate location filter
    const locationFilter = document.getElementById('locationFilter');
    locations.forEach(location => {
        const option = document.createElement('option');
        option.value = location;
        option.textContent = location;
        locationFilter.appendChild(option);
    });
    
    // Populate department filter
    const departmentFilter = document.getElementById('departmentFilter');
    departments.forEach(department => {
        const option = document.createElement('option');
        option.value = department;
        option.textContent = department;
        departmentFilter.appendChild(option);
    });
}

function setupEventListeners() {
    // Search input
    document.getElementById('searchInput').addEventListener('input', handleSearch);
    
    // Filters
    document.getElementById('locationFilter').addEventListener('change', applyFilters);
    document.getElementById('departmentFilter').addEventListener('change', applyFilters);
    document.getElementById('sortBy').addEventListener('change', applyFilters);
}

function handleSearch() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    if (searchTerm === '') {
        filteredEmployees = [...allEmployees];
    } else {
        filteredEmployees = allEmployees.filter(employee => {
            const searchableText = [
                employee.real_name,
                employee.position,
                employee.office_location,
                employee.phone,
                employee.email,
                employee.department,
                ...(employee.projects || []).map(p => p.name || p.title || '')
            ].join(' ').toLowerCase();
            
            return searchableText.includes(searchTerm);
        });
    }
    
    applyFilters();
}

function applyFilters() {
    let filtered = [...filteredEmployees];
    
    // Apply location filter
    const locationFilter = document.getElementById('locationFilter').value;
    if (locationFilter) {
        filtered = filtered.filter(emp => emp.office_location === locationFilter);
    }
    
    // Apply department filter
    const departmentFilter = document.getElementById('departmentFilter').value;
    if (departmentFilter) {
        filtered = filtered.filter(emp => emp.department === departmentFilter);
    }
    
    // Apply sorting
    const sortBy = document.getElementById('sortBy').value;
    filtered.sort((a, b) => {
        switch (sortBy) {
            case 'name':
                return (a.real_name || '').localeCompare(b.real_name || '');
            case 'location':
                return (a.office_location || '').localeCompare(b.office_location || '');
            case 'department':
                return (a.department || '').localeCompare(b.department || '');
            default:
                return 0;
        }
    });
    
    renderEmployees(filtered);
}

function renderEmployees(employees = filteredEmployees) {
    const grid = document.getElementById('employeeGrid');
    
    if (employees.length === 0) {
        grid.innerHTML = '<div class="no-results">No employees found matching your criteria.</div>';
        return;
    }
    
    grid.innerHTML = employees.map(employee => createEmployeeCard(employee)).join('');
}

function createEmployeeCard(employee) {
    const imageUrl = employee.image_local_path || employee.image_url || `images/${employee.real_name?.replace(/\s+/g, '_')}_profile.jpg`;
    const projects = employee.projects || [];
    const projectId = `projects_${employee.real_name?.replace(/\s+/g, '_')}`;
    
    return `
        <div class="employee-card">
            <div class="employee-image">
                <img src="${imageUrl}" alt="${employee.real_name}" onerror="this.src='images/default_profile.jpg'">
            </div>
            <div class="employee-info">
                <h3 class="employee-name">${employee.real_name || 'Unknown'}</h3>
                <p class="employee-position">${employee.position || 'Position not available'}</p>
                <p class="employee-location">${employee.office_location || 'Location not available'}</p>
                <div class="contact-info">
                    ${employee.email ? `<p class="contact-item">📧 <a href="mailto:${employee.email}">${employee.email}</a></p>` : ''}
                    ${employee.phone ? `<p class="contact-item">📞 <a href="tel:${employee.phone}">${employee.phone}</a></p>` : ''}
                </div>
                ${projects.length > 0 ? `
                    <div class="projects-section">
                        <h4>Projects (${projects.length})</h4>
                        <div class="projects-list" id="${projectId}" style="display: none;">
                            ${projects.map(project => `
                                <div class="project-item">
                                    <strong>${project.name || project.title || 'Untitled Project'}</strong>
                                    ${project.description ? `<p>${project.description}</p>` : ''}
                                </div>
                            `).join('')}
                        </div>
                        <button class="toggle-projects" onclick="toggleProjects('${projectId}')">
                            <span id="icon_${projectId}">▶</span> Show Projects
                        </button>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

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
