// Fuzzy search with typo correction and suggestions
class FuzzySearch {
    constructor() {
        this.employeeNames = [];
        this.searchHistory = [];
    }

    initialize(employees) {
        // Extract all employee names for fuzzy matching
        this.employeeNames = employees.map(emp => ({
            name: emp.human_name,
            normalized: this.normalize(emp.human_name),
            employee: emp
        }));
    }

    normalize(text) {
        return text.toLowerCase()
            .replace(/[^\w\s]/g, '') // Remove special characters
            .replace(/\s+/g, ' ')    // Normalize whitespace
            .trim();
    }

    // Calculate Levenshtein distance for fuzzy matching
    levenshteinDistance(str1, str2) {
        const matrix = [];
        const len1 = str1.length;
        const len2 = str2.length;

        for (let i = 0; i <= len2; i++) {
            matrix[i] = [i];
        }

        for (let j = 0; j <= len1; j++) {
            matrix[0][j] = j;
        }

        for (let i = 1; i <= len2; i++) {
            for (let j = 1; j <= len1; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1, // substitution
                        matrix[i][j - 1] + 1,     // insertion
                        matrix[i - 1][j] + 1      // deletion
                    );
                }
            }
        }

        return matrix[len2][len1];
    }

    // Calculate similarity score (0-1, higher is better)
    calculateSimilarity(str1, str2) {
        const distance = this.levenshteinDistance(str1, str2);
        const maxLength = Math.max(str1.length, str2.length);
        return maxLength === 0 ? 1 : (maxLength - distance) / maxLength;
    }

    // Check if search term looks like a typo
    isLikelyTypo(searchTerm, matches) {
        const normalizedSearch = this.normalize(searchTerm);
        
        // If we have exact matches, probably not a typo
        if (matches.some(match => match.similarity === 1)) {
            return false;
        }

        // If search term is very short, probably not a typo
        if (normalizedSearch.length < 3) {
            return false;
        }

        // If best match has similarity < 0.7, likely a typo
        return matches.length > 0 && matches[0].similarity < 0.7;
    }

    // Get fuzzy search results with suggestions
    search(searchTerm) {
        if (!searchTerm || searchTerm.length < 2) {
            return { results: [], suggestions: [], isTypo: false };
        }

        const normalizedSearch = this.normalize(searchTerm);
        const matches = [];

        // Find all potential matches with similarity scores
        this.employeeNames.forEach(item => {
            const similarity = this.calculateSimilarity(normalizedSearch, item.normalized);
            
            // Include matches with similarity > 0.3
            if (similarity > 0.3) {
                matches.push({
                    name: item.name,
                    similarity: similarity,
                    employee: item.employee
                });
            }
        });

        // Sort by similarity (highest first)
        matches.sort((a, b) => b.similarity - a.similarity);

        // Separate exact/close matches from suggestions
        const results = matches.filter(match => match.similarity >= 0.7);
        const suggestions = matches.slice(0, 5); // Top 5 suggestions

        const isTypo = this.isLikelyTypo(searchTerm, matches);

        return {
            results: results.map(match => match.employee),
            suggestions: suggestions,
            isTypo: isTypo
        };
    }

    // Generate "Did you mean..." suggestions
    generateSuggestions(searchResult) {
        if (!searchResult.isTypo || searchResult.suggestions.length === 0) {
            return [];
        }

        const topSuggestions = searchResult.suggestions.slice(0, 3);
        return topSuggestions.map(suggestion => suggestion.name);
    }
}

// Global fuzzy search instance
const fuzzySearch = new FuzzySearch();
