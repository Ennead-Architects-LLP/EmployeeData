#!/usr/bin/env python3
"""
Test script to verify scraper paths work correctly
Run this from the 2-scraper directory to test path resolution
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core.orchestrator import ScraperOrchestrator
from src.config.settings import ScraperConfig

def test_paths():
    """Test that the orchestrator creates the correct paths"""
    print("🧪 Testing scraper path resolution...")
    print(f"Current working directory: {Path.cwd()}")
    print(f"Script location: {Path(__file__).parent}")
    
    try:
        # Create orchestrator
        config = ScraperConfig.from_env()
        orchestrator = ScraperOrchestrator(config)
        
        # Test that the orchestrator can be created
        print(f"✅ Orchestrator created successfully")
        print(f"✅ Configuration: {orchestrator.config.BASE_URL}")
        print(f"✅ Headless mode: {orchestrator.config.HEADLESS}")
        
        # Check if paths are relative to project root
        project_root = Path(__file__).parent.parent
        expected_docs_path = project_root / "docs" / "assets"
        
        if orchestrator.output_path.resolve() == expected_docs_path.resolve():
            print("✅ Path resolution is correct - points to docs/assets")
        else:
            print(f"❌ Path resolution issue:")
            print(f"   Expected: {expected_docs_path.resolve()}")
            print(f"   Actual: {orchestrator.output_path.resolve()}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing paths: {e}")
        return False

if __name__ == "__main__":
    success = test_paths()
    if success:
        print("\n🎉 Path test passed! Scraper should work correctly.")
    else:
        print("\n💥 Path test failed! Check the path resolution.")
        sys.exit(1)
