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

def save_computer_data(data):
    """Save computer data to assets directory"""
    try:
        # Create computer_data directory
        data_dir = Path("assets/computer_data")
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
        return True
        
    except Exception as e:
        print(f"Error saving computer data: {e}")
        return False

def create_summary_html():
    """Create a summary HTML page for computer data"""
    try:
        master_file = Path("assets/computer_data/all_computers.json")
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
        html_file = Path("assets/computer_data/index.html")
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
