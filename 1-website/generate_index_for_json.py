#!/usr/bin/env python3
"""
Generate index.html for the individual_employees directory to enable directory listing.
This script scans the directory and creates an HTML file with links to all JSON files.
This should be run after the weekly scraper to ensure the index is up to date.
"""

import os
import json
from pathlib import Path
import sys

def generate_employee_index():
    """Generate employee_json_dir.json for the individual_employees directory."""
    # Get the script directory - the script is already in the website directory
    script_dir = Path(__file__).parent
    employees_dir = script_dir / "assets" / "individual_employees"
    json_file = script_dir / "employee_json_dir.json"
    
    if not employees_dir.exists():
        print(f"Error: Directory {employees_dir} does not exist")
        return False
    
    # Get all JSON files
    json_files = []
    for file_path in employees_dir.glob("*.json"):
        json_files.append(file_path.name)
    
    # Sort the files for consistent ordering
    json_files.sort()
    
    # Generate JSON content
    json_content = {
        "employee_files": json_files,
        "total_count": len(json_files),
        "generated_at": str(Path().cwd()),
        "description": "List of all employee JSON files in the individual_employees directory"
    }
    
    # Write the JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_content, f, indent=2)
    
    print(f"Generated employee_json_dir.json with {len(json_files)} employee files")
    return True

if __name__ == "__main__":
    success = generate_employee_index()
    if not success:
        sys.exit(1)