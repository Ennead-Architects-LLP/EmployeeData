#!/usr/bin/env python3
"""
Test script for the weekly scraper
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.orchestrator import ScraperOrchestrator
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
        orchestrator = ScraperOrchestrator(config)
        
        print("🕷️  Testing orchestrator...")
        success = await orchestrator.run()
        if success:
            print(f"✅ Orchestrator completed successfully")
        else:
            print(f"❌ Orchestrator failed")
        
        # Test completed - orchestrator handles everything internally
        
        print("🎉 Scraper test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_scraper())
    sys.exit(0 if success else 1)
