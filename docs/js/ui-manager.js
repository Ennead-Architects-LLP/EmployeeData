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

// Helper functions for computer information display
function formatMemory(value) {
    if (value === null || value === undefined || value === '') return null;
    const bytes = parseInt(value);
    if (isNaN(bytes)) return null;
    
    // Debug logging
    console.log('formatMemory - Input:', value, 'Parsed bytes:', bytes);
    
    // The values appear to be in bytes, so convert to GB
    // 133,893,872 bytes should be ~124.7 GB
    const gb = bytes / (1024 * 1024 * 1024);
    const result = `${Math.round(gb * 10) / 10} GB`;
    
    console.log('formatMemory - Result:', result);
    return result;
}

function formatGPUMemory(value) {
    if (value === null || value === undefined || value === '') return null;
    const bytes = parseFloat(value);
    if (isNaN(bytes)) return null;
    
    // Debug logging
    console.log('formatGPUMemory - Input:', value, 'Parsed bytes:', bytes);
    
    // The values appear to be in bytes, so convert to GB
    // 4,193,280 bytes should be ~3.9 GB
    const gb = bytes / (1024 * 1024 * 1024);
    const result = `${Math.round(gb * 10) / 10} GB`;
    
    console.log('formatGPUMemory - Result:', result);
    return result;
}

function calculateGPUAge(gpuDate) {
    if (!gpuDate || gpuDate === null || gpuDate === '') return null;
    
    try {
        console.log('calculateGPUAge - Input:', gpuDate);
        
        // Parse various date formats from the GPU data
        let date;
        const dateStr = String(gpuDate).trim();
        
        // Handle formats like "April 12, 2021" or "Apirl 12,2021" (typo in data)
        if (dateStr.match(/^[A-Za-z]+\s+\d+,\s*\d{4}$/)) {
            // Fix common typos in month names
            const fixedDateStr = dateStr.replace('Apirl', 'April');
            date = new Date(fixedDateStr);
        }
        // Handle other common date formats
        else if (dateStr.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
            date = new Date(dateStr);
        }
        // Handle ISO format
        else if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
            date = new Date(dateStr);
        }
        else {
            // Try to parse as-is
            date = new Date(dateStr);
        }
        
        if (isNaN(date.getTime())) {
            console.log('calculateGPUAge - Invalid date:', dateStr);
            return null;
        }
        
        // Calculate age in years
        const now = new Date();
        const ageInYears = (now - date) / (365.25 * 24 * 60 * 60 * 1000);
        
        let result;
        if (ageInYears < 1) {
            const ageInMonths = Math.round(ageInYears * 12);
            result = `${ageInMonths} month${ageInMonths !== 1 ? 's' : ''}`;
        } else {
            result = `${Math.round(ageInYears * 10) / 10} year${ageInYears >= 2 ? 's' : ''}`;
        }
        
        console.log('calculateGPUAge - Result:', result);
        return result;
    } catch (error) {
        console.warn('Error calculating GPU age for date:', gpuDate, error);
        return null;
    }
}

function renderComputerField(computer, fieldKey, displayLabel, alternateKey = null, formatter = null) {
    // Fields to skip (as requested by user)
    const skipFields = ['username', 'Username', 'last name', 'Last Name', 'first name', 'First Name', 'date', 'Date'];
    
    // Get value from computer object (try both lowercase and title case keys)
    let value = computer[fieldKey] || computer[alternateKey];
    
    
    
    // Skip if no value or if field should be skipped (but allow 0 values for memory)
    if ((value === null || value === undefined || value === '') || skipFields.includes(fieldKey) || skipFields.includes(alternateKey)) {
        return '';
    }
    
    // Apply formatter if provided
    if (formatter) {
        const formattedValue = formatter(value);
        if (formattedValue === null || formattedValue === undefined || formattedValue === '') {
            return '';
        }
        value = formattedValue;
    }
    
    return `<p class="computer-item"><strong>${displayLabel}:</strong> ${value}</p>`;
}

function renderComputerSection(computers, sectionTitle, basePath, showAllFields = false) {
    if (!computers || computers.length === 0) return '';
    
    // Determine CSS class based on section title
    let sectionClass = 'computer-section';
    if (sectionTitle.includes('Individual Computer Data')) {
        sectionClass += ' individual-computer-data';
    } else if (sectionTitle.includes('Static GPU Master List')) {
        sectionClass += ' static-gpu-master-list';
    }
    
    // Add data source indicator
    let dataSourceIndicator = '';
    if (sectionTitle.includes('Individual Computer Data')) {
        dataSourceIndicator = '<span class="data-source-badge confidential">Live Data</span>';
    } else if (sectionTitle.includes('Static GPU Master List')) {
        dataSourceIndicator = '<span class="data-source-badge static">Static Data</span>';
    }
    
    return `
        <div class="${sectionClass}">
            <h4>
                <img class="computer-icon" src="${basePath}assets/icons/computer.png" alt="Computer icon">
                ${sectionTitle}
                ${dataSourceIndicator}
            </h4>
            ${computers.map((computer, index) => `
                <div class="computer-details">
                    ${computer.computername || computer.Computername ? `<h5 class="computer-name">${computer.computername || computer.Computername}</h5>` : ''}
                    <div class="computer-specs">
                        ${showAllFields ? 
                            // For GPU Master List - show ALL fields
                            Object.entries(computer).map(([key, value]) => {
                                if (value === null || value === undefined || value === '') return '';
                                if (key === 'computername' || key === 'Computername') return '';
                                return `<p class="computer-item"><strong>${key}:</strong> ${value}</p>`;
                            }).join('') :
                            // For individual computer info - show specific fields
                            `
                                ${renderComputerField(computer, 'os', 'OS', 'OS')}
                                ${renderComputerField(computer, 'cpu', 'CPU', 'CPU')}
                                ${renderComputerField(computer, 'gpu_name', 'GPU', 'GPU Name')}
                                ${renderComputerField(computer, 'gpu_processor', 'GPU Processor', 'GPU Processor')}
                                ${renderComputerField(computer, 'gpu_driver', 'GPU Driver', 'GPU Driver')}
                                ${computer['GPU Date'] || computer['gpu_date'] ? `<p class="computer-item"><strong>GPU Age:</strong> ${calculateGPUAge(computer['GPU Date'] || computer['gpu_date']) || 'Unknown'}</p>` : ''}
                                ${renderComputerField(computer, 'replacement_priority', 'Replacement Priority', 'Replacement Piroirty ')}
                                ${renderComputerField(computer, 'memory_bytes', 'RAM', 'Total Physical Memory', formatMemory)}
                                ${renderComputerField(computer, 'gpu_memory', 'GPU Memory', 'GPU Memory', formatGPUMemory)}
                                ${renderComputerField(computer, 'manufacturer', 'Manufacturer', 'Manufacturer')}
                                ${renderComputerField(computer, 'model', 'Model', 'Model')}
                                ${renderComputerField(computer, 'serial_number', 'Serial', 'Serial Number')}
                            `
                        }
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function createEmployeeCard(employee) {
    // Determine the base path for assets (GitHub Pages vs local)
    const isGitHubPages = window.location.hostname.includes('github.io');
    const basePath = isGitHubPages ? '/EmployeeData/' : '';
    
    // Use local image path if available, otherwise fall back to image_url or default
    let imageUrl;
    let fallbackImageUrl = basePath + 'assets/icons/default_profile_image.jpg';
    
    if (employee.image_local_path && employee.image_local_path.trim() !== '') {
        // Adjust path for GitHub Pages
        imageUrl = basePath + employee.image_local_path;
    } else if (employee.image_url && employee.image_url.trim() !== '') {
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
    
    // Handle computer specifications - now we have two separate sections
    const individualComputerInfo = employee.computer_info || employee.computer || employee.computer_specs;
    const gpuMasterListInfo = employee['Static GPU Master List'];
    
    let individualComputers = [];
    let gpuMasterListComputers = [];
    
    // Process individual computer info
    if (individualComputerInfo) {
        if (Array.isArray(individualComputerInfo)) {
            individualComputers = individualComputerInfo;
        } else if (typeof individualComputerInfo === 'object') {
            individualComputers = Object.values(individualComputerInfo);
        }
    }
    
    // Process GPU master list info
    if (gpuMasterListInfo) {
        if (Array.isArray(gpuMasterListInfo)) {
            gpuMasterListComputers = gpuMasterListInfo;
        } else if (typeof gpuMasterListInfo === 'object') {
            gpuMasterListComputers = Object.values(gpuMasterListInfo);
        }
    }
    
    // Debug logging for data separation
    if (employee.human_name && (employee.human_name.includes('Sen') || individualComputers.length > 0 || gpuMasterListComputers.length > 0)) {
        console.log(`Debug - Employee: ${employee.human_name}`);
        console.log(`Debug - Individual Computer Info:`, individualComputerInfo);
        console.log(`Debug - GPU Master List Info:`, gpuMasterListInfo);
        console.log(`Debug - Individual Computers (${individualComputers.length}):`, individualComputers);
        console.log(`Debug - GPU Master List Computers (${gpuMasterListComputers.length}):`, gpuMasterListComputers);
        console.log('--- Data Separation Status ---');
        console.log(`Individual Computer Data: ${individualComputers.length > 0 ? '✅ Present' : '❌ Missing'}`);
        console.log(`Static GPU Master List Data: ${gpuMasterListComputers.length > 0 ? '✅ Present' : '❌ Missing'}`);
        console.log('--- End Debug ---');
    }
    
    // Create source indicators for data origin using created_from list
    let sourceIndicator = '';
    if (employee.created_from && Array.isArray(employee.created_from)) {
        // Create multiple colored dots based on the created_from list
        const indicators = employee.created_from.map(source => {
            let colorClass = '';
            let tooltip = '';
            
            if (source.includes('Individual Employee')) {
                colorClass = 'individual-employee';
                tooltip = 'Individual Employee Files (Blue)';
            } else if (source.includes('Individual Computer')) {
                colorClass = 'individual-computer';
                tooltip = 'Individual Computer Data (Green - Live Data)';
            } else if (source.includes('GPU Master List')) {
                colorClass = 'gpu-master';
                tooltip = 'GPU Master List 2025 (Orange - Static Data)';
            } else {
                // Default color for unknown sources
                colorClass = 'unknown-source';
                tooltip = source;
            }
            
            return `<div class="source-indicator ${colorClass}" title="${tooltip}">●</div>`;
        });
        
        sourceIndicator = indicators.join('');
    } else if (employee.created_from && typeof employee.created_from === 'string') {
        // Handle legacy string format
        let tooltip = `Created from: ${employee.created_from}`;
        if (employee.created_from.includes('GPU Master List')) {
            tooltip = 'GPU Master List 2025 (Orange - Static Data)';
            sourceIndicator = `<div class="source-indicator gpu-master" title="${tooltip}">●</div>`;
        } else if (employee.created_from.includes('Individual Computer')) {
            tooltip = 'Individual Computer Data (Green - Live Data)';
            sourceIndicator = `<div class="source-indicator individual-computer" title="${tooltip}">●</div>`;
        } else if (employee.created_from.includes('Individual Employee')) {
            tooltip = 'Individual Employee Files (Blue)';
            sourceIndicator = `<div class="source-indicator individual-employee" title="${tooltip}">●</div>`;
        }
    }
    
    return `
        <div class="employee-card">
            <div class="employee-image">
                <img id="${imageId}" src="${imageUrl}" alt="${employee.human_name}">
            </div>
            <div class="employee-info">
                <h3 class="employee-name">
                    ${employee.human_name || 'Unknown'}
                    ${sourceIndicator}
                </h3>
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
                ${(individualComputers.length > 0 || gpuMasterListComputers.length > 0) && (window.sectionToggles?.computer ?? true) ? `
                    ${renderComputerSection(individualComputers, 'Individual Computer Data (Live Data)', basePath, false)}
                    ${renderComputerSection(gpuMasterListComputers, 'Static GPU Master List (2025)', basePath, true)}
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
            console.log(`Image failed to load: ${this.src}`);
            
            if (!this.dataset.fallbackTried) {
                this.dataset.fallbackTried = 'true';
                // Try fallback image
                const isGitHubPages = window.location.hostname.includes('github.io');
                const basePath = isGitHubPages ? '/EmployeeData/' : '';
                const fallbackUrl = basePath + 'assets/icons/default_profile_image.jpg';
                console.log(`Trying fallback image: ${fallbackUrl}`);
                this.src = fallbackUrl;
            } else {
                // If fallback also failed, show placeholder
                console.log('Fallback image also failed, showing placeholder');
                this.style.display = 'none';
                this.parentElement.innerHTML = '<div class="no-image-placeholder">📷</div>';
            }
        });
        
        // Add load success handler for debugging
        img.addEventListener('load', function() {
            console.log(`Image loaded successfully: ${this.src}`);
        });
    });
}
