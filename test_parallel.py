#!/usr/bin/env python3
"""
Test script for parallel employee scraping.

This script demonstrates the parallel processing capabilities with different worker counts.
"""

import asyncio
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.complete_scraper import CompleteScraper
from src.config.settings import ScraperConfig


async def test_parallel_scraping():
    """Test parallel scraping with different worker counts."""
    
    print("🧪 Testing Parallel Employee Scraping")
    print("=" * 50)
    
    # Test with different worker counts
    worker_counts = [1, 2, 3]
    
    for worker_count in worker_counts:
        print(f"\n🔧 Testing with {worker_count} worker(s)...")
        
        config = ScraperConfig.from_env()
        config.DEBUG_MODE = True
        config.DEBUG_MAX_EMPLOYEES = 10  # Limit for testing
        config.DOWNLOAD_IMAGES = False  # Skip images for faster testing
        
        scraper = CompleteScraper(config)
        
        start_time = time.time()
        
        try:
            if worker_count == 1:
                # Use sequential method for comparison
                employees = await scraper.scrape_all_employees_incremental()
            else:
                # Use parallel method
                employees = await scraper.scrape_all_employees_parallel(max_parallel_workers=worker_count)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"   ✅ Completed: {len(employees)} employees in {duration:.2f} seconds")
            print(f"   📊 Rate: {len(employees)/duration:.2f} employees/second")
            
            # Verify task completion
            verification = await scraper.verify_all_tasks_completed(10, employees)
            print(f"   🔍 Completion rate: {verification['completion_rate']:.1f}%")
            print(f"   ✅ All tasks completed: {'YES' if verification['all_tasks_completed'] else 'NO'}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🎉 Parallel testing completed!")


if __name__ == "__main__":
    asyncio.run(test_parallel_scraping())
