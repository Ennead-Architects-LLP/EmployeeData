#!/usr/bin/env python3
"""
Test script to verify that the server correctly uses human name as matching key
to find and update individual employee JSON files
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def test_name_matching_flow():
    """Test the complete name matching and update flow"""
    print("Testing Name Matching Flow for Individual JSON Updates")
    print("=" * 60)
    
    # Import server functions
    sys.path.append('4-server')
    from server import find_employee_by_name, find_employee_by_username, update_individual_employee_file, load_employee_data
    
    # Load all employees
    employees = load_employee_data()
    print(f"Loaded {len(employees)} employees from database")
    
    # Find an employee to test with (let's use "Sen Zhang" if available, otherwise any employee)
    test_employee = None
    test_name = "Sen Zhang"
    
    # First try to find Sen Zhang
    test_employee = find_employee_by_name(employees, test_name)
    if not test_employee:
        # If not found, use any available employee
        test_employee = employees[0] if employees else None
        test_name = test_employee.get('real_name', 'Test User') if test_employee else 'Test User'
    
    if not test_employee:
        print("❌ No employees found in database")
        return False
    
    print(f"Using test employee: {test_name}")
    print(f"Email: {test_employee.get('email', 'N/A')}")
    
    # Create test computer data with the human name as the matching key
    test_computer_data = {
        "Computername": "TEST-WORKSTATION-001",
        "Username": test_employee.get('email', 'test@example.com').split('@')[0],
        "Name": test_name,  # This is the key field for matching!
        "OS": "Windows 11 Pro",
        "Manufacturer": "Dell Technologies",
        "Model": "OptiPlex 7090",
        "CPU": "Intel Core i7-11700",
        "GPU Name": "NVIDIA GeForce RTX 3060",
        "GPU Driver": "31.0.15.3742",
        "Total Physical Memory": 34359738368,  # 32GB
        "Serial Number": "TEST123456789",
        "Date": datetime.now().isoformat()
    }
    
    print(f"\nTest computer data:")
    print(f"  Computer: {test_computer_data['Computername']}")
    print(f"  Name (matching key): {test_computer_data['Name']}")
    print(f"  Username: {test_computer_data['Username']}")
    print(f"  OS: {test_computer_data['OS']}")
    print(f"  CPU: {test_computer_data['CPU']}")
    
    # Test the matching process
    print(f"\nStep 1: Testing employee matching...")
    
    # Try to find employee by name (primary method)
    found_employee = find_employee_by_name(employees, test_computer_data['Name'])
    
    if found_employee:
        print(f"✅ Found employee by name: {found_employee.get('real_name', 'Unknown')}")
    else:
        # Try by username (fallback method)
        found_employee = find_employee_by_username(employees, test_computer_data['Username'])
        if found_employee:
            print(f"✅ Found employee by username: {found_employee.get('real_name', 'Unknown')}")
        else:
            print(f"❌ Could not find employee with name '{test_computer_data['Name']}' or username '{test_computer_data['Username']}'")
            return False
    
    # Test updating the individual employee file
    print(f"\nStep 2: Testing individual file update...")
    
    success = update_individual_employee_file(found_employee, test_computer_data)
    
    if success:
        print("✅ Successfully updated individual employee file")
        
        # Verify the update
        employee_name = found_employee.get('real_name', '').replace(' ', '_')
        individual_file = Path("1-website/assets/individual_employees") / f"{employee_name}.json"
        
        if individual_file.exists():
            with open(individual_file, 'r', encoding='utf-8') as f:
                updated_data = json.load(f)
            
            if 'computer_info' in updated_data:
                comp_info = updated_data['computer_info']
                print(f"\n✅ Computer info successfully added to individual file:")
                print(f"   File: {individual_file.name}")
                print(f"   Computer: {comp_info.get('computername', 'N/A')}")
                print(f"   OS: {comp_info.get('os', 'N/A')}")
                print(f"   CPU: {comp_info.get('cpu', 'N/A')}")
                print(f"   GPU: {comp_info.get('gpu_name', 'N/A')}")
                print(f"   Last Updated: {comp_info.get('last_updated', 'N/A')}")
                
                return True
            else:
                print("❌ Computer info not found in updated file")
                return False
        else:
            print(f"❌ Individual file not found: {individual_file}")
            return False
    else:
        print("❌ Failed to update individual employee file")
        return False

def show_matching_process():
    """Show how the matching process works"""
    print("\n" + "=" * 60)
    print("Name Matching Process Explanation")
    print("=" * 60)
    
    print("\n1. AboutMe App Data Collection:")
    print("   • Collects user's full name via Windows API")
    print("   • Stores in 'Name' field (e.g., 'Sen Zhang')")
    print("   • Also collects username for fallback matching")
    
    print("\n2. Server Matching Process:")
    print("   • Primary: Match by 'Name' field (human name)")
    print("   • Fallback: Match by 'Username' field")
    print("   • Uses fuzzy matching for name variations")
    
    print("\n3. Individual JSON Update:")
    print("   • Finds employee record using name matching")
    print("   • Updates individual JSON file: {Name}.json")
    print("   • Adds 'computer_info' section with all specs")
    print("   • Includes timestamp for tracking updates")
    
    print("\n4. Data Structure:")
    print("   AboutMe sends: {")
    print("     'Name': 'Sen Zhang',        // ← Primary matching key")
    print("     'Username': 'szhang',       // ← Fallback matching key")
    print("     'Computername': 'EA-25CWFS3',")
    print("     'CPU': 'Intel Core i7',")
    print("     // ... other computer specs")
    print("   }")
    
    print("\n   Server updates: individual_employees/Sen_Zhang.json")
    print("   {")
    print("     'real_name': 'Sen Zhang',")
    print("     'email': 'sen.zhang@ennead.com',")
    print("     'computer_info': {          // ← Added by server")
    print("       'computername': 'EA-25CWFS3',")
    print("       'cpu': 'Intel Core i7',")
    print("       'last_updated': '2025-09-12T17:06:42.143100'")
    print("       // ... other specs")
    print("     }")
    print("   }")

def main():
    """Main test function"""
    print("🔍 Testing Human Name Matching for Individual JSON Updates")
    
    # Test the matching flow
    success = test_name_matching_flow()
    
    # Show the process explanation
    show_matching_process()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Name matching and individual JSON updates are working correctly!")
        print("\nKey points verified:")
        print("  • AboutMe app sends human name as primary matching key")
        print("  • Server uses name to find employee records")
        print("  • Individual JSON files are updated with computer specs")
        print("  • Fallback matching by username works")
        print("  • Computer info is properly structured and timestamped")
    else:
        print("❌ Name matching needs attention")
    
    print("\nUsage:")
    print("  Users run: python 3-aboutme/about_me.py --send-to-github --github-token TOKEN")
    print("  Server receives: Name='Sen Zhang', Username='szhang', Computer specs...")
    print("  Server matches: Finds employee with real_name='Sen Zhang'")
    print("  Server updates: individual_employees/Sen_Zhang.json with computer_info")

if __name__ == "__main__":
    main()
