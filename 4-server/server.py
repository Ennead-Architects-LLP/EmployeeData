#!/usr/bin/env python3
"""
Server Component for EmployeeData
Handles POST requests from AboutMe app and merges computer data into employee data
This server is designed to run on GitHub Actions and handle repository dispatch events
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = os.environ.get('REPO_OWNER', 'szhang')
REPO_NAME = os.environ.get('REPO_NAME', 'EmployeeData')
EMPLOYEE_DATA_FILE = '1-website/assets/employees_data.json'
INDIVIDUAL_EMPLOYEES_DIR = '1-website/assets/individual_employees'
COMPUTER_DATA_DIR = '1-website/assets/computer_data'

def load_employee_data():
    """Load existing employee data"""
    try:
        with open(EMPLOYEE_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('employees', [])
    except FileNotFoundError:
        print(f"❌ Employee data file not found: {EMPLOYEE_DATA_FILE}")
        return []
    except Exception as e:
        print(f"❌ Error loading employee data: {e}")
        return []

def save_employee_data(employees):
    """Save employee data to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(EMPLOYEE_DATA_FILE), exist_ok=True)
        
        with open(EMPLOYEE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(employees, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Employee data saved to {EMPLOYEE_DATA_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error saving employee data: {e}")
        return False

def save_computer_data(computer_data):
    """Save computer data to individual file"""
    try:
        # Ensure computer data directory exists
        os.makedirs(COMPUTER_DATA_DIR, exist_ok=True)
        
        # Generate filename
        computer_name = computer_data.get('Computername', 'unknown').replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{computer_name}_{timestamp}.json"
        file_path = os.path.join(COMPUTER_DATA_DIR, filename)
        
        # Save individual computer data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(computer_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Update master computer data file
        master_file = os.path.join(COMPUTER_DATA_DIR, 'all_computers.json')
        all_computers = []
        
        if os.path.exists(master_file):
            with open(master_file, 'r', encoding='utf-8') as f:
                all_computers = json.load(f)
        
        # Add new data
        all_computers.append({
            "timestamp": datetime.now().isoformat(),
            "computer_name": computer_data.get('Computername', 'Unknown'),
            "user": computer_data.get('Name', 'Unknown'),
            "data": computer_data
        })
        
        # Keep only last 100 entries
        all_computers = all_computers[-100:]
        
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(all_computers, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Computer data saved to {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving computer data: {e}")
        return False

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

def update_individual_employee_file(employee_data, computer_data):
    """Update individual employee JSON file with computer data"""
    try:
        # Find the employee's individual file
        employee_name = employee_data.get('real_name', '').replace(' ', '_')
        individual_file = os.path.join(INDIVIDUAL_EMPLOYEES_DIR, f"{employee_name}.json")
        
        if os.path.exists(individual_file):
            # Update the individual file
            with open(individual_file, 'r', encoding='utf-8') as f:
                individual_data = json.load(f)
            
            # Add computer data
            individual_data['computer_info'] = {
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
            
            # Save updated individual file
            with open(individual_file, 'w', encoding='utf-8') as f:
                json.dump(individual_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Updated individual employee file: {individual_file}")
            return True
        else:
            print(f"⚠️  Individual employee file not found: {individual_file}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating individual employee file: {e}")
        return False

def merge_computer_data(employees, computer_data):
    """Merge computer data into employee data"""
    updated_count = 0
    
    # Try to find employee by name first
    user_name = computer_data.get('Name', '')
    username = computer_data.get('Username', '')
    employee = find_employee_by_name(employees, user_name)
    
    # If not found by name, try by username
    if not employee and username:
        employee = find_employee_by_username(employees, username)
    
    if employee:
        # Merge computer data into employee record
        employee['computer_info'] = {
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
        
        # Also update individual employee file
        update_individual_employee_file(employee, computer_data)
        
        updated_count = 1
        print(f"✅ Updated employee record for {user_name} ({username})")
    else:
        print(f"⚠️  Could not find employee record for {user_name} ({username})")
        print(f"   Searched by name: '{user_name}' and username: '{username}'")
    
    return updated_count

def commit_to_github():
    """Commit changes to GitHub repository using git commands"""
    if not GITHUB_TOKEN:
        print("⚠️  No GitHub token available for committing")
        return False
    
    try:
        import subprocess
        
        # Configure git
        subprocess.run(['git', 'config', '--local', 'user.email', 'action@github.com'], check=True)
        subprocess.run(['git', 'config', '--local', 'user.name', 'GitHub Action'], check=True)
        
        # Add changes
        subprocess.run(['git', 'add', EMPLOYEE_DATA_FILE, INDIVIDUAL_EMPLOYEES_DIR, COMPUTER_DATA_DIR], check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(['git', 'diff', '--staged', '--quiet'], capture_output=True)
        if result.returncode == 0:
            print("📝 No changes to commit")
            return True
        
        # Commit changes
        commit_message = f"Update employee computer data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Push changes
        subprocess.run(['git', 'push'], check=True)
        
        print("✅ Changes committed and pushed to GitHub")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error committing to GitHub: {e}")
        return False

@app.route('/api/computer-data', methods=['POST'])
def handle_computer_data():
    """Handle POST request from AboutMe app"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        computer_data = data.get('computer_data', {})
        if not computer_data:
            return jsonify({'error': 'No computer data provided'}), 400
        
        print(f"📥 Received computer data for: {computer_data.get('Computername', 'Unknown')}")
        
        # Load existing employee data
        employees = load_employee_data()
        if not employees:
            return jsonify({'error': 'No employee data available'}), 500
        
        # Save computer data
        if not save_computer_data(computer_data):
            return jsonify({'error': 'Failed to save computer data'}), 500
        
        # Merge computer data into employee data
        updated_count = merge_computer_data(employees, computer_data)
        
        # Save updated employee data
        if not save_employee_data(employees):
            return jsonify({'error': 'Failed to save employee data'}), 500
        
        # Commit to GitHub (if configured)
        commit_to_github()
        
        return jsonify({
            'success': True,
            'message': 'Computer data processed successfully',
            'updated_employees': updated_count
        }), 200
        
    except Exception as e:
        print(f"❌ Error processing computer data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'EmployeeData Server',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/computer-data': 'Submit computer data from AboutMe app',
            'GET /api/health': 'Health check'
        }
    }), 200

def process_computer_data_from_event():
    """Process computer data from GitHub repository dispatch event"""
    try:
        # Get event data from GitHub Actions environment
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        if not event_path or not os.path.exists(event_path):
            print("❌ No GitHub event data found")
            return False
        
        with open(event_path, 'r', encoding='utf-8') as f:
            event_data = json.load(f)
        
        # Extract computer data from repository dispatch event
        computer_data = event_data.get('client_payload', {}).get('computer_data')
        if not computer_data:
            print("❌ No computer data found in event payload")
            return False
        
        print(f"📥 Processing computer data for: {computer_data.get('Computername', 'Unknown')}")
        
        # Load existing employee data
        employees = load_employee_data()
        if not employees:
            print("❌ No employee data available")
            return False
        
        # Save computer data
        if not save_computer_data(computer_data):
            print("❌ Failed to save computer data")
            return False
        
        # Merge computer data into employee data
        updated_count = merge_computer_data(employees, computer_data)
        
        # Save updated employee data
        if not save_employee_data(employees):
            print("❌ Failed to save employee data")
            return False
        
        # Commit to GitHub
        commit_to_github()
        
        print(f"✅ Successfully processed computer data. Updated {updated_count} employee(s)")
        return True
        
    except Exception as e:
        print(f"❌ Error processing computer data from event: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting EmployeeData Server")
    print("=" * 50)
    
    # Check if running in GitHub Actions (repository dispatch event)
    if os.environ.get('GITHUB_ACTIONS') and os.environ.get('GITHUB_EVENT_PATH'):
        print("🔧 Running in GitHub Actions mode - processing repository dispatch event")
        
        # Process computer data from GitHub event
        success = process_computer_data_from_event()
        if success:
            print("🎉 Computer data processing completed successfully!")
            sys.exit(0)
        else:
            print("❌ Computer data processing failed!")
            sys.exit(1)
    
    # Check configuration for Flask server mode
    if not GITHUB_TOKEN:
        print("⚠️  Warning: No GitHub token configured")
    
    print(f"📊 Employee data file: {EMPLOYEE_DATA_FILE}")
    print(f"💾 Computer data directory: {COMPUTER_DATA_DIR}")
    print(f"🌐 Server starting on port 5000")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()
