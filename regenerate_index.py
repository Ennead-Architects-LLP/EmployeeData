#!/usr/bin/env python3
"""
Regenerate the employee index.html file.
This script can be run manually to update the index after adding new employee files.
"""

import sys
from pathlib import Path

# Add the 1-website directory to the path
website_dir = Path(__file__).parent / "1-website"
sys.path.insert(0, str(website_dir))

# Import and run the generator
from generate_index_for_json import generate_employee_index

if __name__ == "__main__":
    print("Regenerating employee JSON directory file...")
    success = generate_employee_index()
    if success:
        print("✅ employee_json_dir.json regenerated successfully!")
    else:
        print("❌ Failed to regenerate employee JSON directory file")
        sys.exit(1)
