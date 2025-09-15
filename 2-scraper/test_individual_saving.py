#!/usr/bin/env python3
"""
Test script to verify individual JSON saving functionality.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.models import EmployeeData
from core.unified_scraper import UnifiedEmployeeScraper

async def test_individual_saving():
    """Test that individual JSON files are saved correctly."""
    print("🧪 Testing individual JSON saving functionality...")
    
    # Create a test employee
    test_employee = EmployeeData(
        human_name="Test Employee",
        email="test@example.com",
        position="Test Position",
        department="Test Department",
        bio="This is a test employee for verification",
        profile_url="https://example.com/test",
        image_url="https://example.com/test.jpg"
    )
    
    # Create scraper instance
    scraper = UnifiedEmployeeScraper(
        base_url="https://example.com",
        download_images=False,  # Disable for test
        headless=True
    )
    
    try:
        # Test the individual saving method
        saved_path = await scraper._save_individual_employee(test_employee)
        
        if saved_path and Path(saved_path).exists():
            print(f"✅ Individual JSON saved successfully: {saved_path}")
            
            # Verify content
            with open(saved_path, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                
            if data.get('human_name') == "Test Employee":
                print("✅ JSON content is correct")
                return True
            else:
                print("❌ JSON content is incorrect")
                return False
        else:
            print("❌ Failed to save individual JSON")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    finally:
        # Cleanup test file
        if saved_path and Path(saved_path).exists():
            Path(saved_path).unlink()
            print("🧹 Cleaned up test file")

if __name__ == "__main__":
    success = asyncio.run(test_individual_saving())
    if success:
        print("\n🎉 Individual JSON saving test PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Individual JSON saving test FAILED!")
        sys.exit(1)
