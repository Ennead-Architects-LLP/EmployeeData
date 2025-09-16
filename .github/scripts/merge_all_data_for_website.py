#!/usr/bin/env python3
"""
Merge all individual employee JSON files into a single file for the website.
This script is intended to be run from GitHub Actions and lives under .github/scripts.
It writes outputs into the docs/ directory regardless of current working directory.

Output:
- docs/assets/employees.json: array of employee objects merged from individual files
"""

import json
from pathlib import Path
import sys


def get_repo_root() -> Path:
    # .github/scripts/ -> repo root is two parents up
    return Path(__file__).resolve().parents[2]


def merge_all_employees() -> bool:
    repo_root = get_repo_root()
    docs_dir = repo_root / "docs"
    employees_dir = docs_dir / "assets" / "individual_employees"
    merged_output = docs_dir / "assets" / "employees.json"

    if not employees_dir.exists():
        print(f"Error: Directory {employees_dir} does not exist")
        return False

    employees = []
    for p in sorted(employees_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            employees.append(data)
        except Exception as e:
            print(f"Warning: failed to read {p.name}: {e}")

    merged_output.write_text(json.dumps(employees, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {merged_output.relative_to(repo_root)} with {len(employees)} employees")
    return True


if __name__ == "__main__":
    success = merge_all_employees()
    if not success:
        sys.exit(1)


