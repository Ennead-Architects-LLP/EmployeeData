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
from difflib import SequenceMatcher

app = Flask(__name__)

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = os.environ.get('REPO_OWNER', 'Ennead-Architects-LLP')
REPO_NAME = os.environ.get('REPO_NAME', 'EmployeeData')
# Using individual JSON files only - direct updates to employee records
INDIVIDUAL_EMPLOYEES_DIR = '1-website/assets/individual_employees'

def find_employee_file_by_user(computer_data):
    """Find the employee JSON file that matches the user from computer data"""
    try:
        user_name = computer_data.get('Name', '').strip()
        username = computer_data.get('Username', '').strip()
        
        if not user_name and not username:
            print("❌ No user name or username provided in computer data")
            return None
        
        # Scan the individual employees directory for all JSON files
        if not os.path.exists(INDIVIDUAL_EMPLOYEES_DIR):
            print(f"❌ Employee directory not found: {INDIVIDUAL_EMPLOYEES_DIR}")
            return None
        
        # Get all JSON files in the directory
        employee_files = []
        for filename in os.listdir(INDIVIDUAL_EMPLOYEES_DIR):
            if filename.endswith('.json') and filename != 'index.json':
                employee_files.append(filename)
        
        if not employee_files:
            print(f"⚠️  No employee JSON files found in {INDIVIDUAL_EMPLOYEES_DIR}")
            return None
        
        # Search through each file to find matching user
        for filename in employee_files:
            try:
                employee_path = os.path.join(INDIVIDUAL_EMPLOYEES_DIR, filename)
                with open(employee_path, 'r', encoding='utf-8') as f:
                    employee_data = json.load(f)
                
                # Check if this employee matches by name or username
                if _employee_matches_user(employee_data, user_name, username):
                    print(f"✅ Found matching employee in {filename}")
                    return employee_path
                    
            except Exception as e:
                print(f"⚠️  Warning: Could not read {filename}: {e}")
                continue
        
        print(f"⚠️  No matching employee found for user: {user_name} ({username})")
        return None
        
    except Exception as e:
        print(f"❌ Error finding employee file: {e}")
        return None

def _employee_matches_user(employee_data, human_name, username):
    """Check if employee data matches the user from computer data with fuzzy matching"""
    try:
        # Try exact match first, then fuzzy match
        if human_name:
            employee_name = employee_data.get('real_name', '').strip()
            
            # Exact match (case insensitive)
            if employee_name.lower() == human_name.lower():
                return True
            
            # Fuzzy match with 80% similarity threshold
            similarity = SequenceMatcher(None, employee_name.lower(), human_name.lower()).ratio()
            if similarity >= 0.8:
                print(f"✅ Fuzzy name match: '{employee_name}' ≈ '{human_name}' ({similarity:.1%})")
                return True
        
        # Try to match by username (from email)
        if username:
            employee_email = employee_data.get('email', '')
            if employee_email:
                email_username = employee_email.split('@')[0].strip().lower()
                
                # Exact username match
                if email_username == username.lower():
                    return True
                
                # Fuzzy username match with 80% similarity threshold
                similarity = SequenceMatcher(None, email_username, username.lower()).ratio()
                if similarity >= 0.8:
                    print(f"✅ Fuzzy username match: '{email_username}' ≈ '{username}' ({similarity:.1%})")
                    return True
        
        return False
        
    except Exception as e:
        print(f"⚠️  Error matching employee: {e}")
        return False

def update_employee_computer_info(employee_file_path, computer_data):
    """Update the computer info in a specific employee JSON file"""
    try:
        # Read the employee file
        with open(employee_file_path, 'r', encoding='utf-8') as f:
            employee_data = json.load(f)
        
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
        if 'computer_info' not in employee_data:
            employee_data['computer_info'] = []
        elif not isinstance(employee_data['computer_info'], list):
            # Convert existing single dict to list if needed
            employee_data['computer_info'] = [employee_data['computer_info']]
        
        # Check if this computer already exists (by computername and serial number)
        computer_exists = False
        for i, existing_computer in enumerate(employee_data['computer_info']):
            if (existing_computer.get('computername') == new_computer_info.get('computername') and 
                existing_computer.get('serial_number') == new_computer_info.get('serial_number')):
                # Update existing entry
                employee_data['computer_info'][i] = new_computer_info
                computer_exists = True
                print(f"✅ Updated existing computer entry for {new_computer_info.get('computername')}")
                break
        
        if not computer_exists:
            # Add new computer entry
            employee_data['computer_info'].append(new_computer_info)
            print(f"✅ Added new computer entry for {new_computer_info.get('computername')}")
        
        # Save updated employee file
        with open(employee_file_path, 'w', encoding='utf-8') as f:
            json.dump(employee_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Updated employee file: {employee_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating employee file: {e}")
        return False


def commit_to_github(computer_data=None):
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
        subprocess.run(['git', 'add', INDIVIDUAL_EMPLOYEES_DIR], check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(['git', 'diff', '--staged', '--quiet'], capture_output=True)
        if result.returncode == 0:
            print("📝 No changes to commit")
            return True
        
        # Commit changes
        human_name = computer_data.get('Name', 'Unknown') if computer_data else 'Unknown'
        commit_message = f"AutoUpdate Computer Data: {human_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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
        
        # Find the employee file that matches this user
        employee_file_path = find_employee_file_by_user(computer_data)
        if not employee_file_path:
            return jsonify({'error': 'No matching employee found'}), 404
        
        # Update the computer info in the employee's file
        if not update_employee_computer_info(employee_file_path, computer_data):
            return jsonify({'error': 'Failed to update employee computer info'}), 500
        
        updated_count = 1
        
        # Commit to GitHub (if configured)
        commit_to_github(computer_data)
        
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
        
        # Find the employee file that matches this user
        employee_file_path = find_employee_file_by_user(computer_data)
        if not employee_file_path:
            print("❌ No matching employee found")
            return False
        
        # Update the computer info in the employee's file
        if not update_employee_computer_info(employee_file_path, computer_data):
            print("❌ Failed to update employee computer info")
            return False
        
        updated_count = 1
        
        # Commit to GitHub
        commit_to_github(computer_data)
        
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
    
    print(f"👥 Individual employees directory: {INDIVIDUAL_EMPLOYEES_DIR}")
    print(f"🌐 Server starting on port 5000")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()
