#!/usr/bin/env python3
"""
GitHub Actions script to handle computer data from AboutMe app
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def load_computer_data():
    """Load computer data from GitHub event payload"""
    try:
        # Try to get data from repository dispatch event
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        if event_path and os.path.exists(event_path):
            with open(event_path, 'r') as f:
                event_data = json.load(f)
                return event_data.get('client_payload', {}).get('computer_data')
        
        # Fallback: create test data if in test mode
        if os.environ.get('TEST_MODE') == 'true':
            return {
                "Computername": "TEST-COMPUTER",
                "Name": "Test User",
                "Username": "testuser",
                "OS": "Windows 10 Test",
                "Manufacturer": "Test Manufacturer",
                "Model": "Test Model",
                "CPU": "Test CPU",
                "Total Physical Memory": 8589934592,
                "GPU Name": "Test GPU",
                "Serial Number": "TEST123456",
                "Date": datetime.now().isoformat()
            }
        
        return None
    except Exception as e:
        print(f"Error loading computer data: {e}")
        return None

def find_employee_by_name(employees, name):
    """Find employee by name (fuzzy matching)"""
    if not name:
        return None
    
    name_lower = name.lower().strip()
    
    # Exact match first
    for emp in employees:
        if emp.get('real_name', '').lower().strip() == name_lower:
            return emp
    
    # Partial match
    for emp in employees:
        emp_name = emp.get('real_name', '').lower().strip()
        if name_lower in emp_name or emp_name in name_lower:
            return emp
    
    return None

def find_employee_by_username(employees, username):
    """Find employee by username (from email)"""
    if not username:
        return None
    
    username_lower = username.lower().strip()
    
    for emp in employees:
        email = emp.get('email', '')
        if email:
            emp_username = email.split('@')[0].lower().strip()
            if emp_username == username_lower:
                return emp
    
    return None

def load_employee_data():
    """Load existing employee data"""
    try:
        with open("1-website/assets/employees_data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('employees', [])
    except FileNotFoundError:
        print("Employee data file not found")
        return []
    except Exception as e:
        print(f"Error loading employee data: {e}")
        return []

def update_individual_employee_file(employee_data, computer_data):
    """Update individual employee JSON file with computer data"""
    try:
        # Find the employee's individual file
        employee_name = employee_data.get('real_name', '').replace(' ', '_')
        individual_file = Path("1-website/assets/individual_employees") / f"{employee_name}.json"
        
        if individual_file.exists():
            # Update the individual file
            with open(individual_file, 'r', encoding='utf-8') as f:
                individual_data = json.load(f)
            
            # Create new computer info entry
            new_computer_info = {
                'computername': computer_data.get('Computername'),
                'os': computer_data.get('OS'),
                'manufacturer': computer_data.get('Manufacturer'),
                'model': computer_data.get('Model'),
                'cpu': computer_data.get('CPU'),
                'gpu_name': computer_data.get('GPU Name'),
                'gpu_driver': computer_data.get('GPU Driver'),
                'memory_bytes': computer_data.get('Total Physical Memory'),
                'serial_number': computer_data.get('Serial Number'),
                'last_updated': datetime.now().isoformat()
            }
            
            # Handle computer_info as a list
            if 'computer_info' not in individual_data:
                individual_data['computer_info'] = []
            elif not isinstance(individual_data['computer_info'], list):
                # Convert existing single dict to list if needed
                individual_data['computer_info'] = [individual_data['computer_info']]
            
            # Check if this computer already exists (by computername and serial number)
            computer_exists = False
            for i, existing_computer in enumerate(individual_data['computer_info']):
                if (existing_computer.get('computername') == new_computer_info.get('computername') and 
                    existing_computer.get('serial_number') == new_computer_info.get('serial_number')):
                    # Update existing entry
                    individual_data['computer_info'][i] = new_computer_info
                    computer_exists = True
                    print(f"Updated existing computer entry for {new_computer_info.get('computername')}")
                    break
            
            if not computer_exists:
                # Add new computer entry
                individual_data['computer_info'].append(new_computer_info)
                print(f"Added new computer entry for {new_computer_info.get('computername')}")
            
            # Save updated individual file
            with open(individual_file, 'w', encoding='utf-8') as f:
                json.dump(individual_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"Updated individual employee file: {individual_file}")
            return True
        else:
            print(f"Individual employee file not found: {individual_file}")
            return False
            
    except Exception as e:
        print(f"Error updating individual employee file: {e}")
        return False

def save_computer_data(data):
    """Save computer data to assets directory and merge with employee records"""
    try:
        # Create computer_data directory
        data_dir = Path("1-website/assets/computer_data")
        data_dir.mkdir(exist_ok=True)
        
        # Generate filename based on computer name and timestamp
        computer_name = data.get('Computername', 'unknown').replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{computer_name}_{timestamp}.json"
        
        # Save individual computer data
        file_path = data_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Saved computer data to {file_path}")
        
        # Update master computer data file
        master_file = data_dir / "all_computers.json"
        all_computers = []
        
        if master_file.exists():
            with open(master_file, 'r', encoding='utf-8') as f:
                all_computers = json.load(f)
        
        # Add new data
        all_computers.append({
            "timestamp": datetime.now().isoformat(),
            "computer_name": data.get('Computername', 'Unknown'),
            "user": data.get('Name', 'Unknown'),
            "data": data
        })
        
        # Keep only last 100 entries to prevent file from growing too large
        all_computers = all_computers[-100:]
        
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(all_computers, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Updated master computer data file: {master_file}")
        
        # Merge computer data with employee records
        employees = load_employee_data()
        if employees:
            # Try to find employee by name first
            user_name = data.get('Name', '')
            username = data.get('Username', '')
            employee = find_employee_by_name(employees, user_name)
            
            # If not found by name, try by username
            if not employee and username:
                employee = find_employee_by_username(employees, username)
            
            if employee:
                # Create new computer info entry
                new_computer_info = {
                    'computername': data.get('Computername'),
                    'os': data.get('OS'),
                    'manufacturer': data.get('Manufacturer'),
                    'model': data.get('Model'),
                    'cpu': data.get('CPU'),
                    'gpu_name': data.get('GPU Name'),
                    'gpu_driver': data.get('GPU Driver'),
                    'memory_bytes': data.get('Total Physical Memory'),
                    'serial_number': data.get('Serial Number'),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Handle computer_info as a list in main employee data
                if 'computer_info' not in employee:
                    employee['computer_info'] = []
                elif not isinstance(employee['computer_info'], list):
                    # Convert existing single dict to list if needed
                    employee['computer_info'] = [employee['computer_info']]
                
                # Check if this computer already exists (by computername and serial number)
                computer_exists = False
                for i, existing_computer in enumerate(employee['computer_info']):
                    if (existing_computer.get('computername') == new_computer_info.get('computername') and 
                        existing_computer.get('serial_number') == new_computer_info.get('serial_number')):
                        # Update existing entry
                        employee['computer_info'][i] = new_computer_info
                        computer_exists = True
                        print(f"Updated existing computer entry in main data for {new_computer_info.get('computername')}")
                        break
                
                if not computer_exists:
                    # Add new computer entry
                    employee['computer_info'].append(new_computer_info)
                    print(f"Added new computer entry to main data for {new_computer_info.get('computername')}")
                
                # Update individual employee file
                update_individual_employee_file(employee, data)
                
                # Save updated employees data
                with open("1-website/assets/employees_data.json", 'w', encoding='utf-8') as f:
                    json.dump({"employees": employees}, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"Updated employee record for {user_name} ({username})")
            else:
                print(f"Could not find employee record for {user_name} ({username})")
        
        return True
        
    except Exception as e:
        print(f"Error saving computer data: {e}")
        return False

def create_summary_html():
    """Create a summary HTML page for computer data"""
    try:
        master_file = Path("1-website/assets/computer_data/all_computers.json")
        if not master_file.exists():
            return
        
        with open(master_file, 'r', encoding='utf-8') as f:
            all_computers = json.load(f)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Computer Data Collection - EmployeeData</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .computer-card {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; background: #fafafa; }}
        .computer-name {{ font-weight: bold; color: #333; font-size: 1.2em; }}
        .computer-info {{ margin: 5px 0; color: #666; }}
        .timestamp {{ color: #999; font-size: 0.9em; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; padding: 20px; background: #e8f4f8; border-radius: 5px; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #2c5aa0; }}
        .stat-label {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ Computer Data Collection</h1>
            <p>Data collected from AboutMe applications</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(all_computers)}</div>
                <div class="stat-label">Total Submissions</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(set(c.get('computer_name', 'Unknown') for c in all_computers))}</div>
                <div class="stat-label">Unique Computers</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(set(c.get('user', 'Unknown') for c in all_computers))}</div>
                <div class="stat-label">Unique Users</div>
            </div>
        </div>
        
        <h2>Recent Submissions</h2>
"""
        
        # Sort by timestamp (newest first)
        sorted_computers = sorted(all_computers, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        for computer in sorted_computers[:20]:  # Show last 20
            data = computer.get('data', {})
            timestamp = computer.get('timestamp', 'Unknown')
            
            html_content += f"""
        <div class="computer-card">
            <div class="computer-name">{data.get('Computername', 'Unknown')}</div>
            <div class="computer-info"><strong>User:</strong> {data.get('Name', 'Unknown')} ({data.get('Username', 'Unknown')})</div>
            <div class="computer-info"><strong>OS:</strong> {data.get('OS', 'Unknown')}</div>
            <div class="computer-info"><strong>Manufacturer:</strong> {data.get('Manufacturer', 'Unknown')} {data.get('Model', 'Unknown')}</div>
            <div class="computer-info"><strong>CPU:</strong> {data.get('CPU', 'Unknown')}</div>
            <div class="computer-info"><strong>GPU:</strong> {data.get('GPU Name', 'Unknown')}</div>
            <div class="computer-info"><strong>Memory:</strong> {data.get('Total Physical Memory', 'Unknown')} bytes</div>
            <div class="timestamp">Submitted: {timestamp}</div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        # Save HTML file
        html_file = Path("1-website/assets/computer_data/index.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Created computer data summary: {html_file}")
        
    except Exception as e:
        print(f"Error creating summary HTML: {e}")

def trigger_website_regeneration():
    """Trigger the website regeneration workflow"""
    try:
        import requests
        
        # Get GitHub token and repository info
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            print("⚠️  No GitHub token available to trigger website regeneration")
            return False
        
        # Get repository info from environment
        github_repository = os.environ.get('GITHUB_REPOSITORY', 'szhang/EmployeeData')
        repo_owner, repo_name = github_repository.split('/')
        
        # Trigger the regenerate-website workflow
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/regenerate-website.yml/dispatches"
        
        payload = {
            "ref": "main",
            "inputs": {
                "triggered_by": "computer_data_handler"
            }
        }
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 204:
            print("✅ Triggered website regeneration workflow")
            return True
        else:
            print(f"⚠️  Failed to trigger website regeneration: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️  Error triggering website regeneration: {e}")
        return False

def main():
    """Main function"""
    print("🖥️ Handling computer data...")
    
    # Load computer data
    data = load_computer_data()
    if not data:
        print("❌ No computer data found")
        sys.exit(1)
    
    print(f"📊 Processing data for: {data.get('Computername', 'Unknown')} ({data.get('Name', 'Unknown')})")
    
    # Save computer data
    if save_computer_data(data):
        print("✅ Computer data saved successfully")
        
        # Create summary HTML
        create_summary_html()
        
        # Trigger website regeneration
        print("🔄 Triggering website regeneration...")
        trigger_website_regeneration()
        
        print("🎉 Computer data handling complete!")
    else:
        print("❌ Failed to save computer data")
        sys.exit(1)

if __name__ == "__main__":
    main()
