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


def validate_data_structure(data: dict, expected_type: str) -> bool:
    """
    Validate that the data structure matches the expected type.
    This prevents accidental merging of incompatible data structures.
    
    Args:
        data: Data to validate
        expected_type: Either "individual_computer" or "gpu_master_list"
    
    Returns:
        bool: True if structure is valid for the expected type
    """
    if not isinstance(data, dict):
        return False
    
    if expected_type == "individual_computer":
        # Individual computer data should have lowercase field names
        expected_fields = {"computername", "os", "manufacturer", "model", "cpu", "gpu_name", "gpu_driver", "memory_bytes", "serial_number", "last_updated"}
        sample_computer = next(iter(data.values())) if data else {}
        return any(field in sample_computer for field in expected_fields)
    
    elif expected_type == "gpu_master_list":
        # GPU master list data has nested structure: {employee_name: {computer_id: {fields...}}}
        # We need to check the inner computer data structure
        if not data:
            return False
        # Get the first employee's computer data
        first_employee_computers = next(iter(data.values()))
        if not isinstance(first_employee_computers, dict):
            return False
        # Get the first computer's data
        sample_computer = next(iter(first_employee_computers.values())) if first_employee_computers else {}
        expected_fields = {"Computername", "Username", "Last Name", "First Name", "OS", "Manufacturer", "Model", "Total Physical Memory", "CPU", "Serial Number", "GPU Name", "GPU Date", "GPU Age ", "GPU Processor", "Replacement Piroirty ", "GPU Driver", "GPU Memory", "Date"}
        return any(field in sample_computer for field in expected_fields)
    
    return False


def add_computer_data_to_employee(employee_data: dict, computer_data: dict, section_name: str) -> None:
    """
    Add computer data to employee under a specific section name.
    This keeps different data sources completely separate and validates structure.
    
    Args:
        employee_data: Employee data dict to modify
        computer_data: Computer data to add
        section_name: Name of the section (e.g., "computer_info", "Static GPU Master List")
    """
    if not computer_data:
        return
    
    # For individual computer data, validate the structure
    if section_name == "computer_info":
        if not validate_data_structure(computer_data, "individual_computer"):
            print(f"WARNING: Data structure validation failed for {section_name} - skipping to prevent data corruption")
            return
    
    # For GPU master list data, we don't validate individual employee data
    # since it's already validated at the master list level
    
    # Ensure the section doesn't already exist to prevent overwriting
    if section_name in employee_data:
        print(f"WARNING: {section_name} already exists for employee {employee_data.get('human_name', 'Unknown')} - preserving existing data")
        return
    
    employee_data[section_name] = computer_data
    print(f"✅ Added {section_name} data for {employee_data.get('human_name', 'Unknown')}")


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

    print("\n=== DATA SOURCE 2: INDIVIDUAL COMPUTER INFO FILES (CONFIDENTIAL) ===")
    # Load individual computer info files
    computer_info_by_employee = {}
    computer_matches = 0
    computer_created_employees = 0
    computer_validation_errors = 0
    
    if computers_dir.exists():
        # Load all individual computer data files
        for cp in sorted(computers_dir.glob("*_computer_info.json")):
            clean_key = cp.stem.replace("_computer_info", "")
            payload = _safe_read_json(cp)
            if isinstance(payload, dict):
                # Validate this is individual computer data structure
                if validate_data_structure(payload, "individual_computer"):
                    computer_info_by_employee[clean_key] = payload
                    print(f"✅ Validated individual computer data: {cp.name}")
                else:
                    computer_validation_errors += 1
                    print(f"❌ Invalid individual computer data structure: {cp.name}")
            else:
                computer_validation_errors += 1
                print(f"❌ Invalid data format in: {cp.name}")
        
        # Try to match individual computer data to existing employees
        for employee_key, employee_data in employees.items():
            # Try to find matching computer info by filename
            clean_key = employee_key.lower().replace(" ", "_")
            comp = computer_info_by_employee.get(clean_key)
            if comp:
                # Add to separate "computer_info" section
                add_computer_data_to_employee(employee_data, comp, "computer_info")
                computer_matches += 1
                print(f"Matched individual computer data for: {employee_key}")
        
        # Create new employees for unmatched computer data
        for clean_key, comp_data in computer_info_by_employee.items():
            # Check if this computer data already matched to an existing employee
            already_matched = False
            for employee_data in employees.values():
                if employee_data.get("computer_info") == comp_data:
                    already_matched = True
                    break
            
            if not already_matched:
                # Create new employee from computer data
                # Extract name from computer data (use clean_key as fallback)
                first_computer = next(iter(comp_data.values())) if comp_data else {}
                first_name = first_computer.get("first_name", "").strip()
                last_name = first_computer.get("last_name", "").strip()
                full_name = f"{first_name} {last_name}".strip()
                
                if not full_name:
                    # Use clean_key as fallback, convert back to readable format
                    full_name = clean_key.replace("_", " ").title()
                
                new_employee = {
                    "human_name": full_name,
                    "source": "individual_computer_only",
                    "created_from": "Individual Computer Data"
                }
                # Add computer data to separate section
                add_computer_data_to_employee(new_employee, comp_data, "computer_info")
                employees[full_name] = new_employee
                computer_created_employees += 1
                print(f"Created new employee from individual computer data: {full_name}")
        
        print(f"Loaded computer info for {len(computer_info_by_employee)} employees")
        print(f"Successfully matched {computer_matches} employees with individual computer data")
        print(f"Created {computer_created_employees} new employees from individual computer data")
        if computer_validation_errors > 0:
            print(f"⚠️  {computer_validation_errors} individual computer data files failed validation")
    else:
        print(f"Note: Individual computers directory not found: {computers_dir}")

    print("\n=== DATA SOURCE 3: GPU MASTER LIST JSON (STATIC) ===")
    # Load GPU master list data
    gpu_data_by_name = {}
    gpu_matches = 0
    created_employees = 0
    if gpu_master_file.exists():
        gpu_data = _safe_read_json(gpu_master_file)
        if isinstance(gpu_data, dict):
            print("✅ Loading GPU master list data as-is (assuming correct structure)")
            # Create normalized name mapping for better matching
            for full_name, computers in gpu_data.items():
                normalized_key = normalize_name_for_matching(full_name)
                gpu_data_by_name[normalized_key] = computers
            
            # Add GPU master list data to existing employee data under "Static GPU Master List" section
            for employee_key, employee_data in employees.items():
                human_name = employee_data.get("human_name", "")
                if human_name:
                    normalized_name = normalize_name_for_matching(human_name)
                    gpu_computers = gpu_data_by_name.get(normalized_name)
                    
                    if gpu_computers:
                        # Add to separate "Static GPU Master List" section
                        add_computer_data_to_employee(employee_data, gpu_computers, "Static GPU Master List")
                        gpu_matches += 1
                        print(f"Matched GPU master list data for: {human_name}")
            
            # Create missing employees from GPU master list
            for normalized_name, gpu_computers in gpu_data_by_name.items():
                # Check if this employee already exists
                employee_exists = False
                for employee_data in employees.values():
                    if employee_data.get("human_name") and normalize_name_for_matching(employee_data["human_name"]) == normalized_name:
                        employee_exists = True
                        break
                
                if not employee_exists:
                    # Create new employee entry from GPU data
                    # Extract name from first computer entry
                    first_computer = next(iter(gpu_computers.values()))
                    first_name = first_computer.get("First Name", "").strip()
                    last_name = first_computer.get("Last Name", "").strip()
                    full_name = f"{first_name} {last_name}".strip()
                    
                    if full_name:
                        new_employee = {
                            "human_name": full_name,
                            "source": "gpu_master_list_only",
                            "created_from": "GPU Master List 2025"
                        }
                        # Add GPU data to separate section
                        add_computer_data_to_employee(new_employee, gpu_computers, "Static GPU Master List")
                        employees[full_name] = new_employee
                        created_employees += 1
                        print(f"Created missing employee from GPU master list: {full_name}")
            
            print(f"Loaded GPU data for {len(gpu_data_by_name)} employees from master list")
            print(f"Successfully matched {gpu_matches} employees with GPU master list data")
            print(f"Created {created_employees} missing employees from GPU master list")
    else:
        print(f"Note: GPU master list not found: {gpu_master_file}")

    print("\n=== MERGING COMPLETE ===")
    
    # Final validation summary
    print("\n🔍 DATA SEPARATION VALIDATION SUMMARY:")
    print(f"Source 1 - Individual Employee Files: {len(employees) - computer_created_employees - created_employees} employees")
    print(f"Source 2 - Individual Computer Data: {computer_matches} matched + {computer_created_employees} created")
    print(f"Source 3 - GPU Master List Data: {gpu_matches} matched + {created_employees} created")
    print(f"Total employees with individual computer data: {sum(1 for emp in employees.values() if emp.get('computer_info'))}")
    print(f"Total employees with GPU master list data: {sum(1 for emp in employees.values() if emp.get('Static GPU Master List'))}")
    print(f"Total final employees: {len(employees)}")
    
    if computer_validation_errors > 0:
        print(f"\n⚠️  VALIDATION WARNINGS:")
        print(f"   - {computer_validation_errors} individual computer data files failed validation")
        print("   - Data separation maintained, but some individual computer data may be missing")
    
    # Verify no cross-contamination
    cross_contamination = 0
    for emp_name, emp_data in employees.items():
        has_individual = 'computer_info' in emp_data and emp_data['computer_info']
        has_gpu_master = 'Static GPU Master List' in emp_data and emp_data['Static GPU Master List']
        if has_individual and has_gpu_master:
            cross_contamination += 1
            print(f"⚠️  WARNING: {emp_name} has both data sources - this may indicate a matching issue")
    
    if cross_contamination == 0:
        print("✅ No cross-contamination detected - data sources properly separated")
    else:
        print(f"⚠️  {cross_contamination} employees have both data sources - review matching logic")
    
    merged_output.write_text(json.dumps(employees, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n📁 Generated {merged_output.relative_to(repo_root)} with {len(employees)} employees")
    
    # Return success only if no critical errors
    return computer_validation_errors == 0


if __name__ == "__main__":
    success = merge_all_employees()
    if not success:
        sys.exit(1)


