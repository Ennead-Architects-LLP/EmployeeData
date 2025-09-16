"""
HTML Report Generator for Employee Data
Creates a beautiful, interactive HTML report with search functionality.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging


class HTMLReportGenerator:
    """
    Generates a beautiful HTML report for employee data with search functionality.
    """
    
    def __init__(self, output_dir: str = "."):
        """
        Initialize the HTML report generator.
        
        Args:
            output_dir: Directory where the HTML report will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, employees_data: List[Dict[str, Any]], 
                       json_file_path: str = None,
                       fetched_at: str = None) -> str:
        """
        Generate a beautiful HTML report from employee data.
        
        Args:
            employees_data: List of employee data dictionaries
            json_file_path: Path to the JSON file (optional)
            
        Returns:
            Path to the generated HTML file
        """
        self.logger.info(f"Generating HTML report for {len(employees_data)} employees")
        
        # Generate HTML content
        html_content = self._generate_html_content(employees_data, fetched_at)
        
        # Save HTML file at root as index.html for GitHub Pages
        html_file_path = self.output_dir / "index.html"
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report generated: {html_file_path}")
        
        # No secondary save location
        
        return str(html_file_path)
    
    def _generate_html_content(self, employees_data: List[Dict[str, Any]], 
                              fetched_at: str = None) -> str:
        """Generate the complete HTML content."""
        
        # Calculate statistics
        stats = self._calculate_statistics(employees_data)
        
        # Generate employee cards HTML
        employee_cards_html = self._generate_employee_cards(employees_data)
        
        # Generate departments list
        departments = self._get_departments(employees_data)
        
        # Generate memberships list
        memberships = self._get_memberships(employees_data)
        
        # Ensure assets directories exist
        assets_dir = self.output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy CSS and JS from static templates
        import shutil
        static_css = Path("static/css/styles.css")
        static_js = Path("static/js/app.js")
        
        if static_css.exists():
            shutil.copy2(static_css, assets_dir / "styles.css")
        else:
            # Fallback to generated CSS if static file doesn't exist
            with open(assets_dir / "styles.css", 'w', encoding='utf-8') as css_file:
                css_file.write(self._get_css_styles())
                
        if static_js.exists():
            shutil.copy2(static_js, assets_dir / "app.js")
        else:
            # Fallback to generated JS if static file doesn't exist
            with open(assets_dir / "app.js", 'w', encoding='utf-8') as js_file:
                js_file.write(self._get_javascript())

        fetched_text = fetched_at or "unknown"
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ennead's People - Employee Directory</title>
    <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
    <!-- Background Slideshow -->
    <div class="slideshow-container">
        <div class="slide active"></div>
        <div class="slide"></div>
        <div class="slide"></div>
        <div class="slide"></div>
        <div class="slide"></div>
    </div>

    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="header-content">
                <h1 class="main-title">Ennead's People ({len(employees_data)} employees)</h1>
                <div class="header-meta">
                    <span class="meta-text">Powered by EnneadTab Ecosystem</span>
                    <span class="meta-text">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                    <span class="meta-text">Data fetched on: {fetched_text}</span>
                </div>
            </div>
        </header>

        <!-- Search and Filters -->
        <div class="search-section">
            <div class="search-container">
                <div class="search-input-wrapper">
                    <img src="https://img.icons8.com/?size=100&id=enn64pGPtmU9&format=png&color=000000" alt="Search" class="search-icon">
                    <input type="text" id="searchInput" placeholder="Search by name, position, location, phone, email, or project..." class="search-input">
                </div>
                <div class="search-suggestions">
                    <span class="suggestion-label">Try searching for:</span>
                    <span class="search-suggestion" onclick="setSearchTerm('New York')">New York</span>
                    <span class="search-suggestion" onclick="setSearchTerm('Shanghai')">Shanghai</span>
                    <span class="search-suggestion" onclick="setSearchTerm('California')">California</span>
                    <span class="search-suggestion" onclick="setSearchTerm('212')">212 (NY area code)</span>
                    <span class="search-suggestion" onclick="setSearchTerm('@ennead.com')">@ennead.com</span>
                </div>
            </div>
            <div class="filter-container">
                <div class="filter-group">
                    <label for="departmentFilter" class="filter-label">Department</label>
                    <select id="departmentFilter" class="filter-select">
                        <option value="">All Departments</option>
                        {self._generate_filter_options(departments)}
                    </select>
                </div>
                <div class="filter-group">
                    <label for="membershipFilter" class="filter-label">Membership</label>
                    <select id="membershipFilter" class="filter-select">
                        <option value="">All Memberships</option>
                        {self._generate_filter_options(memberships)}
                    </select>
                </div>
                <div class="filter-group">
                    <label for="officeLocationFilter" class="filter-label">Office Location</label>
                    <select id="officeLocationFilter" class="filter-select">
                        <option value="">All Locations</option>
                        {self._generate_office_location_options(employees_data)}
                    </select>
                </div>
                <div class="filter-group">
                    <label for="sortBy" class="filter-label">Sort by</label>
                    <select id="sortBy" class="filter-select">
                        <option value="name">Name</option>
                        <option value="position">Position</option>
                        <option value="years">Years with Firm</option>
                        <option value="department">Department</option>
                    </select>
                </div>
                <div class="filter-group">
                    <button id="clearAllFilters" class="clear-all-button">Clear All Filters</button>
                </div>
            </div>
        </div>


        <!-- Employee Cards -->
        <div class="employees-section">
            <div class="section-header">
                <h2>Employee Directory</h2>
                <div class="results-info">
                    <span id="resultsCount">{len(employees_data)} employees found</span>
                </div>
            </div>
            <div id="employeeCards" class="employee-cards-grid">
                {employee_cards_html}
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <div class="footer-content">
                <p>Generated by @ EnneadTab 2025</p>
                <p class="data-sources">Data Sources: Employee contact info from EI, seating info from check-in-website, computer info from IT</p>
            </div>
        </footer>
        
        <!-- Return to Top Button -->
        <button id="returnToTop" class="return-to-top" onclick="scrollToTop()" title="Return to Top">
            <span class="arrow-up">↑</span>
        </button>
    </div>

    <script src="assets/app.js"></script>
</body>
</html>
"""
        return html_content
    
    def _generate_employee_cards(self, employees_data: List[Dict[str, Any]]) -> str:
        """Generate HTML for employee cards."""
        cards_html = []
        
        for employee in employees_data:
            card_html = self._generate_employee_card(employee)
            cards_html.append(card_html)
        
        return '\n'.join(cards_html)
    
    def _generate_employee_card(self, employee: Dict[str, Any]) -> str:
        """Generate HTML for a single employee card."""
        
        # Handle image - prefer local image, fallback to remote URL with error handling
        image_html = ""
        employee_name = employee.get("real_name", "Employee")
        
        if employee.get('image_local_path'):
            # Use local downloaded image
            image_html = f'<img src="{employee["image_local_path"]}" alt="{employee_name}" class="employee-photo">'
        elif employee.get('image_url'):
            # Use remote image URL with error handling for authentication issues
            image_html = f'''<img src="{employee["image_url"]}" 
                              alt="{employee_name}" 
                              class="employee-photo" 
                              onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                           <div class="employee-photo-placeholder" style="display:none;"><i class="icon-user">👤</i></div>'''
        else:
            # Use placeholder
            image_html = '<div class="employee-photo-placeholder"><i class="icon-user">👤</i></div>'
        
        # Handle contact info
        contact_html = ""
        if employee.get('email'):
            contact_html += f'<div class="contact-item"><strong>Email:</strong> <a href="mailto:{employee["email"]}">{employee["email"]}</a></div>'
        if employee.get('phone'):
            contact_html += f'<div class="contact-item"><strong>Phone:</strong> <a href="tel:{employee["phone"]}">{employee["phone"]}</a></div>'
        if employee.get('mobile') and employee['mobile'] != employee.get('phone'):
            contact_html += f'<div class="contact-item"><strong>Mobile:</strong> <a href="tel:{employee["mobile"]}">{employee["mobile"]}</a></div>'
        if employee.get('teams_url'):
            contact_html += f'<div class="contact-item"><strong>Teams:</strong> <a href="{employee["teams_url"]}" target="_blank">Open MS Teams</a></div>'
        
        # Handle memberships
        memberships_html = ""
        if employee.get('memberships'):
            memberships_list = ', '.join(employee['memberships'])
            memberships_html = f'<div class="memberships"><strong>Memberships:</strong> {memberships_list}</div>'
        
        # Handle education
        education_html = ""
        if employee.get('education'):
            education_list = []
            for edu in employee['education']:
                if edu.get('institution'):
                    degree = edu.get('degree', '')
                    specialty = edu.get('specialty', '')
                    edu_text = edu['institution']
                    if degree:
                        edu_text += f' - {degree}'
                    if specialty:
                        edu_text += f' in {specialty}'
                    education_list.append(edu_text)
            if education_list:
                education_html = f'<div class="education"><strong>Education:</strong> {"; ".join(education_list)}</div>'
        
        # Handle projects with expandable section
        projects_html = ""
        if employee.get('projects'):
            project_count = len(employee['projects'])
            project_id = f"projects_{employee.get('profile_id', 'unknown')}"
            
            # Create project list HTML
            project_list_html = ""
            for i, project in enumerate(employee['projects']):
                project_name = project.get('name', 'Unknown Project')
                project_number = project.get('number', '')
                project_client = project.get('client', '')
                project_role = project.get('role', '')
                project_url = project.get('url', '#')
                
                project_details = []
                if project_number:
                    project_details.append(f"<span class='project-number'>#{project_number}</span>")
                if project_client:
                    project_details.append(f"<span class='project-client'>Client: {project_client}</span>")
                if project_role:
                    project_details.append(f"<span class='project-role'>Role: {project_role}</span>")
                
                details_html = f"<div class='project-details'>{' • '.join(project_details)}</div>" if project_details else ""
                
                project_list_html += f"""
                <div class="project-item">
                    <a href="{project_url}" target="_blank" class="project-link">{project_name}</a>
                    {details_html}
                </div>
                """
            
            projects_html = f"""
            <div class="projects">
                <div class="projects-header" onclick="toggleProjects('{project_id}')">
                    <strong>Projects:</strong> {project_count} project{"s" if project_count != 1 else ""}
                    <span class="expand-icon" id="icon_{project_id}">▼</span>
                </div>
                <div class="projects-list" id="{project_id}" style="display: none;">
                    {project_list_html}
                </div>
            </div>
            """
        
        # Handle years with firm
        years_html = ""
        if employee.get('years_with_firm'):
            years_html = f'<div class="years"><strong>Years with Firm:</strong> {employee["years_with_firm"]}</div>'
        
        # Handle computer information
        computer_html = ""
        if employee.get('computer'):
            computer_html = f'<div class="computer"><strong>Computer:</strong> {employee["computer"]}</div>'
        
        # Create searchable data attributes
        searchable_data = []
        searchable_data.append(employee.get('real_name', ''))
        searchable_data.append(employee.get('position', ''))
        searchable_data.append(employee.get('department', ''))
        searchable_data.append(employee.get('computer', ''))
        searchable_data.extend(employee.get('memberships', []))
        searchable_data.extend([edu.get('institution', '') for edu in employee.get('education', [])])
        searchable_data.extend([proj.get('name', '') for proj in employee.get('projects', [])])
        
        # Add location-related search terms for better discoverability
        # Include phone numbers for location search (but don't auto-assign location)
        phone = employee.get('phone', '') or employee.get('mobile', '')
        if phone:
            searchable_data.append(phone)
        
        # Add email for location search
        email = employee.get('email', '')
        if email:
            searchable_data.append(email)
        
        # Add inferred location to searchable text (for search, not auto-assignment)
        inferred_location = self._infer_office_location(employee)
        if inferred_location:
            searchable_data.append(inferred_location)
        
        searchable_text = ' '.join(filter(None, searchable_data))
        
        # Get office location for data attribute
        office_location = employee.get('office_location', '')
        if not office_location or not office_location.strip():
            office_location = self._infer_office_location(employee) or ''
        
        card_html = f"""
        <div class="employee-card" data-searchable="{searchable_text}" data-department="{employee.get('department', '')}" data-memberships="{' '.join(employee.get('memberships', []))}" data-office-location="{office_location}">
            <div class="card-header">
                {image_html}
                <div class="employee-info">
                    <h3 class="employee-name">{employee.get('real_name', 'Unknown')}</h3>
                    <div class="employee-position">{employee.get('position', 'Position not specified')}</div>
                    {f'<div class="employee-department">{employee["department"]}</div>' if employee.get('department') else ''}
                </div>
            </div>
            <div class="card-content">
                {contact_html}
                {years_html}
                {computer_html}
                {memberships_html}
                {education_html}
                {projects_html}
            </div>
            <div class="card-footer">
                <a href="{employee.get('profile_url', '#')}" target="_blank" class="profile-link">View Full Profile</a>
            </div>
        </div>
        """
        
        return card_html
    
    def _calculate_statistics(self, employees_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate statistics from employee data."""
        stats = {
            'total_employees': len(employees_data),
            'employees_with_images': sum(1 for emp in employees_data if emp.get('image_url') or emp.get('image_local_path')),
            'employees_with_emails': sum(1 for emp in employees_data if emp.get('email')),
            'employees_with_phones': sum(1 for emp in employees_data if emp.get('phone') or emp.get('mobile')),
            'employees_with_projects': sum(1 for emp in employees_data if emp.get('projects')),
            'total_projects': sum(len(emp.get('projects', [])) for emp in employees_data)
        }
        return stats
    
    def _get_departments(self, employees_data: List[Dict[str, Any]]) -> List[str]:
        """Get unique departments from employee data."""
        departments = set()
        for employee in employees_data:
            if employee.get('department'):
                departments.add(employee['department'])
        return sorted(list(departments))
    
    def _get_memberships(self, employees_data: List[Dict[str, Any]]) -> List[str]:
        """Get unique memberships from employee data."""
        memberships = set()
        for employee in employees_data:
            for membership in employee.get('memberships', []):
                memberships.add(membership)
        return sorted(list(memberships))
    
    def _generate_filter_options(self, items: List[str]) -> str:
        """Generate HTML options for filter dropdowns."""
        options = []
        for item in items:
            options.append(f'<option value="{item}">{item}</option>')
        return '\n'.join(options)
    
    def _get_office_locations(self, employees_data: List[Dict[str, Any]]) -> List[str]:
        """Get unique office locations from employee data."""
        office_locations = set()
        for employee in employees_data:
            # Try to get office location from the data
            office_location = employee.get('office_location', '')
            if office_location and office_location.strip():
                office_locations.add(office_location.strip())
            else:
                # Try to infer office location from other data
                inferred_location = self._infer_office_location(employee)
                if inferred_location:
                    office_locations.add(inferred_location)
        
        # Add common office locations if none found
        if not office_locations:
            office_locations = {'New York', 'California', 'Shanghai'}
        
        return sorted(list(office_locations))
    
    def _infer_office_location(self, employee: Dict[str, Any]) -> str:
        """Try to infer office location from other employee data (excluding phone area codes)."""
        
        # Check email domain patterns (more reliable than phone area codes)
        email = employee.get('email', '')
        if email:
            if 'shanghai' in email.lower():
                return 'Shanghai'
            elif 'ny' in email.lower() or 'newyork' in email.lower():
                return 'New York'
            elif 'ca' in email.lower() or 'california' in email.lower():
                return 'California'
        
        # Check project locations (can indicate office location)
        projects = employee.get('projects', [])
        for project in projects:
            project_name = project.get('name', '').lower()
            if any(location in project_name for location in ['shanghai', 'china', 'beijing']):
                return 'Shanghai'
            elif any(location in project_name for location in ['california', 'los angeles', 'san francisco']):
                return 'California'
            elif any(location in project_name for location in ['new york', 'nyc', 'manhattan']):
                return 'New York'
        
        return None
    
    def _generate_office_location_options(self, employees_data: List[Dict[str, Any]]) -> str:
        """Generate HTML options for office location filter with counts."""
        office_locations = self._get_office_locations(employees_data)
        
        # Count employees for each location
        location_counts = {}
        for employee in employees_data:
            # Get office location (inferred if not available)
            office_location = employee.get('office_location', '')
            if not office_location or not office_location.strip():
                office_location = self._infer_office_location(employee) or 'Unknown'
            
            location_counts[office_location] = location_counts.get(office_location, 0) + 1
        
        # Generate options with counts
        options = []
        for location in office_locations:
            count = location_counts.get(location, 0)
            if count > 0:
                options.append(f'<option value="{location}">{location} ({count})</option>')
        
        return '\n'.join(options)
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the HTML report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
            color: #ffffff;
            line-height: 1.6;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }

        /* Background Slideshow Styles */
        .slideshow-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
        }

        .slide {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            opacity: 0;
            transition: opacity 3s ease-in-out;
        }

        .slide.active {
            opacity: 0.15; /* Very subtle background effect */
        }

        .slide:nth-child(1) {
            background-image: url('https://static.designboom.com/wp-content/uploads/2022/07/new-milwaukee-public-museum-by-ennead-architects-and-kahler-slater-designboom-02.jpg');
        }

        .slide:nth-child(2) {
            background-image: url('https://www.archpaper.com/wp-content/uploads/2021/07/01_Shanghai-Astronomy-Museum_Aerial_Photo-by-ArchExists-1-scaled.jpg');
        }

        .slide:nth-child(3) {
            background-image: url('https://archinect.gumlet.io/uploads/77/7716e6676923bf8785e6b1c7dbf79493.jpg?auto=compress%2Cformat');
        }

        .slide:nth-child(4) {
            background-image: url('https://visualatelier8.com/wp-content/uploads/2019/03/Yangtze-River-Estuary-Chinese-Sturgeon-Nature-Preserve-Ennead-Visual-Atelier-8-Architecture-11.jpg');
        }

        .slide:nth-child(5) {
            background-image: url('https://images.adsttc.com/media/images/57c9/46c4/e58e/cebf/2400/0027/medium_jpg/ACLS_NW_Corner.jpg?1472808637');
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #4CAF50, #2196F3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header-meta {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }

        .meta-text {
            color: #b0b0b0;
            font-size: 0.9rem;
        }

        .search-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .search-container {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            align-items: center;
        }

        /* Old search styles removed - using simple design below */

        .filter-container {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .filter-select {
            padding: 12px 15px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .filter-select:focus {
            outline: none;
            border-color: #4CAF50;
        }

        .filter-select option {
            background: #2d2d2d;
            color: #ffffff;
        }

        .stats-section {
            margin-bottom: 30px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #4CAF50;
            margin-bottom: 10px;
        }

        .stat-label {
            color: #b0b0b0;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .employees-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .section-header h2 {
            font-size: 1.8rem;
            color: #4CAF50;
        }

        .results-info {
            color: #b0b0b0;
            font-size: 0.9rem;
        }

        .employee-cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
        }

        .employee-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .employee-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
            border-color: #4CAF50;
        }

        .card-header {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            align-items: flex-start;
        }

        .employee-photo {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #4CAF50;
        }

        .employee-photo-placeholder {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            border: 3px solid #4CAF50;
            font-size: 2rem;
        }

        .employee-info {
            flex: 1;
        }

        .employee-name {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 5px;
            color: #ffffff;
        }

        .employee-position {
            color: #4CAF50;
            font-weight: 500;
            margin-bottom: 5px;
        }

        .employee-department {
            color: #b0b0b0;
            font-size: 0.9rem;
        }

        .card-content {
            margin-bottom: 20px;
        }

        .contact-item, .memberships, .education, .projects, .years, .computer {
            margin-bottom: 10px;
            font-size: 0.9rem;
        }

        /* Simple Search Bar Design */
        .search-input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
            background: white;
            border: 2px solid #2196F3;
            border-radius: 25px;
            padding: 0;
            max-width: 400px;
            margin: 0 auto;
        }

        .search-icon {
            width: 20px;
            height: 20px;
            padding: 12px 15px;
            opacity: 0.7;
        }

        .search-input {
            flex: 1;
            border: none;
            padding: 12px 15px 12px 0;
            font-size: 16px;
            background: transparent;
            outline: none;
            color: #333;
        }

        .search-input::placeholder {
            color: #999;
        }

        .search-suggestions {
            margin-top: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }

        .suggestion-label {
            color: #666;
            font-size: 0.9rem;
            font-weight: 500;
        }

        .search-suggestion {
            background: #f8f9fa;
            color: #495057;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            cursor: pointer;
            border: 1px solid #dee2e6;
            transition: all 0.2s ease;
        }

        .search-suggestion:hover {
            background: #e9ecef;
            border-color: #007bff;
            color: #007bff;
        }

        .clear-button {
            display: none;
            border: none;
            padding: 10px 15px;
            cursor: pointer;
            font-size: 18px;
            color: #6c757d;
            transition: all 0.3s ease;
        }

        .clear-button:hover {
            background: #e9ecef;
            color: #495057;
        }

        .filter-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
        }

        .filter-label {
            font-weight: 600;
            margin-bottom: 8px;
            color: #495057;
            font-size: 14px;
        }

        .filter-select {
            padding: 12px 15px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            transition: all 0.3s ease;
        }

        .filter-select:focus {
            border-color: #007bff;
            outline: none;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
        }

        .clear-all-button {
            background: #6c757d;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
            align-self: end;
        }

        .clear-all-button:hover {
            background: #5a6268;
            transform: translateY(-1px);
        }

        /* Expandable Projects Styles */
        .projects-header {
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            transition: all 0.3s ease;
        }

        .projects-header:hover {
            color: #007bff;
        }

        .expand-icon {
            transition: transform 0.3s ease;
            font-size: 12px;
        }

        .expand-icon.expanded {
            transform: rotate(180deg);
        }

        .projects-list {
            margin-top: 10px;
            padding-left: 15px;
            border-left: 2px solid #e9ecef;
        }

        .project-item {
            margin-bottom: 12px;
            padding: 8px 0;
        }

        .project-link {
            color: #ffffff;
            text-decoration: none;
            font-weight: 500;
            display: block;
            margin-bottom: 4px;
        }

        .project-link:hover {
            color: #4CAF50;
            text-decoration: underline;
        }

        .project-details {
            font-size: 0.85rem;
            color: #6c757d;
            margin-top: 4px;
        }

        .project-number {
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.8rem;
        }

        .project-client, .project-role {
            font-style: italic;
        }

        .contact-item a {
            color: #4CAF50;
            text-decoration: none;
        }

        .contact-item a:hover {
            text-decoration: underline;
        }

        .card-footer {
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            padding-top: 15px;
        }

        .profile-link {
            display: inline-block;
            padding: 10px 20px;
            background: linear-gradient(45deg, #4CAF50, #2196F3);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .profile-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
        }

        .footer {
            margin-top: 50px;
            text-align: center;
            color: #b0b0b0;
            font-size: 0.9rem;
        }

        .footer-content p {
            margin-bottom: 5px;
        }

        .data-sources {
            font-size: 0.8rem;
            color: #888;
            font-style: italic;
            margin-top: 10px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }

            .main-title {
                font-size: 2rem;
            }

            .search-container {
                flex-direction: column;
            }

            .filter-container {
                flex-direction: column;
            }

            .employee-cards-grid {
                grid-template-columns: 1fr;
            }

            .card-header {
                flex-direction: column;
                text-align: center;
            }

            .stats-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
        }

        /* Animation for search results */
        .employee-card.hidden {
            display: none;
        }

        .employee-card.fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Return to Top Button */
        .return-to-top {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #4a90e2, #357abd);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
            transition: all 0.3s ease;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transform: translateY(20px);
        }

        .return-to-top.show {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }

        .return-to-top:hover {
            background: linear-gradient(135deg, #357abd, #2c5aa0);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
        }

        .return-to-top:active {
            transform: translateY(0);
        }

        .arrow-up {
            display: block;
            line-height: 1;
        }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for search and filter functionality."""
        return """
        // Function to toggle project expansion
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

        // Function to set search term from suggestions
        function setSearchTerm(term) {
            const searchInput = document.getElementById('searchInput');
            searchInput.value = term;
            searchInput.focus();
            // Trigger the search
            const event = new Event('input', { bubbles: true });
            searchInput.dispatchEvent(event);
        }

        // Background Slideshow Class
        class BackgroundSlideshow {
            constructor() {
                this.slides = document.querySelectorAll('.slide');
                this.currentSlide = 0;
                this.slideInterval = 8000; // 8 seconds per slide
                this.interval = null;
                this.isPlaying = true;
                
                this.init();
            }

            init() {
                this.startSlideshow();
                
                // Pause on hover for better user experience
                document.addEventListener('mouseenter', () => {
                    if (this.isPlaying) {
                        this.pauseSlideshow();
                    }
                });
                
                document.addEventListener('mouseleave', () => {
                    if (this.isPlaying) {
                        this.startSlideshow();
                    }
                });
            }

            startSlideshow() {
                this.interval = setInterval(() => {
                    this.nextSlide();
                }, this.slideInterval);
            }

            pauseSlideshow() {
                clearInterval(this.interval);
            }

            nextSlide() {
                this.slides[this.currentSlide].classList.remove('active');
                this.currentSlide = (this.currentSlide + 1) % this.slides.length;
                this.slides[this.currentSlide].classList.add('active');
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            // Initialize background slideshow
            new BackgroundSlideshow();
            
            const searchInput = document.getElementById('searchInput');
            const clearAllButton = document.getElementById('clearAllFilters');
            const departmentFilter = document.getElementById('departmentFilter');
            const membershipFilter = document.getElementById('membershipFilter');
            const officeLocationFilter = document.getElementById('officeLocationFilter');
            const sortBy = document.getElementById('sortBy');
            const employeeCards = document.getElementById('employeeCards');
            const resultsCount = document.getElementById('resultsCount');
            
            let allCards = Array.from(document.querySelectorAll('.employee-card'));
            
            function filterAndSearch() {
                const searchTerm = searchInput.value.toLowerCase();
                const selectedDepartment = departmentFilter.value;
                const selectedMembership = membershipFilter.value;
                const selectedOfficeLocation = officeLocationFilter.value;
                const sortOption = sortBy.value;
                
                let filteredCards = allCards.filter(card => {
                    const searchableText = card.getAttribute('data-searchable').toLowerCase();
                    const department = card.getAttribute('data-department');
                    const memberships = card.getAttribute('data-memberships').toLowerCase();
                    const officeLocation = card.getAttribute('data-office-location');
                    
                    const matchesSearch = searchableText.includes(searchTerm);
                    const matchesDepartment = !selectedDepartment || department === selectedDepartment;
                    const matchesMembership = !selectedMembership || memberships.includes(selectedMembership.toLowerCase());
                    const matchesOfficeLocation = !selectedOfficeLocation || officeLocation === selectedOfficeLocation;
                    
                    return matchesSearch && matchesDepartment && matchesMembership && matchesOfficeLocation;
                });
                
                // Sort cards
                filteredCards.sort((a, b) => {
                    switch(sortOption) {
                        case 'name':
                            return a.querySelector('.employee-name').textContent.localeCompare(b.querySelector('.employee-name').textContent);
                        case 'position':
                            return a.querySelector('.employee-position').textContent.localeCompare(b.querySelector('.employee-position').textContent);
                        case 'years':
                            const yearsA = parseInt(a.querySelector('.years')?.textContent.match(/\\d+/)?.[0] || '0');
                            const yearsB = parseInt(b.querySelector('.years')?.textContent.match(/\\d+/)?.[0] || '0');
                            return yearsB - yearsA;
                        case 'department':
                            const deptA = a.getAttribute('data-department') || '';
                            const deptB = b.getAttribute('data-department') || '';
                            return deptA.localeCompare(deptB);
                        default:
                            return 0;
                    }
                });
                
                // Update display
                allCards.forEach(card => {
                    if (filteredCards.includes(card)) {
                        card.classList.remove('hidden');
                        card.classList.add('fade-in');
                    } else {
                        card.classList.add('hidden');
                        card.classList.remove('fade-in');
                    }
                });
                
                // Update results count
                resultsCount.textContent = `${filteredCards.length} employee${filteredCards.length !== 1 ? 's' : ''} found`;
            }
            
            // Event listeners
            searchInput.addEventListener('input', filterAndSearch);
            
            clearAllButton.addEventListener('click', function() {
                searchInput.value = '';
                departmentFilter.value = '';
                membershipFilter.value = '';
                officeLocationFilter.value = '';
                sortBy.value = 'name';
                filterAndSearch();
            });
            
            departmentFilter.addEventListener('change', filterAndSearch);
            membershipFilter.addEventListener('change', filterAndSearch);
            officeLocationFilter.addEventListener('change', filterAndSearch);
            sortBy.addEventListener('change', filterAndSearch);
            
            // Initial filter
            filterAndSearch();
            
            // Return to Top Button functionality
            const returnToTopButton = document.getElementById('returnToTop');
            
            // Show/hide button based on scroll position
            window.addEventListener('scroll', function() {
                if (window.pageYOffset > 300) {
                    returnToTopButton.classList.add('show');
                } else {
                    returnToTopButton.classList.remove('show');
                }
            });
        });
        
        // Function to scroll to top
        function scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
        """
    
    def generate_from_json_file(self, json_file_path: str) -> str:
        """
        Generate HTML report from a JSON file.
        
        Args:
            json_file_path: Path to the JSON file containing employee data
            
        Returns:
            Path to the generated HTML file
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            fetched_at = None
            if isinstance(data, dict) and 'employees' in data:
                # New structure with metadata and employees array
                employees_data = data['employees']
                try:
                    fetched_at = data.get('metadata', {}).get('scraped_at')
                except Exception:
                    fetched_at = None
            elif isinstance(data, list):
                # Direct array of employees
                employees_data = data
            else:
                raise ValueError("Invalid JSON structure: expected list of employees or dict with 'employees' key")
            
            return self.generate_report(employees_data, json_file_path, fetched_at)
        except Exception as e:
            self.logger.error(f"Error generating report from JSON file: {e}")
            raise


def generate_employee_directory_html(json_file_path: str, output_dir: str = ".") -> str:
    """
    Convenience function to generate HTML report from JSON file.
    
    Args:
        json_file_path: Path to the JSON file containing employee data
        output_dir: Directory where the HTML report will be saved
        
    Returns:
        Path to the generated HTML file
    """
    generator = HTMLReportGenerator(output_dir)
    return generator.generate_from_json_file(json_file_path)


if __name__ == "__main__":
    # Test the HTML generator
    import sys
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        html_file = generate_employee_directory_html(json_file)
        print(f"HTML report generated: {html_file}")
    else:
        print("Usage: python html_report_generator.py <json_file_path>")
