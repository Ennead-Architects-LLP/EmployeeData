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

COMPUTER_BACKUP_DIR = os.path.join(REPO_ROOT, 'docs', 'assets', 'computer_info_data_backup')
INDIVIDUAL_COMPUTER_DATA_DIR = os.path.join(REPO_ROOT, 'docs', 'assets', 'individual_computer_data')


def create_individual_computer_data_file(computer_data):
    """Create/update individual computer data JSON file for each employee"""
    try:
        # Ensure directory exists
        os.makedirs(INDIVIDUAL_COMPUTER_DATA_DIR, exist_ok=True)
        
        # Get human name for filename
        human_name = computer_data.get('human_name', 'Unknown').strip()
        if not human_name or human_name == 'Unknown':
            print("❌ No human_name provided for individual computer data file")
            return False
        
        # Create safe filename
        safe_name = human_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{safe_name}_computer_info.json"
        file_path = os.path.join(INDIVIDUAL_COMPUTER_DATA_DIR, filename)
        
        # Load existing data if file exists
        existing_data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"⚠️  Warning: Could not load existing computer data file: {e}")
                existing_data = {}
        
        # Create computer info entry
        computer_name = computer_data.get('computer_name', 'Unknown')
        computer_info = {
            'computername': computer_name,
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
        
        # Update or add computer info (dict of dicts format)
        existing_data[computer_name] = computer_info
        
        # Save updated file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Individual computer data saved to {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating individual computer data file: {e}")
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


def process_computer_data_workflow(computer_data):
    """Unified workflow for processing computer data - handles backup, individual files, and GitHub commit"""
    success_count = 0
    total_operations = 3  # backup, individual file, commit
    
    print(f"📥 Processing computer data for: {computer_data.get('computer_name', computer_data.get('Computername', 'Unknown'))}")
    
    # Create backup of computer data
    if backup_computer_data(computer_data):
        success_count += 1
    else:
        print("⚠️  Warning: Computer backup failed, but continuing with other operations")
    
    # Create/update individual computer data file
    if create_individual_computer_data_file(computer_data):
        success_count += 1
    else:
        print("⚠️  Warning: Individual computer data file creation failed, but continuing with other operations")
    
    # Commit to GitHub (if configured)
    if commit_to_github(computer_data):
        success_count += 1
    else:
        print("⚠️  Warning: GitHub commit failed, but data was saved locally")
    
    return success_count, total_operations

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
        subprocess.run(['git', 'add', COMPUTER_BACKUP_DIR, INDIVIDUAL_COMPUTER_DATA_DIR], check=True)
        
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

def extract_computer_data_from_request(data):
    """Extract computer data from request payload, handling both old and new structures"""
    # Handle both old and new payload structures
    if 'computer_info' in data:
        # New nested structure
        computer_data = data.get('computer_info', {})
    else:
        # Old flat structure (for backward compatibility)
        computer_data = data.get('computer_data', {})
    
    return computer_data

@app.route('/api/computer-data', methods=['POST'])
def handle_computer_data():
    """Handle POST request from AboutMe app"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract computer data using unified function
        computer_data = extract_computer_data_from_request(data)
        
        if not computer_data:
            return jsonify({'error': 'No computer data provided'}), 400
        
        # Process computer data using unified workflow
        success_count, total_operations = process_computer_data_workflow(computer_data)
        
        # Determine response based on success rate
        if success_count == total_operations:
            message = 'Computer data processed successfully'
            status_code = 200
        elif success_count > 0:
            message = f'Computer data partially processed ({success_count}/{total_operations} operations succeeded)'
            status_code = 200
        else:
            message = 'Computer data processing failed'
            status_code = 500
        
        return jsonify({
            'success': success_count > 0,
            'message': message,
            'operations_completed': f'{success_count}/{total_operations}',
            'updated_employees': 1 if success_count > 0 else 0
        }), status_code
        
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

def extract_computer_data_from_event():
    """Extract computer data from GitHub repository dispatch event"""
    # Get event data from GitHub Actions environment
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    if not event_path or not os.path.exists(event_path):
        print("❌ No GitHub event data found")
        return None
    
    with open(event_path, 'r', encoding='utf-8') as f:
        event_data = json.load(f)
    
    # Extract nested data from repository dispatch event
    client_payload = event_data.get('client_payload', {})
    computer_data = client_payload.get('computer_info', {})
    if not computer_data:
        print("❌ No computer data found in event payload")
        return None
    
    return computer_data

def process_computer_data_from_event():
    """Process computer data from GitHub repository dispatch event"""
    try:
        # Extract computer data using unified function
        computer_data = extract_computer_data_from_event()
        if not computer_data:
            return False
        
        # Process computer data using unified workflow
        success_count, total_operations = process_computer_data_workflow(computer_data)
        
        # Determine success based on operations completed
        if success_count == total_operations:
            print(f"✅ Successfully processed computer data. All {total_operations} operations completed.")
            return True
        elif success_count > 0:
            print(f"⚠️  Partially processed computer data. {success_count}/{total_operations} operations completed.")
            return True  # Still consider partial success as success
        else:
            print("❌ Failed to process computer data. No operations completed.")
            return False
        
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
    print(f"📁 Individual employees computer data dir: {INDIVIDUAL_COMPUTER_DATA_DIR}")
    print(f"📁 Individual employees computer data exists: {os.path.exists(INDIVIDUAL_COMPUTER_DATA_DIR)}")
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
    
    print(f"👥 Individual computer data directory: {INDIVIDUAL_COMPUTER_DATA_DIR}")
    print(f"💾 Computer backup directory: {COMPUTER_BACKUP_DIR}")
    print(f"🌐 Server starting on port 5000")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()
