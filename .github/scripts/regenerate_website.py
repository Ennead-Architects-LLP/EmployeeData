#!/usr/bin/env python3
"""
Script to regenerate the website HTML with updated computer data
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

def load_employee_data():
    """Load existing employee data from individual JSON files"""
    try:
        # Load the index file to get list of employee files
        index_path = Path('assets/individual_employees/index.json')
        if not index_path.exists():
            print("❌ Employee index not found. Please run the main scraper first.")
            return None
        
        with open(index_path, 'r', encoding='utf-8') as f:
            employee_files = json.load(f)
        
        # Load each individual employee file
        employees = []
        for filename in employee_files:
            try:
                employee_path = Path(f'assets/individual_employees/{filename}')
                if employee_path.exists():
                    with open(employee_path, 'r', encoding='utf-8') as f:
                        employee_data = json.load(f)
                        employees.append(employee_data)
            except Exception as e:
                print(f"⚠️  Warning: Could not load {filename}: {e}")
                continue
        
        print(f"✅ Loaded {len(employees)} employees from individual files")
        return employees
        
    except Exception as e:
        print(f"❌ Error loading employee data: {e}")
        return None

def load_computer_data():
    """Load computer data from all_computers.json"""
    try:
        computer_data_file = Path('assets/computer_data/all_computers.json')
        if not computer_data_file.exists():
            print("ℹ️  No computer data available yet")
            return []
        
        with open(computer_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading computer data: {e}")
        return []

def generate_computer_data_html(computer_data):
    """Generate HTML for computer data section"""
    if not computer_data:
        return '''
        <div class="computer-data-section">
            <h2>🖥️ Computer Data Collection</h2>
            <p>Data collected from AboutMe applications across the organization</p>
            <div id="computerDataContainer">
                <div class="no-data-message">No computer data available yet. Data will appear here when users submit their computer information.</div>
            </div>
        </div>
        '''
    
    # Sort by timestamp (newest first)
    sorted_computers = sorted(computer_data, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Generate stats
    unique_computers = len(set(c.get('computer_name', 'Unknown') for c in computer_data))
    unique_users = len(set(c.get('user', 'Unknown') for c in computer_data))
    
    html = f'''
        <div class="computer-data-section">
            <h2>🖥️ Computer Data Collection</h2>
            <p>Data collected from AboutMe applications across the organization</p>
            <div id="computerDataContainer">
                <div class="computer-stats">
                    <div class="stat-item">
                        <span class="stat-number">{len(computer_data)}</span>
                        <span class="stat-label">Total Submissions</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{unique_computers}</span>
                        <span class="stat-label">Unique Computers</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{unique_users}</span>
                        <span class="stat-label">Unique Users</span>
                    </div>
                </div>
                <div class="computer-list">
    '''
    
    # Generate computer cards (show last 10)
    for computer in sorted_computers[:10]:
        data = computer.get('data', {})
        memory_bytes = data.get('Total Physical Memory', 0)
        memory_gb = (memory_bytes / (1024**3)).toFixed(1) if memory_bytes and memory_bytes != 'Unknown' else 'Unknown'
        
        html += f'''
                    <div class="computer-card">
                        <div class="computer-header">
                            <h3>{data.get('Computername', 'Unknown')}</h3>
                            <span class="timestamp">{datetime.fromisoformat(computer.get('timestamp', '')).strftime('%Y-%m-%d %H:%M:%S')}</span>
                        </div>
                        <div class="computer-details">
                            <div class="detail-row">
                                <span class="label">User:</span>
                                <span class="value">{data.get('Name', 'Unknown')} ({data.get('Username', 'Unknown')})</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">OS:</span>
                                <span class="value">{data.get('OS', 'Unknown')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Hardware:</span>
                                <span class="value">{data.get('Manufacturer', 'Unknown')} {data.get('Model', 'Unknown')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">CPU:</span>
                                <span class="value">{data.get('CPU', 'Unknown')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">GPU:</span>
                                <span class="value">{data.get('GPU Name', 'Unknown')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Memory:</span>
                                <span class="value">{memory_gb} GB</span>
                            </div>
                        </div>
                    </div>
        '''
    
    html += '''
                </div>
            </div>
        </div>
    '''
    
    return html

def regenerate_website():
    """Regenerate the website HTML with updated computer data"""
    print("🔄 Regenerating website...")
    
    # Load data
    employee_data = load_employee_data()
    if not employee_data:
        return False
    
    computer_data = load_computer_data()
    
    # Load the existing HTML template
    try:
        with open('static/templates/index.html', 'r', encoding='utf-8') as f:
            html_template = f.read()
    except FileNotFoundError:
        print("❌ HTML template not found at static/templates/index.html")
        return False
    
    # Generate computer data HTML
    computer_data_html = generate_computer_data_html(computer_data)
    
    # Update the HTML with new computer data section
    # Find the computer data section and replace it
    start_marker = '<!-- Computer Data Collection Section -->'
    end_marker = '<!-- Return to Top Button -->'
    
    start_idx = html_template.find(start_marker)
    end_idx = html_template.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        # Replace the computer data section
        before_section = html_template[:start_idx]
        after_section = html_template[end_idx:]
        
        new_html = before_section + computer_data_html + '\n\n        ' + after_section
        
        # Update employee count in header
        employee_count = len(employee_data)
        new_html = new_html.replace('Ennead\'s People (171 employees)', f'Ennead\'s People ({employee_count} employees)')
        
        # Update generation timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_html = new_html.replace('Generated on: 2025-09-12 16:04:20', f'Generated on: {current_time}')
        
        # Write the updated HTML
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(new_html)
        
        print(f"✅ Website regenerated successfully with {len(computer_data)} computer data entries")
        return True
    else:
        print("❌ Could not find computer data section markers in HTML template")
        return False

def main():
    """Main function"""
    print("🚀 Starting website regeneration...")
    
    if regenerate_website():
        print("🎉 Website regeneration complete!")
        return 0
    else:
        print("❌ Website regeneration failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
