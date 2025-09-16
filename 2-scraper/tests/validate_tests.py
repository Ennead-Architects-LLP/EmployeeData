#!/usr/bin/env python3
"""
Validation script for the test suite.

This script validates that all test files are properly structured
and can be imported without errors.
"""

import sys
import importlib
from pathlib import Path

def validate_test_structure():
    """Validate the test directory structure."""
    tests_dir = Path(__file__).parent
    
    print("🔍 Validating test directory structure...")
    
    required_files = [
        "__init__.py",
        "test_production_full_scraping_without_browser.py",
        "test_debugging_limited_employee_with_DOM_with_browser.py", 
        "test_quick_debug_no_images.py",
        "test_production_headless_with_images.py",
        "test_credentials_setup.py",
        "run_all_tests.py",
        "conftest.py",
        "requirements.txt",
        "README.md"
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = tests_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)
        else:
            print(f"  ✅ {file_name}")
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    else:
        print("  ✅ All required files present")
        return True

def validate_test_imports():
    """Validate that test modules can be imported."""
    tests_dir = Path(__file__).parent
    sys.path.insert(0, str(tests_dir))
    
    print("\n🔍 Validating test module imports...")
    
    test_modules = [
        "test_production_full_scraping_without_browser",
        "test_debugging_limited_employee_with_DOM_with_browser",
        "test_quick_debug_no_images", 
        "test_production_headless_with_images",
        "test_credentials_setup",
        "run_all_tests"
    ]
    
    failed_imports = []
    for module_name in test_modules:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")
            failed_imports.append(module_name)
        except Exception as e:
            print(f"  ⚠️  {module_name}: {e}")
    
    if failed_imports:
        print(f"  ❌ Failed imports: {failed_imports}")
        return False
    else:
        print("  ✅ All test modules can be imported")
        return True

def validate_test_classes():
    """Validate that test classes exist and have required methods."""
    print("\n🔍 Validating test class structure...")
    
    test_classes = [
        ("test_production_full_scraping_without_browser", "ProductionFullScrapingTest"),
        ("test_debugging_limited_employee_with_DOM_with_browser", "DebuggingLimitedEmployeeTest"),
        ("test_quick_debug_no_images", "QuickDebugNoImagesTest"),
        ("test_production_headless_with_images", "ProductionHeadlessWithImagesTest"),
        ("test_credentials_setup", "CredentialsSetupTest"),
        ("run_all_tests", "TestRunner")
    ]
    
    failed_classes = []
    for module_name, class_name in test_classes:
        try:
            module = importlib.import_module(module_name)
            test_class = getattr(module, class_name, None)
            if test_class is None:
                print(f"  ❌ {module_name}: Class {class_name} not found")
                failed_classes.append(f"{module_name}.{class_name}")
            else:
                # Check for required methods
                required_methods = ["run_test", "log_test_start", "log_test_end"]
                missing_methods = []
                for method_name in required_methods:
                    if not hasattr(test_class, method_name):
                        missing_methods.append(method_name)
                
                if missing_methods:
                    print(f"  ⚠️  {module_name}: Missing methods {missing_methods}")
                else:
                    print(f"  ✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            failed_classes.append(f"{module_name}.{class_name}")
    
    if failed_classes:
        print(f"  ❌ Failed classes: {failed_classes}")
        return False
    else:
        print("  ✅ All test classes are properly structured")
        return True

def validate_configuration():
    """Validate configuration files."""
    print("\n🔍 Validating configuration files...")
    
    tests_dir = Path(__file__).parent
    
    # Check conftest.py
    conftest_path = tests_dir / "conftest.py"
    if conftest_path.exists():
        try:
            with open(conftest_path, 'r') as f:
                content = f.read()
                if "TestConfig" in content and "TestRunner" in content:
                    print("  ✅ conftest.py contains required classes")
                else:
                    print("  ⚠️  conftest.py may be missing required classes")
        except Exception as e:
            print(f"  ❌ Error reading conftest.py: {e}")
    else:
        print("  ❌ conftest.py not found")
    
    # Check requirements.txt
    requirements_path = tests_dir / "requirements.txt"
    if requirements_path.exists():
        try:
            with open(requirements_path, 'r') as f:
                content = f.read()
                if "pytest" in content:
                    print("  ✅ requirements.txt contains pytest")
                else:
                    print("  ⚠️  requirements.txt may be missing pytest")
        except Exception as e:
            print(f"  ❌ Error reading requirements.txt: {e}")
    else:
        print("  ❌ requirements.txt not found")
    
    return True

def main():
    """Run all validation checks."""
    print("🚀 EMPLOYEE DATA SCRAPER - TEST VALIDATION")
    print("="*60)
    
    checks = [
        validate_test_structure,
        validate_test_imports,
        validate_test_classes,
        validate_configuration
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Validation check failed: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    check_names = [
        "Test Structure",
        "Module Imports", 
        "Class Structure",
        "Configuration"
    ]
    
    for i, (name, result) in enumerate(zip(check_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    total_checks = len(results)
    passed_checks = sum(results)
    
    print(f"\nTotal checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    
    if passed_checks == total_checks:
        print("\n🎉 All validations passed! The test suite is ready to use.")
        print("\nNext steps:")
        print("1. Install test dependencies: pip install -r tests/requirements.txt")
        print("2. Run individual tests: python -m tests.test_quick_debug_no_images")
        print("3. Run all tests: python -m tests.run_all_tests")
        print("4. See available tests: python -m tests.run_all_tests --list")
        return True
    else:
        print(f"\n⚠️  {total_checks - passed_checks} validation(s) failed.")
        print("Please check the errors above and fix them before running tests.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
