// Fuzzy search functionality
function handleSearch() {
    const searchTerm = document.getElementById('searchInput').value;
    const suggestionsContainer = document.getElementById('searchSuggestions');
    
    if (searchTerm === '') {
        filteredEmployees = [...allEmployees];
        suggestionsContainer.classList.remove('show');
        return;
    }
    
    // Use fuzzy search for name matching
    const searchResult = fuzzySearch.search(searchTerm);
    
    if (searchResult.isTypo && searchResult.results.length === 0) {
        // Show "Did you mean..." suggestions for typos
        showSuggestions(searchTerm, searchResult);
        filteredEmployees = [];
    } else {
        // Use fuzzy results + regular text search for other fields
        let fuzzyResults = searchResult.results;
        
        // Also do regular text search for non-name fields
        const textSearchResults = allEmployees.filter(employee => {
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
                ...(employee.projects || []).map(p => p.name || p.title || ''),
                ...(employee.education || []).map(edu => edu.institution || ''),
                ...(employee.memberships || [])
            ].join(' ').toLowerCase();
            
            return searchableText.includes(searchTerm.toLowerCase());
        });
        
        // Combine and deduplicate results
        const combinedResults = [...fuzzyResults, ...textSearchResults];
        filteredEmployees = combinedResults.filter((employee, index, self) => 
            index === self.findIndex(emp => emp.real_name === employee.real_name)
        );
        
        suggestionsContainer.classList.remove('show');
    }
    
    applyFilters();
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
    handleSearch();
}

function applyFilters() {
    // Simple search - just render the filtered results
    renderEmployees(filteredEmployees);
}
