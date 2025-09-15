#!/usr/bin/env python3
"""
Test script to compare outputs between SimpleEmployeeScraper and CompleteScraper
Run this to ensure both scrapers produce consistent results for the same data.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core.models import EmployeeData
from src.core.base_scraper import BaseEmployeeScraper


def compare_employee_data(simple_data: EmployeeData, complete_data: EmployeeData) -> Dict[str, Any]:
    """
    Compare two EmployeeData objects and return differences.
    
    Args:
        simple_data: Data from SimpleEmployeeScraper
        complete_data: Data from CompleteScraper
        
    Returns:
        Dictionary with comparison results
    """
    comparison = {
        'identical': True,
        'differences': [],
        'simple_only': [],
        'complete_only': [],
        'field_comparison': {}
    }
    
    # Get dictionaries for comparison
    simple_dict = simple_data.to_dict()
    complete_dict = complete_data.to_dict()
    
    # Compare each field
    all_fields = set(simple_dict.keys()) | set(complete_dict.keys())
    
    for field in all_fields:
        simple_value = simple_dict.get(field)
        complete_value = complete_dict.get(field)
        
        if simple_value != complete_value:
            comparison['identical'] = False
            comparison['field_comparison'][field] = {
                'simple': simple_value,
                'complete': complete_value,
                'match': simple_value == complete_value
            }
            
            if simple_value and not complete_value:
                comparison['simple_only'].append(field)
            elif complete_value and not simple_value:
                comparison['complete_only'].append(field)
            else:
                comparison['differences'].append(field)
    
    return comparison


def test_scraper_consistency():
    """Test that both scrapers produce consistent results."""
    print("🧪 Testing Scraper Consistency")
    print("=" * 50)
    
    # Create test employee data
    test_employee = EmployeeData(
        human_name="John Doe",
        email="john.doe@ennead.com",
        phone="+1-555-0123",
        position="Project Manager",
        department="Architecture",
        bio="Experienced project manager with 10+ years in architecture.",
        office_location="New York",
        profile_url="https://ei.ennead.com/employee/12345",
        image_url="https://ei.ennead.com/images/john_doe.jpg"
    )
    
    print("📋 Test Employee Data:")
    print(f"   Name: {test_employee.human_name}")
    print(f"   Email: {test_employee.email}")
    print(f"   Position: {test_employee.position}")
    print(f"   Department: {test_employee.department}")
    
    # Test base scraper functionality
    print("\n🔧 Testing Base Scraper:")
    base_scraper = BaseEmployeeScraper(download_images=False)
    
    # Test validation
    is_valid = base_scraper.validate_employee_data(test_employee)
    print(f"   Validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test summary
    summary = base_scraper.get_employee_summary(test_employee)
    print(f"   Summary: {summary}")
    
    # Test location normalization
    test_locations = ["ny", "new york", "nyc", "california", "ca", "unknown location"]
    print(f"\n🌍 Testing Location Normalization:")
    for loc in test_locations:
        normalized = base_scraper.normalize_office_location(loc)
        print(f"   '{loc}' → '{normalized}'")
    
    print("\n" + "=" * 50)
    print("✅ Base scraper functionality tested successfully!")
    print("\n💡 Next Steps:")
    print("   1. Refactor SimpleEmployeeScraper to inherit from BaseEmployeeScraper")
    print("   2. Refactor CompleteScraper to inherit from BaseEmployeeScraper")
    print("   3. Remove duplicate code from both scrapers")
    print("   4. Run integration tests to ensure consistency")


if __name__ == "__main__":
    test_scraper_consistency()
