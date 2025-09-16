#!/usr/bin/env python3
"""
Test Runner: Run All Test Scenarios

This script runs all available test scenarios for the Employee Data Scraper.
It provides options to run individual tests or all tests in sequence.

Usage:
    # Run all tests
    python -m tests.run_all_tests
    
    # Run specific test
    python -m tests.run_all_tests --test production_full
    
    # Run tests with custom parameters
    python -m tests.run_all_tests --debug-employees 5 --headless
    
    # List available tests
    python -m tests.run_all_tests --list
"""

import asyncio
import sys
import time
import argparse
from pathlib import Path
import logging
from typing import Dict, List, Any

# Setup logging for test runner
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestRunner:
    """Main test runner class."""
    
    def __init__(self):
        self.test_modules = {
            "production_full": {
                "module": "test_production_full_scraping_without_browser",
                "description": "Production full scraping without browser",
                "category": "production"
            },
            "debug_limited": {
                "module": "test_debugging_limited_employee_with_DOM_with_browser", 
                "description": "Debug limited employees with DOM and browser",
                "category": "debug"
            },
            "quick_debug": {
                "module": "test_quick_debug_no_images",
                "description": "Quick debug without images (fast)",
                "category": "debug"
            },
            "production_headless": {
                "module": "test_production_headless_with_images",
                "description": "Production headless with images",
                "category": "production"
            },
            "credentials": {
                "module": "test_credentials_setup",
                "description": "Credentials setup test",
                "category": "setup"
            }
        }
        
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def list_tests(self):
        """List all available tests."""
        print("="*80)
        print("AVAILABLE TEST SCENARIOS")
        print("="*80)
        
        categories = {}
        for test_id, test_info in self.test_modules.items():
            category = test_info["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((test_id, test_info["description"]))
        
        for category, tests in categories.items():
            print(f"\n{category.upper()} TESTS:")
            for test_id, description in tests:
                print(f"  - {test_id}: {description}")
        
        print(f"\nTotal tests: {len(self.test_modules)}")
        print("="*80)
    
    def log_runner_start(self, test_ids: List[str], args: Any):
        """Log test runner start information."""
        self.start_time = time.time()
        logger.info("="*80)
        logger.info("🚀 STARTING TEST RUNNER")
        logger.info("="*80)
        logger.info(f"Tests to run: {len(test_ids)}")
        logger.info(f"Test IDs: {', '.join(test_ids)}")
        logger.info(f"Custom parameters:")
        if args.debug_employees:
            logger.info(f"  - debug-employees: {args.debug_employees}")
        if args.headless:
            logger.info(f"  - headless: {args.headless}")
        if args.no_images:
            logger.info(f"  - no-images: {args.no_images}")
        if args.timeout:
            logger.info(f"  - timeout: {args.timeout}")
        logger.info("="*80)
    
    def log_runner_end(self):
        """Log test runner end information."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time if self.start_time else 0
        
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = len(self.test_results) - successful_tests
        
        logger.info("="*80)
        logger.info("🏁 TEST RUNNER COMPLETED")
        logger.info("="*80)
        logger.info(f"Total duration: {duration:.2f} seconds")
        logger.info(f"Tests run: {len(self.test_results)}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success rate: {(successful_tests/len(self.test_results)*100):.1f}%")
        
        # Detailed results
        logger.info("\nDETAILED RESULTS:")
        for test_id, result in self.test_results.items():
            status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            duration = result.get("duration", 0)
            logger.info(f"  - {test_id}: {status} ({duration:.2f}s)")
            if not result["success"] and result.get("error"):
                logger.error(f"    Error: {result['error']}")
        
        logger.info("="*80)
        
        return successful_tests == len(self.test_results)
    
    async def run_single_test(self, test_id: str, args: Any) -> Dict[str, Any]:
        """Run a single test scenario."""
        if test_id not in self.test_modules:
            return {
                "success": False,
                "error": f"Test '{test_id}' not found",
                "duration": 0
            }
        
        test_info = self.test_modules[test_id]
        module_name = test_info["module"]
        
        logger.info(f"🧪 Running test: {test_id} ({test_info['description']})")
        
        start_time = time.time()
        
        try:
            # Build command for the test
            cmd = [
                sys.executable, "-m", f"tests.{module_name}"
            ]
            
            # Add custom parameters based on test type
            if test_id in ["debug_limited", "quick_debug"] and args.debug_employees:
                cmd.append(f"--debug-employees={args.debug_employees}")
            
            if test_id == "debug_limited" and args.headless is not None:
                if args.headless:
                    cmd.append("--headless")
            
            if test_id in ["debug_limited", "quick_debug"] and args.no_images:
                cmd.append("--no-images")
            
            if args.timeout:
                cmd.append(f"--timeout={args.timeout}")
            
            if args.base_url:
                cmd.append(f"--base-url={args.base_url}")
            
            # Run the test
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(__file__).parent.parent  # Run from 2-scraper directory
            )
            
            stdout, stderr = await process.communicate()
            return_code = process.returncode
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = return_code == 0
            error_msg = stderr.decode().strip() if not success else None
            
            logger.info(f"Test {test_id} {'completed successfully' if success else 'failed'}")
            
            return {
                "success": success,
                "error": error_msg,
                "duration": duration,
                "return_code": return_code,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip()
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(f"Failed to run test {test_id}: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "duration": duration
            }
    
    async def run_tests(self, test_ids: List[str], args: Any) -> bool:
        """Run multiple test scenarios."""
        self.log_runner_start(test_ids, args)
        
        # Run tests sequentially
        for test_id in test_ids:
            result = await self.run_single_test(test_id, args)
            self.test_results[test_id] = result
        
        # Log final results
        return self.log_runner_end()


async def main():
    """Main function to run the test runner."""
    parser = argparse.ArgumentParser(description="Run test scenarios for Employee Data Scraper")
    
    # Test selection
    parser.add_argument("--test", type=str, help="Run specific test (use --list to see available tests)")
    parser.add_argument("--list", action="store_true", help="List all available tests")
    
    # Test parameters
    parser.add_argument("--debug-employees", type=int, help="Number of employees for debug tests")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode for debug tests")
    parser.add_argument("--no-images", action="store_true", help="Skip downloading images")
    parser.add_argument("--timeout", type=int, help="Custom timeout in milliseconds")
    parser.add_argument("--base-url", type=str, help="Custom base URL")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Handle list command
    if args.list:
        runner.list_tests()
        return
    
    # Determine which tests to run
    if args.test:
        if args.test not in runner.test_modules:
            print(f"Error: Test '{args.test}' not found. Use --list to see available tests.")
            sys.exit(1)
        test_ids = [args.test]
    else:
        # Run all tests by default
        test_ids = list(runner.test_modules.keys())
    
    # Run the tests
    success = await runner.run_tests(test_ids, args)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
