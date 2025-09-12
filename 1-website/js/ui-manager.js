// UI Management functions
function initializeUI() {
    // Populate filters
    populateFilters();
    
    // Render employees
    renderEmployees();
    
    // Setup search and filters
    setupEventListeners();
}

function populateFilters() {
    // No filters needed for simple search design
}

function setupEventListeners() {
    // Search input
    document.getElementById('searchInput').addEventListener('input', handleSearch);
}

function renderEmployees(employees = filteredEmployees) {
    const grid = document.getElementById('employeeGrid');
    
    if (employees.length === 0) {
        grid.innerHTML = '<div class="no-results">No employees found matching your search.</div>';
        return;
    }
    
    grid.innerHTML = employees.map(employee => createEmployeeCard(employee)).join('');
}

function createEmployeeCard(employee) {
    // Use local image path if available, otherwise fall back to image_url or default
    const imageUrl = employee.image_local_path || employee.image_url || `assets/images/${employee.real_name?.replace(/\s+/g, '_')}_profile.jpg`;
    const projects = employee.projects || [];
    const projectId = `projects_${employee.real_name?.replace(/\s+/g, '_')}`;
    
    // Handle phone formatting - the phone is already formatted in the JSON
    const phone = employee.phone || employee.mobile || '';
    
    // Handle department - check multiple possible fields
    const department = employee.department || employee.team || employee.division || '';
    
    // Handle years with firm
    const yearsInfo = employee.years_with_firm ? `Years with firm: ${employee.years_with_firm}` : '';
    
    // Handle education
    const education = employee.education || [];
    
    // Handle computer specifications if available
    const computerInfo = employee.computer || employee.computer_specs;
    
    return `
        <div class="employee-card">
            <div class="employee-image">
                <img src="${imageUrl}" alt="${employee.real_name}" onerror="this.src='assets/images/default_profile.jpg'">
            </div>
            <div class="employee-info">
                <h3 class="employee-name">${employee.real_name || 'Unknown'}</h3>
                <p class="employee-position">${employee.position || employee.title || 'Position not available'}</p>
                <p class="employee-location">${employee.office_location || 'Location not available'}</p>
                ${department ? `<p class="employee-department">Department: ${department}</p>` : ''}
                ${yearsInfo ? `<p class="employee-years">${yearsInfo}</p>` : ''}
                <div class="contact-info">
                    ${employee.email ? `<p class="contact-item">📧 <a href="mailto:${employee.email}">${employee.email}</a></p>` : ''}
                    ${phone ? `<p class="contact-item">📞 <a href="tel:${phone}">${phone}</a></p>` : ''}
                    ${employee.teams_url ? `<p class="contact-item">💬 <a href="${employee.teams_url}" target="_blank">Microsoft Teams</a></p>` : ''}
                </div>
                ${education.length > 0 ? `
                    <div class="education-section">
                        <h4>Education</h4>
                        ${education.map(edu => `
                            <p class="education-item">${edu.institution} - ${edu.degree}</p>
                            ${edu.specialty ? `<p class="education-specialty">${edu.specialty}</p>` : ''}
                        `).join('')}
                    </div>
                ` : ''}
                ${computerInfo ? `
                    <div class="computer-section">
                        <h4>🖥️ Computer Specifications</h4>
                        <div class="computer-details">
                            ${computerInfo.OS ? `<p class="computer-item"><strong>OS:</strong> ${computerInfo.OS}</p>` : ''}
                            ${computerInfo.CPU ? `<p class="computer-item"><strong>CPU:</strong> ${computerInfo.CPU}</p>` : ''}
                            ${computerInfo['GPU Name'] ? `<p class="computer-item"><strong>GPU:</strong> ${computerInfo['GPU Name']}</p>` : ''}
                            ${computerInfo['Total Physical Memory'] ? `<p class="computer-item"><strong>RAM:</strong> ${Math.round(computerInfo['Total Physical Memory'] / (1024**3))} GB</p>` : ''}
                            ${computerInfo.Manufacturer && computerInfo.Model ? `<p class="computer-item"><strong>Hardware:</strong> ${computerInfo.Manufacturer} ${computerInfo.Model}</p>` : ''}
                        </div>
                    </div>
                ` : ''}
                ${projects.length > 0 ? `
                    <div class="projects-section">
                        <h4>Projects (${projects.length})</h4>
                        <div class="projects-list" id="${projectId}" style="display: none;">
                            ${projects.map(project => `
                                <div class="project-item">
                                    <strong>${project.name || project.title || 'Untitled Project'}</strong>
                                    ${project.client ? `<p class="project-client">Client: ${project.client}</p>` : ''}
                                    ${project.role ? `<p class="project-role">Role: ${project.role}</p>` : ''}
                                    ${project.url ? `<a href="${project.url}" target="_blank" class="project-link">View Project →</a>` : ''}
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

// Computer data is now integrated into individual employee cards
