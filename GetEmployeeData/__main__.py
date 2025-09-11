#!/usr/bin/env python3
"""
Main entry point for the Employee Data Scraper.

This script scrapes employee data from the Ennead website including:
- Employee names, emails, contact information
- Profile images (downloaded locally)
- Bio and additional information
- Office locations (New York, Shanghai, California)
- Saves all data to JSON format

Usage Examples:
    # Normal scraping (all employees)
    python -m GetEmployeeData
    
    # Basic debug mode (10 employees + DOM capture)
    python -m GetEmployeeData --debug
    
    # Debug with custom employee limit
    python -m GetEmployeeData --debug --debug-employees 5
    
    # Debug without DOM capturing (faster)
    python -m GetEmployeeData --debug --debug-no-dom
    
    # Debug with explicit DOM capturing
    python -m GetEmployeeData --debug --debug-dom
    
    # Other options
    python -m GetEmployeeData --headless=false --no-images
    python -m GetEmployeeData --setup-credentials
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

from .modules import CompleteScraper, ScraperConfig, AutoLogin, show_credentials_gui
from .modules.orchestrator import Orchestrator


def print_debug_help():
    """Print detailed help for debug mode options."""
    print("""
DEBUG MODE HELP
==================

Debug mode is designed for testing and debugging the scraper with a limited
number of employees and optional DOM capturing for analysis.

DEBUG MODE OPTIONS:
  --debug                 Enable debug mode (limits employees and captures DOM)
  --debug-employees N     Set number of employees to scrape (default: 10)
  --debug-dom            Force DOM capturing on (overrides default)
  --debug-no-dom         Force DOM capturing off (faster execution)
  --debug-help           Show this help message

EXAMPLES:
  # Basic debug mode (10 employees, DOM capture enabled)
  python -m GetEmployeeData --debug
  
  # Debug with only 3 employees
  python -m GetEmployeeData --debug --debug-employees 3
  
  # Debug without DOM capturing (faster)
  python -m GetEmployeeData --debug --debug-no-dom
  
  # Debug with explicit DOM capturing
  python -m GetEmployeeData --debug --debug-dom
  
  # Debug with custom employee count and no DOM capture
  python -m GetEmployeeData --debug --debug-employees 5 --debug-no-dom

DEBUG OUTPUT:
  When debug mode is enabled, additional files are created:
  - debug/dom_captures/     HTML files of each page for DOM analysis
  - debug/screenshots/      PNG screenshots of each page for visual debugging
  - employees_data_debug.json  JSON output with debug metadata

BENEFITS:
  - Faster testing (only scrapes limited employees)
  - DOM analysis for debugging selectors and page structure
  - Visual debugging with screenshots
  - Easy switching between debug and production modes
""")


def setup_logging(config: ScraperConfig):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper()),
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    """Main function to run the employee scraper."""
    parser = argparse.ArgumentParser(description="Scrape employee data from Ennead website")
    parser.add_argument("--headless", type=str, default="true", 
                       help="Run browser in headless mode (true/false)")
    parser.add_argument("--no-images", action="store_true", 
                       help="Skip downloading profile images")
    parser.add_argument("--output", type=str, default="employees_data.json",
                       help="Output JSON filename")
    parser.add_argument("--timeout", type=int, default=15000,
                       help="Page load timeout in milliseconds")
    parser.add_argument("--base-url", type=str, 
                       default="https://ei.ennead.com/employees/1/all-employees",
                       help="Base URL of the employee directory")
    parser.add_argument("--setup-credentials", action="store_true",
                       help="Setup credentials interactively")
    # Debug mode options
    parser.add_argument("--debug", action="store_true",
                       help="Enable DEBUG mode (limits employees and captures DOM)")
    parser.add_argument("--debug-employees", type=int, default=10,
                       help="Number of employees to scrape in debug mode (default: 10)")
    parser.add_argument("--debug-dom", action="store_true",
                       help="Capture DOM and screenshots for debugging")
    parser.add_argument("--debug-no-dom", action="store_true",
                       help="Disable DOM capturing even in debug mode")
    parser.add_argument("--debug-help", action="store_true",
                       help="Show detailed help for debug mode options")
    parser.add_argument("--cleanup-debug", type=int, nargs='?', const=30, metavar='MAX_FILES',
                       help="Clean up debug files keeping max files per folder (default: 30)")
    
    args = parser.parse_args()
    
    # Show debug help if requested
    if args.debug_help:
        print_debug_help()
        sys.exit(0)
    
    # Handle cleanup-only mode
    if args.cleanup_debug is not None:
        config = ScraperConfig.from_env()
        config.setup_directories()
        max_files = args.cleanup_debug
        print(f"🧹 Cleaning up debug files, keeping max {max_files} files per folder...")
        config.cleanup_debug_files(max_files_per_folder=max_files)
        return
    
    # Create configuration
    config = ScraperConfig.from_env()
    config.HEADLESS = args.headless.lower() == "true"
    config.DOWNLOAD_IMAGES = not args.no_images
    config.JSON_FILENAME = args.output
    config.TIMEOUT = args.timeout
    config.BASE_URL = args.base_url
    
    # Configure debug mode settings
    config.DEBUG_MODE = args.debug
    if args.debug:
        # Validate debug employee count
        if args.debug_employees < 1:
            print("Error: --debug-employees must be at least 1")
            sys.exit(1)
        if args.debug_employees > 100:
            print("Warning: --debug-employees is set to a high value. Consider using a smaller number for faster debugging.")
        
        config.DEBUG_MAX_EMPLOYEES = args.debug_employees
        
        # DOM capturing logic
        if args.debug_no_dom:
            config.DEBUG_DOM_CAPTURE = False
        elif args.debug_dom:
            config.DEBUG_DOM_CAPTURE = True
        # If neither --debug-dom nor --debug-no-dom is specified, use default from config
        
        # Validate conflicting options
        if args.debug_dom and args.debug_no_dom:
            print("Error: Cannot specify both --debug-dom and --debug-no-dom")
            sys.exit(1)
    
    # Setup directories and logging
    config.setup_directories()
    setup_logging(config)
    
    # Auto cleanup debug files older than 1 day
    config.auto_cleanup_debug_files()
    
    logger = logging.getLogger(__name__)
    
    # Handle credentials setup
    if args.setup_credentials:
        print("Setting up credentials...")
        if show_credentials_gui():
            print("Credentials saved successfully!")
        else:
            print("Failed to save credentials!")
            return
    
    logger.info("Starting Employee Data Scraper")
    logger.info(f"Configuration: headless={config.HEADLESS}, download_images={config.DOWNLOAD_IMAGES}, debug_mode={config.DEBUG_MODE}")
    logger.info(f"Target URL: {config.BASE_URL}")
    
    if config.DEBUG_MODE:
        logger.info(f"DEBUG MODE ENABLED: Will limit to {config.DEBUG_MAX_EMPLOYEES} employees and capture DOM")
        print(f"\nDEBUG MODE ENABLED")
        print(f"   - Employee limit: {config.DEBUG_MAX_EMPLOYEES}")
        print(f"   - DOM capturing: {'ON' if config.DEBUG_DOM_CAPTURE else 'OFF'}")
        print(f"   - Debug output: {config.get_debug_output_path()}")
        print("="*50)
    
    try:
        # Delegate to orchestrator for stepwise execution and checks
        orchestrator = Orchestrator(config)
        html_path = await orchestrator.run()
        if not html_path:
            print("Scraping failed or produced no output.")
            return
        
        print(f"HTML report: {html_path}")
        
        if config.DEBUG_MODE:
            debug_dir = config.get_debug_output_path()
            print(f"\nDEBUG MODE OUTPUT:")
            print(f"   Debug directory: {debug_dir}")
            print(f"   DOM captures: {debug_dir / 'dom_captures'}")
            print(f"   Screenshots: {debug_dir / 'screenshots'}")
            print(f"   JSON output: {config.get_output_path()}")
            print(f"   (Limited to {config.DEBUG_MAX_EMPLOYEES} employees)")
        
        print("="*50)
    
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print("\nScraping interrupted by user.")
    
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        print(f"\nScraping failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())