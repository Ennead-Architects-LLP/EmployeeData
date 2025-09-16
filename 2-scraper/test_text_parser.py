#!/usr/bin/env python3
"""
Test script for the new text-based section parser
"""

import asyncio
import logging
from src.core.unified_scraper import UnifiedEmployeeScraper

async def test_text_parser():
    """Test the new text-based section parser"""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Text-Based Section Parser")
    print("=" * 50)
    
    # Test with a sample employee URL
    test_url = "https://ei.ennead.com/employees/1/all-employees"
    
    async with UnifiedEmployeeScraper(
        base_url=test_url,
        download_images=False,
        headless=True,
        timeout=30000
    ) as scraper:
        print("✅ Scraper initialized")
        
        # Test the section parser directly
        print("\n🔍 Testing section parsing...")
        
        # Test education section parsing
        print("📚 Testing Education section parsing...")
        education_data = await scraper._parse_section_by_text("Education")
        print(f"   Education data: {education_data}")
        
        # Test licenses section parsing
        print("📜 Testing Licenses section parsing...")
        licenses_data = await scraper._parse_section_by_text("License")
        print(f"   Licenses data: {licenses_data}")
        
        # Test generic section parsing
        print("📋 Testing generic section parsing...")
        contact_data = await scraper._extract_section_data("Contact Info")
        print(f"   Contact data: {contact_data}")
        
        print("\n✅ Text-based parser test completed!")

if __name__ == "__main__":
    asyncio.run(test_text_parser())
