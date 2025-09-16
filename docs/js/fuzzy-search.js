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

    // Calculate advanced similarity with multiple strategies
    calculateAdvancedSimilarity(searchTerm, employeeName) {
        const normalizedSearch = this.normalize(searchTerm);
        const normalizedName = this.normalize(employeeName);
        
        // Strategy 1: Exact match
        if (normalizedSearch === normalizedName) {
            return 1.0;
        }
        
        // Strategy 2: Substring match (partial match)
        if (normalizedName.includes(normalizedSearch) || normalizedSearch.includes(normalizedName)) {
            return 0.9;
        }
        
        // Strategy 3: Word-based matching (handles name order issues)
        const searchWords = normalizedSearch.split(/\s+/).filter(w => w.length > 0);
        const nameWords = normalizedName.split(/\s+/).filter(w => w.length > 0);
        
        if (searchWords.length > 0 && nameWords.length > 0) {
            // Check if all search words are found in name words
            const allWordsFound = searchWords.every(searchWord => 
                nameWords.some(nameWord => 
                    nameWord.includes(searchWord) || searchWord.includes(nameWord)
                )
            );
            
            if (allWordsFound) {
                return 0.85;
            }
            
            // Check if most search words are found
            const foundWords = searchWords.filter(searchWord => 
                nameWords.some(nameWord => 
                    nameWord.includes(searchWord) || searchWord.includes(nameWord)
                )
            ).length;
            
            if (foundWords > 0) {
                return 0.7 + (foundWords / searchWords.length) * 0.15;
            }
        }
        
        // Strategy 4: Fuzzy matching with Levenshtein distance
        const fuzzyScore = this.calculateSimilarity(normalizedSearch, normalizedName);
        
        // Strategy 5: First letter matching (for very short searches)
        if (normalizedSearch.length >= 2) {
            const searchFirst = normalizedSearch.charAt(0);
            const nameFirst = normalizedName.charAt(0);
            if (searchFirst === nameFirst) {
                return Math.max(fuzzyScore, 0.6);
            }
        }
        
        return fuzzyScore;
    }

    // Check if search term looks like a typo
    isLikelyTypo(searchTerm, matches) {
        const normalizedSearch = this.normalize(searchTerm);
        
        // If we have exact matches, probably not a typo
        if (matches.some(match => match.isExactMatch)) {
            return false;
        }

        // If search term is very short, probably not a typo
        if (normalizedSearch.length < 2) {
            return false;
        }

        // If best match has similarity < 0.4, likely a typo (very forgiving threshold)
        return matches.length > 0 && matches[0].similarity < 0.4;
    }

    // Get fuzzy search results with suggestions
    search(searchTerm) {
        if (!searchTerm || searchTerm.length < 1) {
            return { results: [], suggestions: [], isTypo: false };
        }

        const matches = [];

        // Find all potential matches with advanced similarity scores
        this.employeeNames.forEach(item => {
            const similarity = this.calculateAdvancedSimilarity(searchTerm, item.name);
            
            // Include matches with similarity > 0.3 (very forgiving threshold)
            if (similarity > 0.3) {
                matches.push({
                    name: item.name,
                    similarity: similarity,
                    employee: item.employee,
                    isExactMatch: similarity >= 0.99,
                    isPartialMatch: similarity >= 0.8 && similarity < 0.99,
                    isWordMatch: similarity >= 0.7 && similarity < 0.8
                });
            }
        });

        // Sort by similarity (highest first), then by match type
        matches.sort((a, b) => {
            if (Math.abs(a.similarity - b.similarity) < 0.01) {
                // If similarity is very close, prioritize exact > partial > word matches
                const typePriority = { isExactMatch: 3, isPartialMatch: 2, isWordMatch: 1 };
                return (typePriority[b.isExactMatch ? 'isExactMatch' : b.isPartialMatch ? 'isPartialMatch' : 'isWordMatch']) - 
                       (typePriority[a.isExactMatch ? 'isExactMatch' : a.isPartialMatch ? 'isPartialMatch' : 'isWordMatch']);
            }
            return b.similarity - a.similarity;
        });

        // Check for perfect match (exact match)
        const perfectMatch = matches.find(match => match.isExactMatch);
        
        if (perfectMatch) {
            // If there's a perfect match, return only that result
            return {
                results: [perfectMatch.employee],
                suggestions: [],
                isTypo: false,
                hasPerfectMatch: true
            };
        }

        // For non-perfect matches, include more results (very forgiving)
        const results = matches.filter(match => match.similarity >= 0.4);
        const suggestions = matches.slice(0, 8); // More suggestions for better UX

        const isTypo = this.isLikelyTypo(searchTerm, matches);

        return {
            results: results.map(match => match.employee),
            suggestions: suggestions,
            isTypo: isTypo,
            hasPerfectMatch: false
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

