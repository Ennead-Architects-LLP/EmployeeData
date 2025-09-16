#!/usr/bin/env python3
"""
Merge all individual employee JSON files and individual computer info JSON files
into a single file for the website.
This script is intended to be run from GitHub Actions and lives under .github/scripts.
It writes outputs into the docs/ directory regardless of current working directory.

Output:
- docs/assets/employees.json: dictionary of employee objects keyed by human_name, merged from individual files,
  each optionally augmented with per-employee computer_info from
  docs/assets/individual_computer_data/{employee_name}_computer_info.json
"""

import json
from pathlib import Path
import sys


def get_repo_root() -> Path:
    # .github/scripts/ -> repo root is two parents up
    return Path(__file__).resolve().parents[2]


def _safe_read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Warning: failed to read {path.name}: {e}")
        return None


def merge_all_employees() -> bool:
    repo_root = get_repo_root()
    docs_dir = repo_root / "docs"
    employees_dir = docs_dir / "assets" / "individual_employees"
    computers_dir = docs_dir / "assets" / "individual_computer_data"
    merged_output = docs_dir / "assets" / "employees.json"

    if not employees_dir.exists():
        print(f"Error: Directory {employees_dir} does not exist")
        return False

    # Load computer info files into a map keyed by employee clean name (file stem sans suffix)
    computer_info_by_employee = {}
    if computers_dir.exists():
        for cp in sorted(computers_dir.glob("*_computer_info.json")):
            clean_key = cp.stem.replace("_computer_info", "")
            payload = _safe_read_json(cp)
            if isinstance(payload, dict):
                computer_info_by_employee[clean_key] = payload
    else:
        print(f"Note: computers directory not found: {computers_dir}")

    # Merge employee files with matching computer info by filename key
    employees = {}
    for p in sorted(employees_dir.glob("*.json")):
        data = _safe_read_json(p)
        if data is None:
            continue
        clean_key = p.stem  # matches how individual files are named
        comp = computer_info_by_employee.get(clean_key)
        if comp:
            # Replace or set computer_info to the dict-of-dicts structure
            data["computer_info"] = comp
        
        # Use human_name as the key for the dictionary
        employee_key = data.get("human_name", clean_key)
        employees[employee_key] = data

    merged_output.write_text(json.dumps(employees, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {merged_output.relative_to(repo_root)} with {len(employees)} employees (with computer data where available)")
    return True


if __name__ == "__main__":
    success = merge_all_employees()
    if not success:
        sys.exit(1)


