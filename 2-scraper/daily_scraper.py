#!/usr/bin/env python3
"""
Daily Employee Data Scraper
Focuses only on data collection and JSON updates, no HTML generation
"""

import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core.individual_data_orchestrator import IndividualDataOrchestrator
from src.config.settings import ScraperConfig

def setup_logging():
    """Setup logging for the daily scraper"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('daily_scraper.log')
        ]
    )

async def main():
    """Main function for daily scraper"""
    print("🚀 Daily Employee Data Scraper")
    print("Focus: Data collection and JSON updates only")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Configure scraper
        config = ScraperConfig.from_env()
        config.HEADLESS = "true"
        config.DOWNLOAD_IMAGES = True
        config.TIMEOUT = 15000
        
        # Create orchestrator
        orchestrator = IndividualDataOrchestrator(config)
        
        # Run data collection
        logger.info(f"Starting daily scraper at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Credential priority: GitHub secrets → local credentials.json → GUI setup")
        success = await orchestrator.run()
        
        if success:
            logger.info("Daily scraper completed successfully!")
            print("✅ Daily scraper completed successfully!")
            return 0
        else:
            logger.error("Daily scraper failed!")
            print("❌ Daily scraper failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Daily scraper failed with exception: {e}")
        print(f"❌ Daily scraper failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))