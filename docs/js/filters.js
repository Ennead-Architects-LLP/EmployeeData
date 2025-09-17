// Fuzzy search functionality
function handleSearch() {
    const searchTerm = document.getElementById('searchInput').value;
    const suggestionsContainer = document.getElementById('searchSuggestions');
    
    console.log('Search triggered with term:', searchTerm);
    
    // Limit search universe to currently filtered (position + project) employees
    const baseCandidates = getEmployeesAfterNonSearchFilters(allEmployees);
    const baseSet = new Set(baseCandidates.map(e => e.human_name));

    if (searchTerm === '') {
        filteredEmployees = baseCandidates;
        suggestionsContainer.classList.remove('show');
        renderEmployees();
        return;
    }
    
    // Use fuzzy search for name matching
    const searchResult = fuzzySearch.search(searchTerm);
    console.log('Search result:', searchResult);
    
    if (searchResult.isTypo && searchResult.results.length === 0) {
        // Show "Did you mean..." suggestions for typos
        showSuggestions(searchTerm, searchResult);
        filteredEmployees = [];
    } else {
        // If there's a perfect match, only show that employee
        if (searchResult.hasPerfectMatch) {
            filteredEmployees = searchResult.results.filter(emp => baseSet.has(emp.human_name));
            suggestionsContainer.classList.remove('show');
        } else {
            // Use fuzzy results + regular text search for other fields
            let fuzzyResults = searchResult.results;
            
            // Also do regular text search for non-name fields (very forgiving)
            const textSearchResults = baseCandidates.filter(employee => {
                // Safely handle projects - check if it's an array or object
                let projectNames = [];
                if (employee.projects) {
                    if (Array.isArray(employee.projects)) {
                        projectNames = employee.projects.map(p => p.name || p.title || '');
                    } else if (typeof employee.projects === 'object') {
                        // Handle object format like {proj_1: {name: "Project 1"}, proj_2: {name: "Project 2"}}
                        projectNames = Object.values(employee.projects).map(p => p.name || p.title || '');
                    }
                }
                
                // Safely handle education
                let educationNames = [];
                if (employee.education && Array.isArray(employee.education)) {
                    educationNames = employee.education.map(edu => edu.institution || '');
                }
                
                // Safely handle memberships
                let memberships = [];
                if (employee.memberships && Array.isArray(employee.memberships)) {
                    memberships = employee.memberships;
                }
                
                const searchableText = [
                    employee.position,
                    employee.office_location,
                    employee.phone,
                    employee.mobile,
                    employee.email,
                    employee.department,
                    employee.team,
                    employee.division,
                    employee.bio,
                    ...projectNames,
                    ...educationNames,
                    ...memberships
                ].join(' ').toLowerCase();
                
                // Very forgiving partial matching for all fields
                const normalizedSearch = searchTerm.toLowerCase().trim();
                const searchWords = normalizedSearch.split(/\s+/).filter(w => w.length > 0);
                
                // Check if search term is contained anywhere
                if (searchableText.includes(normalizedSearch)) {
                    return true;
                }
                
                // Check if any individual word is contained
                if (searchWords.some(word => 
                    word.length > 1 && searchableText.includes(word)
                )) {
                    return true;
                }
                
                // Check for partial word matches (even more forgiving)
                if (searchWords.some(word => 
                    word.length > 2 && searchableText.split(/\s+/).some(textWord => 
                        textWord.includes(word) || word.includes(textWord)
                    )
                )) {
                    return true;
                }
                
                return false;
            });
            
            // Combine and deduplicate results
            // Restrict fuzzy results to base set as well
            const combinedResults = [...fuzzyResults.filter(emp => baseSet.has(emp.human_name)), ...textSearchResults];
            filteredEmployees = combinedResults.filter((employee, index, self) => 
                index === self.findIndex(emp => emp.human_name === employee.human_name)
            );
            
            suggestionsContainer.classList.remove('show');
        }
    }
    
    renderEmployees();
}

function showSuggestions(searchTerm, searchResult) {
    const suggestionsContainer = document.getElementById('searchSuggestions');
    const suggestions = fuzzySearch.generateSuggestions(searchResult);
    
    if (suggestions.length > 0) {
        const suggestionsHTML = `
            <div class="suggestion-header">
                <span class="suggestion-icon">💡</span>
                Did you mean...
            </div>
            <div class="suggestion-list">
                ${suggestions.map(name => `
                    <span class="suggestion-item" onclick="selectSuggestion('${name}')">${name}</span>
                `).join('')}
            </div>
        `;
        suggestionsContainer.innerHTML = suggestionsHTML;
        suggestionsContainer.classList.add('show');
    } else {
        suggestionsContainer.innerHTML = `
            <div class="suggestion-header">
                <span class="suggestion-icon">❌</span>
                No matches found
            </div>
            <div class="no-suggestions">Try a different search term</div>
        `;
        suggestionsContainer.classList.add('show');
    }
}

function selectSuggestion(suggestion) {
    document.getElementById('searchInput').value = suggestion;
    document.getElementById('searchSuggestions').classList.remove('show');
    // Trigger search immediately - this should result in a perfect match
    handleSearch();
}

function applyFilters() {
    // Section visibility toggles
    window.sectionToggles = {
        bio: document.getElementById('toggle_bio')?.checked !== false,
        computer: document.getElementById('toggle_computer')?.checked !== false,
        memberships: document.getElementById('toggle_memberships')?.checked !== false,
        licenses: document.getElementById('toggle_licenses')?.checked !== false,
        years: document.getElementById('toggle_years')?.checked !== false,
        projects: document.getElementById('toggle_projects')?.checked !== false,
        education: document.getElementById('toggle_education')?.checked !== false,
    };

    // Delegate rendering through the search pipeline so search operates on narrowed set
    if (typeof handleSearch === 'function') {
        handleSearch();
    } else {
        // Fallback: render the base filtered set
        const narrowed = getEmployeesAfterNonSearchFilters(allEmployees);
        filteredEmployees = narrowed;
        renderEmployees(narrowed);
    }
}

function getEmployeesAfterNonSearchFilters(employees) {
    let results = Array.isArray(employees) ? employees.slice() : [];

    // Position filter
    if (window.selectedPositions instanceof Set) {
        if (window.selectedPositions.size === 0) {
            return [];
        }
        results = results.filter(emp => {
            const pos = (emp.position || emp.title || '').trim();
            return pos === '' || window.selectedPositions.has(pos);
        });
    }

    // Project filter (AND logic) - only apply when user has selected some projects
    if (window.selectedProjects instanceof Set) {
        if (window.selectedProjects.size === 0) {
            return [];
        }
        const required = Array.from(window.selectedProjects);
        results = results.filter(emp => {
            let projectNames = [];
            if (emp.projects) {
                if (Array.isArray(emp.projects)) {
                    projectNames = emp.projects.map(p => (p && (p.name || p.title)) ? (p.name || p.title) : '').filter(Boolean);
                } else if (typeof emp.projects === 'object') {
                    projectNames = Object.values(emp.projects).map(p => (p && (p.name || p.title)) ? (p.name || p.title) : '').filter(Boolean);
                }
            }
            if (projectNames.length === 0) return false;
            const lowerSet = new Set(projectNames.map(n => n.toLowerCase()));
            return required.every(req => lowerSet.has(req.toLowerCase()));
        });
    }

    return results;
}

// Wire checkbox changes to re-render
document.addEventListener('DOMContentLoaded', function() {
    const ids = ['toggle_bio','toggle_computer','toggle_memberships','toggle_licenses','toggle_years','toggle_projects','toggle_education'];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', applyFilters);
        }
    });
    // Initialize default
    window.sectionToggles = {
        bio: true,
        computer: true,
        memberships: true,
        licenses: true,
        years: true,
        projects: true,
        education: true,
    };

    // Build dynamic position filters when data is loaded
    if (typeof allEmployees !== 'undefined' && Array.isArray(allEmployees) && allEmployees.length > 0) {
        buildPositionFilter(allEmployees);
        buildProjectFilter(allEmployees);
    }
    window.addEventListener('EmployeesLoaded', () => {
        if (typeof allEmployees !== 'undefined' && Array.isArray(allEmployees) && allEmployees.length > 0) {
            buildPositionFilter(allEmployees);
            buildProjectFilter(allEmployees);
            applyFilters();
        }
    });
});

function buildPositionFilter(employees) {
    const container = document.getElementById('positionFilterOptions');
    const selectAll = document.getElementById('positionSelectAll');
    if (!container) return;

    // Collect unique positions from employees.json (position or title), case-insensitive
    const seenLowerToDisplay = new Map();
    employees.forEach(e => {
        const raw = (e && (e.position || e.title) || '').trim();
        if (!raw) return;
        const lower = raw.toLowerCase();
        if (!seenLowerToDisplay.has(lower)) {
            seenLowerToDisplay.set(lower, raw);
        }
    });
    const positions = Array.from(seenLowerToDisplay.values()).sort((a, b) => a.localeCompare(b));

    // Default: all positions selected
    window.selectedPositions = new Set(positions);

    container.innerHTML = positions.map(pos => `
        <label class="pretty-check"><input type="checkbox" class="position-option" value="${pos.replace(/"/g, '&quot;')}" checked> <span>${pos}</span></label>
    `).join('');

    container.querySelectorAll('.position-option').forEach(cb => {
        cb.addEventListener('change', () => {
            if (cb.checked) {
                window.selectedPositions.add(cb.value);
            } else {
                window.selectedPositions.delete(cb.value);
            }
            // Update select all state
            if (selectAll) {
                selectAll.checked = window.selectedPositions.size === positions.length;
            }
            applyFilters();
        });
    });

    if (selectAll) {
        selectAll.checked = true;
        selectAll.addEventListener('change', () => {
            const check = !!selectAll.checked;
            window.selectedPositions = new Set(check ? positions : []);
            container.querySelectorAll('.position-option').forEach(cb => { cb.checked = check; });
            applyFilters();
        });
    }

    const selectNoneBtn = document.getElementById('positionSelectNone');
    if (selectNoneBtn) {
        selectNoneBtn.addEventListener('click', () => {
            // Uncheck all and hide all employees
            window.selectedPositions = new Set();
            container.querySelectorAll('.position-option').forEach(cb => { cb.checked = false; });
            if (selectAll) selectAll.checked = false;
            applyFilters();
        });
    }
}

function buildProjectFilter(employees) {
    const container = document.getElementById('projectFilterOptions');
    const selectNoneBtn = document.getElementById('projectSelectNone');
    if (!container) return;

    // Collect unique project names across all employees (support array or object shape),
    // dedupe case-insensitively while preserving original display casing
    const seenLowerToDisplay = new Map();
    employees.forEach(e => {
        if (!e || !e.projects) return;
        const pushName = (val) => {
            if (!val) return;
            const trimmed = String(val).trim();
            if (!trimmed) return;
            const lower = trimmed.toLowerCase();
            if (!seenLowerToDisplay.has(lower)) {
                seenLowerToDisplay.set(lower, trimmed);
            }
        };
        if (Array.isArray(e.projects)) {
            e.projects.forEach(p => pushName(p && (p.name || p.title)));
        } else if (typeof e.projects === 'object') {
            Object.values(e.projects).forEach(p => pushName(p && (p.name || p.title)));
        }
    });
    const projects = Array.from(seenLowerToDisplay.values()).sort((a, b) => a.localeCompare(b));

    // Default: do not apply any project filter until user interacts
    window.selectedProjects = null; // null => no project filter applied

    container.innerHTML = projects.map(name => `
        <label class="pretty-check"><input type="checkbox" class="project-option" value="${name.replace(/"/g, '&quot;')}"> <span>${name}</span></label>
    `).join('');

    container.querySelectorAll('.project-option').forEach(cb => {
        cb.addEventListener('change', () => {
            if (!(window.selectedProjects instanceof Set)) {
                window.selectedProjects = new Set();
            }
            if (cb.checked) {
                window.selectedProjects.add(cb.value);
            } else {
                window.selectedProjects.delete(cb.value);
            }
            applyFilters();
        });
    });

    if (selectNoneBtn) {
        selectNoneBtn.addEventListener('click', () => {
            window.selectedProjects = new Set();
            container.querySelectorAll('.project-option').forEach(cb => { cb.checked = false; });
            applyFilters();
        });
    }
}
