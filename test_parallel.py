#!/usr/bin/env python3
"""
Enhanced test script for parallel employee scraping with comprehensive debugging.

This script demonstrates the parallel processing capabilities with different worker counts
and provides detailed performance analysis and debugging information.
"""

import asyncio
import time
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.complete_scraper import CompleteScraper
from src.config.settings import ScraperConfig


class TestLogger:
    """Enhanced logger for test operations with performance tracking."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.performance_data = []
        self.logger = logging.getLogger(f"test_{test_name}")
        
        # Setup logging
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f'%(asctime)s - {test_name} - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_performance(self, operation: str, duration: float, success: bool, **kwargs):
        """Log performance metrics for an operation."""
        self.performance_data.append({
            'operation': operation,
            'duration': duration,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        })
        self.logger.info(f"Performance: {operation} - {duration:.2f}s - {'SUCCESS' if success else 'FAILED'}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        total_duration = time.time() - self.start_time
        successful_ops = sum(1 for op in self.performance_data if op['success'])
        total_ops = len(self.performance_data)
        
        return {
            'test_name': self.test_name,
            'total_duration': total_duration,
            'total_operations': total_ops,
            'successful_operations': successful_ops,
            'success_rate': (successful_ops / total_ops * 100) if total_ops > 0 else 0,
            'performance_data': self.performance_data
        }


async def test_scraper_configuration(config: ScraperConfig, test_logger: TestLogger) -> bool:
    """Test scraper configuration and setup."""
    try:
        test_logger.logger.info("Testing scraper configuration...")
        
        # Test directory setup
        config.setup_directories()
        test_logger.log_performance("directory_setup", 0.1, True)
        
        # Test debug directories if in debug mode
        if config.DEBUG_MODE:
            config.setup_debug_directories()
            test_logger.log_performance("debug_directory_setup", 0.1, True)
        
        # Validate configuration
        if not config.BASE_URL:
            raise ValueError("BASE_URL not configured")
        
        test_logger.logger.info("✅ Configuration test passed")
        return True
        
    except Exception as e:
        test_logger.logger.error(f"❌ Configuration test failed: {e}")
        test_logger.log_performance("configuration_test", 0.1, False, error=str(e))
        return False


async def test_parallel_scraping():
    """Test parallel scraping with different worker counts and comprehensive analysis."""
    
    print("🧪 Enhanced Parallel Employee Scraping Test")
    print("=" * 60)
    
    # Test configurations
    test_configs = [
        {"workers": 1, "name": "Sequential", "description": "Single worker (baseline)"},
        {"workers": 2, "name": "Parallel-2", "description": "Two parallel workers"},
        {"workers": 3, "name": "Parallel-3", "description": "Three parallel workers"},
    ]
    
    all_results = []
    
    for test_config in test_configs:
        worker_count = test_config["workers"]
        test_name = test_config["name"]
        description = test_config["description"]
        
        print(f"\n🔧 Testing {test_name} ({description})...")
        print("-" * 40)
        
        # Create test logger
        test_logger = TestLogger(test_name)
        
        try:
            # Setup configuration
            config = ScraperConfig.from_env()
            config.DEBUG_MODE = True
            config.DEBUG_MAX_EMPLOYEES = 5  # Small number for fast testing
            config.DOWNLOAD_IMAGES = False  # Skip images for faster testing
            config.LOG_LEVEL = "INFO"
            
            # Test configuration first
            config_ok = await test_scraper_configuration(config, test_logger)
            if not config_ok:
                continue
            
            # Create scraper
            scraper = CompleteScraper(config)
            test_logger.log_performance("scraper_creation", 0.1, True)
            
            # Run scraping test
            start_time = time.time()
            
            if worker_count == 1:
                # Use sequential method for comparison
                employees = await scraper.scrape_all_employees_incremental()
                method = "sequential"
            else:
                # Use parallel method
                employees = await scraper.scrape_all_employees_parallel(max_parallel_workers=worker_count)
                method = "parallel"
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Log performance
            test_logger.log_performance(
                f"scraping_{method}",
                duration,
                True,
                employees_count=len(employees),
                workers=worker_count
            )
            
            print(f"   ✅ Completed: {len(employees)} employees in {duration:.2f} seconds")
            print(f"   📊 Rate: {len(employees)/duration:.2f} employees/second")
            
            # Verify task completion
            verification = await scraper.verify_all_tasks_completed(5, employees)
            completion_rate = verification['completion_rate']
            all_completed = verification['all_tasks_completed']
            
            test_logger.log_performance(
                "verification",
                0.1,
                all_completed,
                completion_rate=completion_rate
            )
            
            print(f"   🔍 Completion rate: {completion_rate:.1f}%")
            print(f"   ✅ All tasks completed: {'YES' if all_completed else 'NO'}")
            
            # Store results
            result = {
                'test_name': test_name,
                'workers': worker_count,
                'duration': duration,
                'employees_count': len(employees),
                'rate': len(employees)/duration if duration > 0 else 0,
                'completion_rate': completion_rate,
                'all_completed': all_completed,
                'method': method,
                'performance_summary': test_logger.get_summary()
            }
            all_results.append(result)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            test_logger.log_performance("scraping_test", 0.1, False, error=str(e))
            
            # Store failed result
            result = {
                'test_name': test_name,
                'workers': worker_count,
                'error': str(e),
                'success': False,
                'performance_summary': test_logger.get_summary()
            }
            all_results.append(result)
    
    # Generate comprehensive report
    print("\n📊 COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    # Performance comparison
    successful_results = [r for r in all_results if 'error' not in r]
    if successful_results:
        print("\n🏆 Performance Comparison:")
        print("-" * 30)
        for result in successful_results:
            print(f"  {result['test_name']:12} | {result['duration']:6.2f}s | {result['rate']:6.2f} emp/s | {result['completion_rate']:5.1f}% complete")
        
        # Find best performer
        best_rate = max(successful_results, key=lambda x: x['rate'])
        best_completion = max(successful_results, key=lambda x: x['completion_rate'])
        
        print(f"\n🥇 Fastest: {best_rate['test_name']} ({best_rate['rate']:.2f} employees/second)")
        print(f"🎯 Most Complete: {best_completion['test_name']} ({best_completion['completion_rate']:.1f}% completion)")
    
    # Error summary
    failed_results = [r for r in all_results if 'error' in r]
    if failed_results:
        print(f"\n❌ Failed Tests: {len(failed_results)}")
        for result in failed_results:
            print(f"  {result['test_name']}: {result['error']}")
    
    # Save detailed report
    report_path = Path("test_results.json")
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'test_results': all_results,
            'summary': {
                'total_tests': len(all_results),
                'successful_tests': len(successful_results),
                'failed_tests': len(failed_results)
            }
        }, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_path}")
    print("\n🎉 Enhanced parallel testing completed!")


async def test_debug_capabilities():
    """Test debug capabilities and content analysis."""
    
    print("\n🔍 Testing Debug Capabilities")
    print("=" * 40)
    
    config = ScraperConfig.from_env()
    config.DEBUG_MODE = True
    config.DEBUG_MAX_EMPLOYEES = 3
    config.DEBUG_DOM_CAPTURE = True
    config.DOWNLOAD_IMAGES = False
    
    test_logger = TestLogger("debug_test")
    
    try:
        # Setup debug directories
        config.setup_debug_directories()
        test_logger.logger.info("Debug directories created")
        
        # Test scraper with debug mode
        scraper = CompleteScraper(config)
        
        # Test DOM capture functionality
        test_logger.logger.info("Testing DOM capture functionality...")
        
        # This would normally require a browser context, but we can test the setup
        debug_output_path = config.get_debug_output_path()
        dom_captures_dir = debug_output_path / "dom_captures"
        screenshots_dir = debug_output_path / "screenshots"
        
        if dom_captures_dir.exists() and screenshots_dir.exists():
            test_logger.logger.info("✅ Debug directories properly created")
            test_logger.log_performance("debug_setup", 0.1, True)
        else:
            test_logger.logger.error("❌ Debug directories not created properly")
            test_logger.log_performance("debug_setup", 0.1, False)
        
        print("   ✅ Debug capabilities test completed")
        
    except Exception as e:
        print(f"   ❌ Debug test error: {e}")
        test_logger.log_performance("debug_test", 0.1, False, error=str(e))


if __name__ == "__main__":
    async def main():
        """Main test runner."""
        print("🚀 Starting Enhanced Employee Scraper Tests")
        print("=" * 60)
        
        # Run parallel scraping tests
        await test_parallel_scraping()
        
        # Run debug capability tests
        await test_debug_capabilities()
        
        print("\n✨ All tests completed!")
    
    asyncio.run(main())