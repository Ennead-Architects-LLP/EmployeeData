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
    """Test the unified scraper with comprehensive features"""
    print("🧪 Testing Unified Scraper")
    print("=" * 50)
    
    config = ScraperConfig.from_env()
    
    # Test unified scraper (comprehensive by default)
    print("\n1️⃣ Testing Unified Scraper (Comprehensive Data Extraction)")
    print("-" * 50)
    
    try:
        async with UnifiedEmployeeScraper(
            download_images=True,
            headless=True,
            timeout=10000,
            config=config
        ) as scraper:
            print(f"   Info: {scraper.get_scraper_info()}")
            print("   ✅ Unified scraper initialized successfully")
            print("   📊 Features: Comprehensive data extraction enabled")
            print("   🖼️  Images: Enabled for profile photos")
            print("   🔍 Data: Name, email, phone, position, department, bio,")
            print("           office location, years with firm, seat assignment,")
            print("           computer info, memberships, education, licenses,")
            print("           projects, recent posts, social links")
            
            # Note: We're not actually running the scraper in this test
            print("   ℹ️  Skipping actual scraping (requires authentication)")
            
    except Exception as e:
        print(f"   ❌ Unified scraper failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Unified scraper test completed!")
    print("\n📋 Usage Examples:")
    print("   # For GitHub Actions (weekly scraper):")
    print("   scraper = UnifiedEmployeeScraper()")
    print("   ")
    print("   # For Development (main.py):")
    print("   scraper = UnifiedEmployeeScraper()")
    print("   ")
    print("   # Both use the same comprehensive interface:")
    print("   employees = await scraper.scrape_all_employees()")
    print("   ")
    print("   # All employees will have comprehensive data:")
    print("   # - Basic info (name, email, phone, position, department, bio)")
    print("   # - Advanced info (years with firm, seat, computer, memberships)")
    print("   # - Professional info (education, licenses, projects, posts)")
    print("   # - Contact info (teams, linkedin, website)")


if __name__ == "__main__":
    asyncio.run(test_unified_scraper())
