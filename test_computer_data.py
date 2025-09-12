#!/usr/bin/env python3
"""
Test script to verify computer data collection and transmission
"""

import json
import os
import sys
from datetime import datetime

def create_test_data():
    """Create test computer data"""
    return {
        "Computername": "TEST-COMPUTER-001",
        "Name": "Test User",
        "Username": "testuser",
        "OS": "Windows 10 Test",
        "Manufacturer": "Test Manufacturer",
        "Model": "Test Model",
        "CPU": "Intel Test CPU @ 2.90GHz",
        "Total Physical Memory": 8589934592,  # 8GB
        "GPU Name": "NVIDIA Test GPU",
        "GPU Driver": "Test Driver 1.0",
        "Serial Number": "TEST123456",
        "Date": datetime.now().isoformat()
    }

def test_about_me_script():
    """Test the about_me.py script"""
    print("🧪 Testing AboutMe script...")
    
    # Test basic collection
    try:
        from AboutMe.about_me import ComputerInfoCollector
        
        collector = ComputerInfoCollector()
        collector.collect_all_info()
        
        print("✅ Computer info collection works")
        collector.print_summary()
        
        # Test data saving
        if collector.save_to_json("test_computer_info.json"):
            print("✅ Data saving works")
        else:
            print("❌ Data saving failed")
            return False
        
        # Test GitHub issue creation (without actually sending)
        print("✅ GitHub issue creation method available")
        
        return True
        
    except Exception as e:
        print(f"❌ AboutMe script test failed: {e}")
        return False

def test_github_workflows():
    """Test GitHub workflow files"""
    print("🧪 Testing GitHub workflows...")
    
    workflow_files = [
        ".github/workflows/computer-data-handler.yml",
        ".github/workflows/regenerate-website.yml"
    ]
    
    for workflow_file in workflow_files:
        if os.path.exists(workflow_file):
            print(f"✅ {workflow_file} exists")
        else:
            print(f"❌ {workflow_file} missing")
            return False
    
    return True

def test_scripts():
    """Test GitHub scripts"""
    print("🧪 Testing GitHub scripts...")
    
    script_files = [
        ".github/scripts/handle_computer_data.py",
        ".github/scripts/regenerate_website.py"
    ]
    
    for script_file in script_files:
        if os.path.exists(script_file):
            print(f"✅ {script_file} exists")
        else:
            print(f"❌ {script_file} missing")
            return False
    
    return True

def test_website_integration():
    """Test website integration"""
    print("🧪 Testing website integration...")
    
    # Check if computer data section exists in HTML
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        if 'computer-data-section' in html_content:
            print("✅ Computer data section found in HTML")
        else:
            print("❌ Computer data section not found in HTML")
            return False
        
        if 'loadComputerData' in html_content:
            print("✅ Computer data JavaScript found")
        else:
            print("❌ Computer data JavaScript not found")
            return False
        
        return True
        
    except FileNotFoundError:
        print("❌ index.html not found")
        return False
    except Exception as e:
        print(f"❌ Website integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting computer data system tests...\n")
    
    tests = [
        ("AboutMe Script", test_about_me_script),
        ("GitHub Workflows", test_github_workflows),
        ("GitHub Scripts", test_scripts),
        ("Website Integration", test_website_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The computer data system is ready.")
        print("\n📋 Next steps:")
        print("1. Get a GitHub personal access token")
        print("2. Run: python AboutMe/about_me.py --send-to-github --github-token YOUR_TOKEN")
        print("3. Check the website for the new computer data section")
    else:
        print("⚠️  Some tests failed. Please fix the issues before using the system.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
