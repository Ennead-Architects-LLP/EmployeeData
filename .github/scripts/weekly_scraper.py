#!/usr/bin/env python3
"""
Weekly Employee Data Scraper
Wrapper around main.py for GitHub Actions
Runs weekly on Tuesday at 3:14 AM EST
"""

import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path

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

def main():
    """Main function for weekly scraper - just calls main.py"""
    print("🚀 Weekly Employee Data Scraper")
    print("Schedule: Tuesday at 3:14 AM EST")
    print("Focus: Data collection and JSON updates only")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Call main.py with appropriate flags for GitHub Actions
        logger.info(f"Starting weekly scraper at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Credential priority: GitHub secrets -> local credentials.json -> GUI setup")
        
        # Run main.py with headless mode and image downloading
        # Change to 2-scraper directory where src.main is located
        scraper_dir = Path(__file__).parent.parent.parent / "2-scraper"
        result = subprocess.run([
            sys.executable, "-m", "src.main",
            "--headless=true",
            "--timeout=15000"
        ], cwd=scraper_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Weekly scraper completed successfully!")
            print("[SUCCESS] Weekly scraper completed successfully!")
            print(result.stdout)
            return 0
        else:
            logger.error("Weekly scraper failed!")
            print("[ERROR] Weekly scraper failed!")
            print("[ERROR] STDOUT:", result.stdout)
            print("[ERROR] STDERR:", result.stderr)
            return 1
            
    except Exception as e:
        logger.error(f"Weekly scraper failed with exception: {e}")
        print(f"[ERROR] Weekly scraper failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())