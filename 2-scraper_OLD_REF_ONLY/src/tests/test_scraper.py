#!/usr/bin/env python3
"""
Test script for the weekly scraper
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.individual_data_orchestrator import IndividualDataOrchestrator
from src.config.settings import ScraperConfig

async def test_scraper():
    """Test the scraper with a small number of employees"""
    print("🧪 Testing Weekly Scraper")
    print("=" * 40)
    
    try:
        # Configure for testing
        config = ScraperConfig.from_env()
        config.HEADLESS = "true"
        config.DOWNLOAD_IMAGES = False  # Skip images for testing
        config.TIMEOUT = 10000
        
        # Create orchestrator
        orchestrator = IndividualDataOrchestrator(config)
        
        print("🕷️  Testing employee scraping...")
        new_employees = await orchestrator.scrape_employees()
        print(f"✅ Scraped {len(new_employees)} employees")
        
        if new_employees:
            print("🔄 Testing individual employee processing...")
            processed_count = 0
            for employee in new_employees[:3]:  # Test with first 3 employees
                if await orchestrator.process_employee(employee):
                    processed_count += 1
                    print(f"✅ Processed {employee.get('human_name', 'Unknown')}")
                else:
                    print(f"❌ Failed to process {employee.get('human_name', 'Unknown')}")
            
            print(f"✅ Successfully processed {processed_count} employees")
        else:
            print("⚠️  No new employees scraped")
        
        print("🎉 Scraper test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_scraper())
    sys.exit(0 if success else 1)
