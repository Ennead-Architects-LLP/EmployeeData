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


def normalize_name_for_matching(name: str) -> str:
    """Normalize name for matching between different data sources."""
    if not name:
        return ""
    # Remove extra spaces, convert to title case
    normalized = " ".join(name.split()).title()
    return normalized


def merge_computer_data_safely(existing_data: dict, new_data: dict, source_name: str) -> dict:
    """
    Safely merge computer data from different sources.
    Preserves existing data and adds new data without overwriting.
    
    Args:
        existing_data: Current computer info dict
        new_data: New computer data to merge
        source_name: Name of the data source for labeling
    
    Returns:
        Merged computer data dict
    """
    if not existing_data:
        return new_data.copy()
    
    merged = existing_data.copy()
    
    for computer_name, computer_info in new_data.items():
        if computer_name in merged:
            # Computer already exists, merge the data carefully
            existing_computer = merged[computer_name]
            merged_computer = existing_computer.copy()
            
            # Add new fields without overwriting existing ones
            for field, value in computer_info.items():
                if field not in merged_computer or merged_computer[field] is None:
                    merged_computer[field] = value
                elif merged_computer[field] != value:
                    # Field exists but different value - add as source-specific field
                    source_field = f"{field}_{source_name.lower()}"
                    merged_computer[source_field] = value
            
            merged[computer_name] = merged_computer
        else:
            # New computer, add it directly
            merged[computer_name] = computer_info.copy()
    
    return merged


def merge_all_employees() -> bool:
    repo_root = get_repo_root()
    docs_dir = repo_root / "docs"
    employees_dir = docs_dir / "assets" / "individual_employees"
    computers_dir = docs_dir / "assets" / "individual_computer_data"
    workfiles_dir = repo_root / "99-workfiles"
    gpu_master_file = workfiles_dir / "EA_US_Desktop_Hardware_GPU_Master List_2025.json"
    merged_output = docs_dir / "assets" / "employees.json"

    if not employees_dir.exists():
        print(f"Error: Directory {employees_dir} does not exist")
        return False

    print("=== DATA SOURCE 1: INDIVIDUAL EMPLOYEE FILES ===")
    # Load individual employee data files
    employees = {}
    for p in sorted(employees_dir.glob("*.json")):
        data = _safe_read_json(p)
        if data is None:
            continue
        clean_key = p.stem  # matches how individual files are named
        employee_key = data.get("human_name", clean_key)
        employees[employee_key] = data
    print(f"Loaded {len(employees)} employees from individual employee files")

    print("\n=== DATA SOURCE 2: INDIVIDUAL COMPUTER INFO FILES ===")
    # Load individual computer info files
    computer_info_by_employee = {}
    computer_matches = 0
    if computers_dir.exists():
        for cp in sorted(computers_dir.glob("*_computer_info.json")):
            clean_key = cp.stem.replace("_computer_info", "")
            payload = _safe_read_json(cp)
            if isinstance(payload, dict):
                computer_info_by_employee[clean_key] = payload
        
        # Merge individual computer data with employee data
        for employee_key, employee_data in employees.items():
            # Try to find matching computer info by filename
            clean_key = employee_key.lower().replace(" ", "_")
            comp = computer_info_by_employee.get(clean_key)
            if comp:
                # Use safe merge to preserve any existing computer_info
                existing_comp_info = employee_data.get("computer_info", {})
                merged_comp_info = merge_computer_data_safely(existing_comp_info, comp, "individual")
                employee_data["computer_info"] = merged_comp_info
                computer_matches += 1
                print(f"Matched individual computer data for: {employee_key}")
        
        print(f"Loaded computer info for {len(computer_info_by_employee)} employees")
        print(f"Successfully matched {computer_matches} employees with individual computer data")
    else:
        print(f"Note: Individual computers directory not found: {computers_dir}")

    print("\n=== DATA SOURCE 3: GPU MASTER LIST JSON ===")
    # Load GPU master list data
    gpu_data_by_name = {}
    gpu_matches = 0
    if gpu_master_file.exists():
        gpu_data = _safe_read_json(gpu_master_file)
        if isinstance(gpu_data, dict):
            # Create normalized name mapping for better matching
            for full_name, computers in gpu_data.items():
                normalized_key = normalize_name_for_matching(full_name)
                gpu_data_by_name[normalized_key] = computers
            
            # Merge GPU master list data with employee data
            for employee_key, employee_data in employees.items():
                human_name = employee_data.get("human_name", "")
                if human_name:
                    normalized_name = normalize_name_for_matching(human_name)
                    gpu_computers = gpu_data_by_name.get(normalized_name)
                    
                    if gpu_computers:
                        # Use safe merge to preserve any existing computer_info
                        existing_comp_info = employee_data.get("computer_info", {})
                        merged_comp_info = merge_computer_data_safely(existing_comp_info, gpu_computers, "gpu_master")
                        employee_data["computer_info"] = merged_comp_info
                        gpu_matches += 1
                        print(f"Matched GPU master list data for: {human_name}")
            
            print(f"Loaded GPU data for {len(gpu_data_by_name)} employees from master list")
            print(f"Successfully matched {gpu_matches} employees with GPU master list data")
    else:
        print(f"Note: GPU master list not found: {gpu_master_file}")

    print("\n=== MERGING COMPLETE ===")
    merged_output.write_text(json.dumps(employees, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {merged_output.relative_to(repo_root)} with {len(employees)} employees")
    print(f"Individual computer data matched for {computer_matches} employees")
    print(f"GPU master list data matched for {gpu_matches} employees")
    print(f"Total employees with computer data: {sum(1 for emp in employees.values() if emp.get('computer_info'))}")
    return True


if __name__ == "__main__":
    success = merge_all_employees()
    if not success:
        sys.exit(1)


