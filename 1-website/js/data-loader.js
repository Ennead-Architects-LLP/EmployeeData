// Dynamic Data Loader for Employee Directory
// This script loads employee and computer data from JSON files

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
        // Load employee data
        await loadEmployeeData();
        
        // Computer data is now merged into individual employee files
        
        // Initialize UI
        initializeUI();
        
        // Hide loading indicator
        document.getElementById('loadingIndicator').style.display = 'none';
        
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Failed to load data. Please refresh the page.');
    }
}

async function loadEmployeeData() {
    try {
        // Load the index file to get list of employee files
        const indexResponse = await fetch('assets/individual_employees/index.json');
        if (!indexResponse.ok) {
            throw new Error('Failed to load employee index');
        }
        
        const employeeFiles = await indexResponse.json();
        console.log('Found employee files:', employeeFiles.length);
        
        // Load each individual employee file
        const employeePromises = employeeFiles.map(async (filename) => {
            try {
                const response = await fetch(`assets/individual_employees/${filename}`);
                if (response.ok) {
                    return await response.json();
                }
                return null;
            } catch (error) {
                console.warn(`Failed to load ${filename}:`, error);
                return null;
            }
        });
        
        const employeeResults = await Promise.all(employeePromises);
        allEmployees = employeeResults.filter(emp => emp !== null);
        filteredEmployees = [...allEmployees];
        
        console.log('Loaded employees:', allEmployees.length);
        console.log('Sample employee:', allEmployees[0]);
        
        // Initialize fuzzy search
        fuzzySearch.initialize(allEmployees);
        
        // Update header with employee count
        document.getElementById('mainTitle').textContent = `Ennead's People (${allEmployees.length} employees)`;
        
        // Update generation time
        const now = new Date();
        document.getElementById('generatedTime').textContent = `Generated on: ${now.toLocaleString()}`;
        
        // Update data time (use current time as fallback)
        document.getElementById('dataTime').textContent = `Data fetched on: ${now.toISOString()}`;
        
    } catch (error) {
        console.error('Error loading employee data:', error);
        // Fallback to consolidated file if individual files fail
        await loadFallbackEmployeeData();
    }
}

async function loadFallbackEmployeeData() {
    try {
        const response = await fetch('assets/employees_data.json');
        if (!response.ok) {
            throw new Error('Failed to load fallback employee data');
        }
        const data = await response.json();
        allEmployees = data.employees || data;
        filteredEmployees = [...allEmployees];
        
        console.log('Loaded fallback employees:', allEmployees.length);
        
        // Update header with employee count
        document.getElementById('mainTitle').textContent = `Ennead's People (${allEmployees.length} employees)`;
        
        // Update generation time
        const now = new Date();
        document.getElementById('generatedTime').textContent = `Generated on: ${now.toLocaleString()}`;
        document.getElementById('dataTime').textContent = `Data fetched on: ${now.toISOString()}`;
        
    } catch (error) {
        console.error('Error loading fallback employee data:', error);
        throw error;
    }
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
            '<div class="no-data-message">No computer specifications submitted yet. Employee computer data will appear here when users submit their system information.</div>';
    }
}

function showError(message) {
    const grid = document.getElementById('employeeGrid');
    grid.innerHTML = `<div class="error-message">${message}</div>`;
}
