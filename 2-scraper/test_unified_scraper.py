#!/usr/bin/env python3
"""
Test script for the unified scraper
Tests both SIMPLE and COMPLETE modes
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core.unified_scraper import UnifiedEmployeeScraper
from src.config.settings import ScraperConfig


async def test_unified_scraper():
    """Test the unified scraper in both modes"""
    print("🧪 Testing Unified Scraper")
    print("=" * 50)
    
    config = ScraperConfig.from_env()
    
    # Test SIMPLE mode
    print("\n1️⃣ Testing SIMPLE Mode (for GitHub Actions)")
    print("-" * 30)
    
    try:
        async with UnifiedEmployeeScraper(
            mode=UnifiedEmployeeScraper.MODE_SIMPLE,
            download_images=False,
            headless=True,
            timeout=10000,
            config=config
        ) as scraper:
            print(f"   Mode: {scraper.mode}")
            print(f"   Info: {scraper.get_mode_info()}")
            print("   ✅ SIMPLE mode initialized successfully")
            
            # Note: We're not actually running the scraper in this test
            # to avoid requiring authentication and network access
            print("   ℹ️  Skipping actual scraping (requires authentication)")
            
    except Exception as e:
        print(f"   ❌ SIMPLE mode failed: {e}")
    
    # Test COMPLETE mode
    print("\n2️⃣ Testing COMPLETE Mode (for Development)")
    print("-" * 30)
    
    try:
        async with UnifiedEmployeeScraper(
            mode=UnifiedEmployeeScraper.MODE_COMPLETE,
            download_images=True,
            headless=True,
            timeout=10000,
            config=config
        ) as scraper:
            print(f"   Mode: {scraper.mode}")
            print(f"   Info: {scraper.get_mode_info()}")
            print("   ✅ COMPLETE mode initialized successfully")
            
            # Note: We're not actually running the scraper in this test
            print("   ℹ️  Skipping actual scraping (requires authentication)")
            
    except Exception as e:
        print(f"   ❌ COMPLETE mode failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Unified scraper test completed!")
    print("\n📋 Usage Examples:")
    print("   # For GitHub Actions (weekly scraper):")
    print("   scraper = UnifiedEmployeeScraper(mode=UnifiedEmployeeScraper.MODE_SIMPLE)")
    print("   ")
    print("   # For Development (main.py):")
    print("   scraper = UnifiedEmployeeScraper(mode=UnifiedEmployeeScraper.MODE_COMPLETE)")
    print("   ")
    print("   # Both use the same interface:")
    print("   employees = await scraper.scrape_all_employees()")


if __name__ == "__main__":
    asyncio.run(test_unified_scraper())
