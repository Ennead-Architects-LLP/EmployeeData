#!/usr/bin/env python3
"""
Generate index JSONs for the website's individual_employees directory.
This script is intended to be run from GitHub Actions and lives under .github/scripts.
It writes outputs into the docs/ directory regardless of current working directory.
"""

import json
from pathlib import Path
import sys


def get_repo_root() -> Path:
    # .github/scripts/ -> repo root is three parents up
    return Path(__file__).resolve().parents[2]


def generate_employee_index() -> bool:
    repo_root = get_repo_root()
    docs_dir = repo_root / "docs"
    employees_dir = docs_dir / "assets" / "individual_employees"
    json_file = docs_dir / "employee_json_dir.json"
    fallback_file = docs_dir / "assets" / "employee_files_list.json"

    if not employees_dir.exists():
        print(f"Error: Directory {employees_dir} does not exist")
        return False

    json_files = sorted([p.name for p in employees_dir.glob("*.json")])

    json_content = {
        "employee_files": json_files,
        "total_count": len(json_files),
        "generated_at": str(repo_root),
        "description": "List of all employee JSON files in the individual_employees directory",
    }

    json_file.write_text(json.dumps(json_content, indent=2), encoding="utf-8")
    fallback_file.write_text(json.dumps(json_files, indent=2), encoding="utf-8")

    print(f"Generated {json_file.relative_to(repo_root)} with {len(json_files)} employee files")
    print(f"Generated {fallback_file.relative_to(repo_root)} with {len(json_files)} employee files")
    return True


if __name__ == "__main__":
    success = generate_employee_index()
    if not success:
        sys.exit(1)

