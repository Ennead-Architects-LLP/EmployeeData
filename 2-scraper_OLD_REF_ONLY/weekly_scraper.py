#!/usr/bin/env python3
"""
Weekly Employee Data Scraper
Focuses only on data collection and JSON updates, no HTML generation
Runs weekly on Tuesday at 3:14 AM EST
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
    """Setup logging for the weekly scraper"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('weekly_scraper.log')
        ]
    )

async def main():
    """Main function for weekly scraper"""
    print("🚀 Weekly Employee Data Scraper")
    print("Schedule: Tuesday at 3:14 AM EST")
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
        logger.info(f"Starting weekly scraper at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Credential priority: GitHub secrets -> local credentials.json -> GUI setup")
        success = await orchestrator.run()
        
        if success:
            logger.info("Weekly scraper completed successfully!")
            print("[SUCCESS] Weekly scraper completed successfully!")
            return 0
        else:
            logger.error("Weekly scraper failed!")
            print("[ERROR] Weekly scraper failed!")
            print("[ERROR] Check the logs above for detailed error information")
            return 1
            
    except Exception as e:
        logger.error(f"Weekly scraper failed with exception: {e}")
        print(f"[ERROR] Weekly scraper failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))