// Fuzzy search functionality
function handleSearch() {
    const searchTerm = document.getElementById('searchInput').value;
    const suggestionsContainer = document.getElementById('searchSuggestions');
    
    console.log('Search triggered with term:', searchTerm);
    
    if (searchTerm === '') {
        filteredEmployees = [...allEmployees];
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
            filteredEmployees = searchResult.results;
            suggestionsContainer.classList.remove('show');
        } else {
            // Use fuzzy results + regular text search for other fields
            let fuzzyResults = searchResult.results;
            
            // Also do regular text search for non-name fields (very forgiving)
            const textSearchResults = allEmployees.filter(employee => {
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
            const combinedResults = [...fuzzyResults, ...textSearchResults];
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
    // Simple search - just render the filtered results
    renderEmployees(filteredEmployees);
}
