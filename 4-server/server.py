#!/usr/bin/env python3
"""
Server Component for EmployeeData
Handles POST requests from AboutMe app and merges computer data into employee data
This server is designed to run on GitHub Actions and handle repository dispatch events
"""

import json
import os
import sys
import time
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

def get_repository_root():
    """Smart function to get repository root for both local and GitHub environments"""
    # Start from current working directory, not the file location
    # This allows the function to work when the file is copied to different locations
    current_dir = os.getcwd()
    
    # Walk up the directory tree to find the repository root
    while current_dir != os.path.dirname(current_dir):  # Not at filesystem root
        if os.path.exists(os.path.join(current_dir, 'docs')):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    
    # Fallback: try using the file location as a last resort
    current_file = os.path.abspath(__file__)
    
    # If running from 4-server directory (local development or GitHub Actions)
    if os.path.basename(os.path.dirname(current_file)) == '4-server':
        # Go up one level to get repository root
        return os.path.dirname(os.path.dirname(current_file))
    
    # If running from repository root (direct execution)
    elif os.path.exists(os.path.join(os.path.dirname(current_file), 'docs')):
        return os.path.dirname(current_file)
    
    # Final fallback: assume we're in the repository root
    return os.path.dirname(current_file)

# Get the repository root directory using smart detection
REPO_ROOT = get_repository_root()

# Using individual JSON files only - direct updates to employee records
INDIVIDUAL_EMPLOYEES_DIR = os.path.join(REPO_ROOT, 'docs', 'assets', 'individual_employees')
COMPUTER_BACKUP_DIR = os.path.join(REPO_ROOT, 'docs', 'assets', 'computer_info_data_backup')

def find_employee_file_by_user(computer_data):
    """Find the employee JSON file that matches the user from computer data"""
    try:
        human_name = computer_data.get('human_name', '').strip()
        username = computer_data.get('username', '').strip()
        
        if not human_name and not username:
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
                if _employee_matches_user(employee_data, human_name, username):
                    print(f"✅ Found matching employee in {filename}")
                    return employee_path
                    
            except Exception as e:
                print(f"⚠️  Warning: Could not read {filename}: {e}")
                continue
        
        print(f"⚠️  No matching employee found for user: {human_name} ({username})")
        return None
        
    except Exception as e:
        print(f"❌ Error finding employee file: {e}")
        return None

def _employee_matches_user(employee_data, human_name, username):
    """Check if employee data matches the user from computer data with fuzzy matching"""
    try:
        # Try exact match first, then fuzzy match
        if human_name:
            employee_name = employee_data.get('human_name', employee_data.get('Human Name', '')).strip()
            
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
        
        # Create new computer info entry (handle both old and new field names)
        new_computer_info = {
            'computername': computer_data.get('computer_name'),
            'os': computer_data.get('os'),
            'manufacturer': computer_data.get('manufacturer'),
            'model': computer_data.get('model'),
            'cpu': computer_data.get('cpu'),
            'gpu_name': computer_data.get('gpu_name'),
            'gpu_driver': computer_data.get('gpu_driver'),
            'memory_bytes': computer_data.get('memory_bytes'),
            'serial_number': computer_data.get('serial_number'),
            'last_updated': datetime.now().isoformat()
        }
        
        # Handle computer_info as a dictionary with computername as key
        if 'computer_info' not in employee_data:
            employee_data['computer_info'] = {}
        elif isinstance(employee_data['computer_info'], list):
            # Convert existing list to dictionary if needed
            computer_dict = {}
            for computer in employee_data['computer_info']:
                computername = computer.get('computername', 'Unknown')
                computer_dict[computername] = computer
            employee_data['computer_info'] = computer_dict
        
        # Get computername as key
        computername = new_computer_info.get('computername', 'Unknown')
        
        # Check if this computer already exists
        if computername in employee_data['computer_info']:
            # Update existing entry
            employee_data['computer_info'][computername] = new_computer_info
            print(f"✅ Updated existing computer entry for {computername}")
        else:
            # Add new computer entry
            employee_data['computer_info'][computername] = new_computer_info
            print(f"✅ Added new computer entry for {computername}")
        
        # Save updated employee file
        with open(employee_file_path, 'w', encoding='utf-8') as f:
            json.dump(employee_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Updated employee file: {employee_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating employee file: {e}")
        return False

def backup_computer_data(computer_data):
    """Create a backup of computer data for archival purposes"""
    try:
        # Ensure backup directory exists
        os.makedirs(COMPUTER_BACKUP_DIR, exist_ok=True)
        
        # Generate filename with timestamp
        computer_name = computer_data.get('computer_name', 'unknown').replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{computer_name}_{timestamp}.json"
        file_path = os.path.join(COMPUTER_BACKUP_DIR, filename)
        
        # Clean snake_case schema
        backup_data = {
            "computer_name": computer_data.get('computer_name', 'Unknown'),
            "human_name": computer_data.get('human_name', 'Unknown'),
            "username": computer_data.get('username', 'Unknown'),
            "cpu": computer_data.get('cpu', 'Unknown'),
            "os": computer_data.get('os', 'Unknown'),
            "manufacturer": computer_data.get('manufacturer', 'Unknown'),
            "model": computer_data.get('model', 'Unknown'),
            "gpu_name": computer_data.get('gpu_name', 'Unknown'),
            "gpu_driver": computer_data.get('gpu_driver', 'Unknown'),
            "gpu_memory": computer_data.get('gpu_memory'),
            "memory_bytes": computer_data.get('memory_bytes'),
            "serial_number": computer_data.get('serial_number', 'Unknown')
        }
        
        # Add server timestamp
        backup_data["server_timestamp"] = datetime.now().isoformat()
        
        # Save backup file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Computer data backup saved to {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating computer backup: {e}")
        return False


def commit_to_github(computer_data=None):
    """Commit changes to GitHub repository using git commands"""
    if not GITHUB_TOKEN:
        print("⚠️  No GitHub token available for committing")
        return False
    
    try:
        import subprocess
        
        # Determine current branch (default to main)
        branch = os.environ.get('GITHUB_REF_NAME') or os.environ.get('GITHUB_HEAD_REF') or 'main'
        
        # Configure git
        subprocess.run(['git', 'config', '--local', 'user.email', 'action@github.com'], check=True)
        subprocess.run(['git', 'config', '--local', 'user.name', 'GitHub Action'], check=True)
        
        # Add changes
        subprocess.run(['git', 'add', INDIVIDUAL_EMPLOYEES_DIR, COMPUTER_BACKUP_DIR], check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(['git', 'diff', '--staged', '--quiet'], capture_output=True)
        if result.returncode == 0:
            print("📝 No changes to commit")
            return True
        
        # Commit changes
        human_name = computer_data.get('human_name', 'Unknown') if computer_data else 'Unknown'
        commit_message = f"$$$_Action_Computer_Data_Update: {human_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Push changes with rebase + retry to handle concurrent updates
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                # Fetch and rebase before pushing to minimize conflicts
                subprocess.run(['git', 'fetch', 'origin', branch], check=True)
                subprocess.run(['git', 'rebase', f'origin/{branch}'], check=True)
                subprocess.run(['git', 'push', 'origin', branch], check=True)
                print("✅ Changes committed and pushed to GitHub")
                return True
            except subprocess.CalledProcessError as push_err:
                print(f"⚠️  Push attempt {attempt} failed: {push_err}")
                if attempt == max_attempts:
                    raise
                # Brief backoff before retrying
                time.sleep(1.5 * attempt)
        
        # Should not reach here
        return False
        
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
        
        # Handle both old and new payload structures
        if 'computer_info' in data:
            # New nested structure
            computer_data = data.get('computer_info', {})
        else:
            # Old flat structure (for backward compatibility)
            computer_data = data.get('computer_data', {})
        
        if not computer_data:
            return jsonify({'error': 'No computer data provided'}), 400
        
        print(f"📥 Received computer data for: {computer_data.get('computer_name', computer_data.get('Computername', 'Unknown'))}")
        
        # Find the employee file that matches this user
        employee_file_path = find_employee_file_by_user(computer_data)
        if not employee_file_path:
            return jsonify({'error': 'No matching employee found'}), 404
        
        # Update the computer info in the employee's file
        if not update_employee_computer_info(employee_file_path, computer_data):
            return jsonify({'error': 'Failed to update employee computer info'}), 500
        
        # Create backup of computer data
        if not backup_computer_data(computer_data):
            print("⚠️  Warning: Computer backup failed, but employee update succeeded")
        
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
        
        # Extract nested data from repository dispatch event
        client_payload = event_data.get('client_payload', {})
        computer_data = client_payload.get('computer_info', {})
        if not computer_data:
            print("❌ No computer data found in event payload")
            return False
        
        print(f"📥 Processing computer data for: {computer_data.get('computer_name', 'Unknown')}")
        
        # Find the employee file that matches this user
        employee_file_path = find_employee_file_by_user(computer_data)
        if not employee_file_path:
            print("❌ No matching employee found")
            return False
        
        # Update the computer info in the employee's file
        if not update_employee_computer_info(employee_file_path, computer_data):
            print("❌ Failed to update employee computer info")
            return False
        
        # Create backup of computer data
        if not backup_computer_data(computer_data):
            print("⚠️  Warning: Computer backup failed, but employee update succeeded")
        
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
    
    # Debug information
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"📁 Server file location: {os.path.abspath(__file__)}")
    print(f"📁 Repository root: {REPO_ROOT}")
    print(f"📁 Individual employees dir: {INDIVIDUAL_EMPLOYEES_DIR}")
    print(f"📁 Individual employees exists: {os.path.exists(INDIVIDUAL_EMPLOYEES_DIR)}")
    print(f"📁 Computer backup dir: {COMPUTER_BACKUP_DIR}")
    print(f"📁 Computer backup exists: {os.path.exists(COMPUTER_BACKUP_DIR)}")
    
    # Environment detection
    if os.environ.get('GITHUB_ACTIONS'):
        print("🔧 Running in GitHub Actions environment")
    else:
        print("💻 Running in local development environment")
    
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
    print(f"💾 Computer backup directory: {COMPUTER_BACKUP_DIR}")
    print(f"🌐 Server starting on port 5000")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()
