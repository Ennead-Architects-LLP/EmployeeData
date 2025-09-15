#!/usr/bin/env python3
"""
Demo script showing how to run the test scenarios.

This script demonstrates different ways to run the test scenarios
and provides examples of common usage patterns.
"""

import asyncio
import sys
from pathlib import Path

# Add the tests directory to the path
sys.path.insert(0, str(Path(__file__).parent))

async def demo_quick_test():
    """Demo: Run a quick debug test."""
    print("="*60)
    print("DEMO: Quick Debug Test (3 employees, no images, fast)")
    print("="*60)
    
    from test_quick_debug_no_images import QuickDebugNoImagesTest
    
    test = QuickDebugNoImagesTest()
    success = await test.run_test(debug_employees=3)
    
    print(f"Quick test result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success


async def demo_debug_test():
    """Demo: Run a debug test with DOM capture."""
    print("="*60)
    print("DEMO: Debug Test (5 employees, DOM capture, visible browser)")
    print("="*60)
    
    from test_debugging_limited_employee_with_DOM_with_browser import DebuggingLimitedEmployeeTest
    
    test = DebuggingLimitedEmployeeTest()
    success = await test.run_test(
        debug_employees=5,
        headless=True,  # Set to False to see browser
        dom_capture=True
    )
    
    print(f"Debug test result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success


async def demo_production_test():
    """Demo: Run a production test (limited for demo)."""
    print("="*60)
    print("DEMO: Production Test (headless, with images)")
    print("="*60)
    
    from test_production_headless_with_images import ProductionHeadlessWithImagesTest
    
    test = ProductionHeadlessWithImagesTest()
    success = await test.run_test()
    
    print(f"Production test result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success


async def demo_credentials_test():
    """Demo: Run credentials setup test."""
    print("="*60)
    print("DEMO: Credentials Setup Test")
    print("="*60)
    
    from test_credentials_setup import CredentialsSetupTest
    
    test = CredentialsSetupTest()
    success = await test.run_test()
    
    print(f"Credentials test result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success


async def main():
    """Run demo tests."""
    print("🚀 EMPLOYEE DATA SCRAPER - TEST DEMO")
    print("="*60)
    print("This demo shows different test scenarios in action.")
    print("Each test demonstrates a different configuration.")
    print("="*60)
    
    results = {}
    
    try:
        # Run quick test first (fastest)
        print("\n1. Running Quick Debug Test...")
        results['quick'] = await demo_quick_test()
        
        # Run debug test with DOM capture
        print("\n2. Running Debug Test with DOM Capture...")
        results['debug'] = await demo_debug_test()
        
        # Run credentials test
        print("\n3. Running Credentials Setup Test...")
        results['credentials'] = await demo_credentials_test()
        
        # Note: Production test is commented out for demo to avoid long execution
        # Uncomment to run production test
        # print("\n4. Running Production Test...")
        # results['production'] = await demo_production_test()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        return
    
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        return
    
    # Summary
    print("\n" + "="*60)
    print("DEMO SUMMARY")
    print("="*60)
    
    for test_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{test_name.capitalize()} test: {status}")
    
    total_tests = len(results)
    successful_tests = sum(results.values())
    
    print(f"\nTotal tests run: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {(successful_tests/total_tests*100):.1f}%")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Check the generated files in the output directories")
    print("2. Review the debug/scraper.log for detailed execution logs")
    print("3. Use the individual test scripts for specific scenarios")
    print("4. Run 'python -m tests.run_all_tests --list' to see all available tests")
    print("5. Check the tests/README.md for detailed documentation")
    
    if successful_tests == total_tests:
        print("\n🎉 All demo tests passed! The test suite is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - successful_tests} test(s) failed. Check the logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
