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
    // Search input event listener is handled in employee_data_loader.js
    // No need to duplicate here
}

function renderEmployees(employees = filteredEmployees) {
    const grid = document.getElementById('employeeGrid');
    
    // Add debugging to prevent multiple renders
    if (grid.dataset.rendering === 'true') {
        console.log('Preventing duplicate render');
        return;
    }
    
    grid.dataset.rendering = 'true';
    
    if (employees.length === 0) {
        grid.innerHTML = '<div class="no-results">No employees found matching your search.</div>';
    } else {
        grid.innerHTML = employees.map(employee => createEmployeeCard(employee)).join('');
        
        // Set up image error handling after rendering
        setupImageErrorHandling();
    }
    
    // Reset the rendering flag after a short delay
    setTimeout(() => {
        grid.dataset.rendering = 'false';
    }, 100);
}

function createEmployeeCard(employee) {
    // Determine the base path for assets (GitHub Pages vs local)
    const isGitHubPages = window.location.hostname.includes('github.io');
    const basePath = isGitHubPages ? '/EmployeeData/' : '';
    
    // Use local image path if available, otherwise fall back to image_url or default
    let imageUrl;
    let fallbackImageUrl = basePath + 'assets/icons/default_profile_image.jpg';
    
    if (employee.image_local_path) {
        // Adjust path for GitHub Pages
        imageUrl = basePath + employee.image_local_path;
    } else if (employee.image_url) {
        // Use the remote image URL as-is
        imageUrl = employee.image_url;
    } else {
        // Use default profile image when no image is specified
        imageUrl = fallbackImageUrl;
    }
    
    // Create a unique ID for this image to prevent conflicts
    const imageId = `img_${employee.human_name?.replace(/\s+/g, '_')}_${Date.now()}`;
    // Handle projects - they can be an object or array
    let projects = [];
    if (employee.projects) {
        if (Array.isArray(employee.projects)) {
            projects = employee.projects;
        } else if (typeof employee.projects === 'object') {
            // Convert object format to array
            projects = Object.values(employee.projects);
        }
    }
    const projectId = `projects_${employee.human_name?.replace(/\s+/g, '_')}`;
    
    // Handle phone formatting - the phone is already formatted in the JSON
    const phone = employee.phone || employee.mobile || '';
    
    // Handle department - check multiple possible fields
    const department = employee.department || employee.team || employee.division || '';
    
    // Handle years with firm
    const yearsInfo = employee.years_with_firm ? `Years with firm: ${employee.years_with_firm}` : '';
    
    // Handle education
    const education = employee.education || [];
    
    // Handle licenses
    const licenses = employee.licenses || [];
    
    // Handle memberships
    const memberships = employee.memberships || [];
    
    // Handle computer specifications if available
    const computerInfo = employee.computer_info || employee.computer || employee.computer_specs;
    let computers = [];
    
    // Debug logging
    if (employee.human_name && employee.human_name.includes('Sen')) {
        console.log('Debug - Employee:', employee.human_name);
        console.log('Debug - Computer Info:', computerInfo);
        console.log('Debug - Computer Info Type:', typeof computerInfo);
        console.log('Debug - Is Array:', Array.isArray(computerInfo));
    }
    
    if (computerInfo) {
        if (Array.isArray(computerInfo)) {
            // Handle list of dictionaries format: [{computername: "PC1", os: "Windows"}, ...]
            // Note: Server prefers dict of dict format, but we support both for compatibility
            computers = computerInfo;
            if (employee.human_name && employee.human_name.includes('Sen')) {
                console.log('Debug - Using list of dict format, computers:', computers);
            }
        } else if (typeof computerInfo === 'object') {
            // Handle dictionary of dictionaries format: {"PC1": {computername: "PC1", os: "Windows"}, ...}
            // This is the preferred format used by the server to prevent duplicates
            computers = Object.values(computerInfo);
            if (employee.human_name && employee.human_name.includes('Sen')) {
                console.log('Debug - Using dict of dict format (preferred), computers:', computers);
            }
        }
    }
    
    if (employee.human_name && employee.human_name.includes('Sen')) {
        console.log('Debug - Final computers array:', computers);
    }
    
    return `
        <div class="employee-card">
            <div class="employee-image">
                <img id="${imageId}" src="${imageUrl}" alt="${employee.human_name}">
            </div>
            <div class="employee-info">
                <h3 class="employee-name">${employee.human_name || 'Unknown'}</h3>
                <p class="employee-position">${employee.position || employee.title || 'Position not available'}</p>
                ${employee.office_location ? `<p class="employee-location">${employee.office_location}</p>` : ''}
                ${department ? `<p class="employee-department">Department: ${department}</p>` : ''}
                ${yearsInfo && (window.sectionToggles?.years ?? true) ? `<p class="employee-years">${yearsInfo}</p>` : ''}
                ${employee.bio && (window.sectionToggles?.bio ?? true) ? `<div class=\"bio-section\"><p class=\"employee-bio\">${employee.bio}</p></div>` : ''}
                <div class="contact-info">
                    ${employee.email ? `<p class="contact-item"><span class="icon email-icon"></span> <a href="mailto:${employee.email}">${employee.email}</a></p>` : ''}
                    ${phone ? `<p class="contact-item"><span class="icon phone-icon"></span> <a href="tel:${phone}">${phone}</a></p>` : ''}
                    ${employee.teams_url ? `<p class="contact-item"><span class="icon chat-icon"></span> <a href="${employee.teams_url}" target="_blank">Microsoft Teams</a></p>` : ''}
                </div>
                ${education.length > 0 && (window.sectionToggles?.education ?? true) ? `
                    <div class="education-section">
                        <h4>Education</h4>
                        ${education.map(edu => `
                            <p class="education-item">${edu.institution} - ${edu.degree}</p>
                            ${edu.specialty ? `<p class="education-specialty">${edu.specialty}</p>` : ''}
                        `).join('')}
                    </div>
                ` : ''}
                ${licenses.length > 0 && (window.sectionToggles?.licenses ?? true) ? `
                    <div class="licenses-section">
                        <h4>Licenses & Certifications</h4>
                        ${licenses.map(item => {
                            if (item == null) {
                                return '';
                            }
                            if (typeof item === 'string') {
                                return `<p class="license-item">${item}</p>`;
                            }
                            if (typeof item === 'object') {
                                const parts = [];
                                const title = item.license || item.name || item.title;
                                if (title) parts.push(title);
                                const state = item.state || item.region;
                                if (state) parts.push(state);
                                const number = item.number || item.id;
                                if (number) parts.push(`#${number}`);
                                const earned = item.earned || item.year || item.date;
                                if (earned) parts.push(`${earned}`);
                                const text = parts.length > 0 ? parts.join(' — ') : '[license]';
                                return `<p class="license-item">${text}</p>`;
                            }
                            return '';
                        }).join('')}
                    </div>
                ` : ''}
                ${memberships.length > 0 && (window.sectionToggles?.memberships ?? true) ? `
                    <div class="memberships-section">
                        <h4>Memberships</h4>
                        ${memberships.map(membership => `
                            <p class="membership-item">${membership}</p>
                        `).join('')}
                    </div>
                ` : ''}
                ${computers.length > 0 && (window.sectionToggles?.computer ?? true) ? `
                    <div class="computer-section">
                        <h4>
                            <img class="computer-icon" src="${(window.location.hostname.includes('github.io') ? '/EmployeeData/' : '')}assets/icons/computer.png" alt="Computer icon">
                            ${computers.length === 1 ? 'Computer Specification' : 'Computer Specifications'}
                        </h4>
                        ${computers.map((computer, index) => `
                            <div class="computer-details">
                                ${computer.computername ? `<h5 class="computer-name">${computer.computername}</h5>` : ''}
                                <div class="computer-specs">
                                    ${computer.os ? `<p class="computer-item"><strong>OS:</strong> ${computer.os}</p>` : ''}
                                    ${computer.cpu ? `<p class="computer-item"><strong>CPU:</strong> ${computer.cpu}</p>` : ''}
                                    ${computer.gpu_name ? `<p class="computer-item"><strong>GPU:</strong> ${computer.gpu_name}</p>` : ''}
                                    ${computer.memory_bytes ? `<p class="computer-item"><strong>RAM:</strong> ${Math.round(computer.memory_bytes / (1024**3))} GB</p>` : ''}
                                    ${computer.manufacturer && computer.model ? `<p class="computer-item"><strong>Hardware:</strong> ${computer.manufacturer} ${computer.model}</p>` : ''}
                                    ${computer.serial_number ? `<p class="computer-item"><strong>Serial:</strong> ${computer.serial_number}</p>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                ${projects.length > 0 && (window.sectionToggles?.projects ?? true) ? `
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

// Set up image error handling for all images in the grid
function setupImageErrorHandling() {
    const images = document.querySelectorAll('.employee-image img');
    images.forEach(img => {
        // Remove any existing error handlers
        img.onerror = null;
        
        // Add new error handler that tries fallback image first
        img.addEventListener('error', function() {
            if (!this.dataset.fallbackTried) {
                this.dataset.fallbackTried = 'true';
                // Try fallback image
                const isGitHubPages = window.location.hostname.includes('github.io');
                const basePath = isGitHubPages ? '/EmployeeData/' : '';
                const fallbackUrl = basePath + 'assets/icons/default_profile_image.jpg';
                this.src = fallbackUrl;
            } else {
                // If fallback also failed, show placeholder
                this.style.display = 'none';
                this.parentElement.innerHTML = '<div class="no-image-placeholder">📷</div>';
            }
        });
    });
}
