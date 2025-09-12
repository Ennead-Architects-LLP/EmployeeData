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
    python -m src.main
    
    # Basic debug mode (10 employees + DOM capture)
    python -m src.main --debug
    
    # Debug with custom employee limit
    python -m src.main --debug --debug-employees 5
    
    # Debug without DOM capturing (faster)
    python -m src.main --debug --debug-no-dom
    
    # Debug with explicit DOM capturing
    python -m src.main --debug --debug-dom
    
    # Other options
    python -m src.main --headless=false --no-images
    python -m src.main --setup-credentials
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
import signal
from contextlib import asynccontextmanager

from .config.settings import ScraperConfig
from .core.orchestrator import Orchestrator
from .config.credentials import show_credentials_gui


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
  python -m src.main --debug
  
  # Debug with only 3 employees
  python -m src.main --debug --debug-employees 3
  
  # Debug without DOM capturing (faster)
  python -m src.main --debug --debug-no-dom
  
  # Debug with explicit DOM capturing
  python -m src.main --debug --debug-dom
  
  # Debug with custom employee count and no DOM capture
  python -m src.main --debug --debug-employees 5 --debug-no-dom

DEBUG OUTPUT:
  When debug mode is enabled, additional files are created:
  - output/debug/dom_captures/     HTML files of each page for DOM analysis
  - output/debug/screenshots/      PNG screenshots of each page for visual debugging
  - output/data/employees_data_debug.json  JSON output with debug metadata

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


class TimeoutManager:
    """Manages timeouts with automatic reset for long-running operations."""
    
    def __init__(self, default_timeout: float = 10.0):
        self.default_timeout = default_timeout
        self.active_timers = set()
        self.logger = logging.getLogger(__name__)
    
    @asynccontextmanager
    async def timeout_protection(self, operation_name: str, timeout: float = None):
        """Context manager for timeout protection with automatic reset."""
        timeout = timeout or self.default_timeout
        self.logger.info(f"[START] {operation_name} (timeout: {timeout}s)")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Create a timeout task
            timeout_task = asyncio.create_task(asyncio.sleep(timeout))
            self.active_timers.add(timeout_task)
            
            yield timeout_task
            
            # Cancel timeout if operation completes
            if not timeout_task.done():
                timeout_task.cancel()
                self.active_timers.discard(timeout_task)
                
            elapsed = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"[SUCCESS] {operation_name} completed in {elapsed:.2f}s")
            
        except asyncio.TimeoutError:
            self.logger.error(f"[TIMEOUT] {operation_name} timed out after {timeout}s")
            raise
        except Exception as e:
            self.logger.error(f"[ERROR] {operation_name} failed: {e}")
            raise
        finally:
            # Clean up timeout task
            if timeout_task in self.active_timers:
                timeout_task.cancel()
                self.active_timers.discard(timeout_task)
    
    async def reset_timer(self, operation_name: str):
        """Reset timer for long-running operations."""
        self.logger.info(f"🔄 Timer reset for {operation_name}")
    
    async def cancel_all_timers(self):
        """Cancel all active timers."""
        for timer in list(self.active_timers):
            timer.cancel()
            self.active_timers.discard(timer)
        self.logger.info("[STOP] All timers cancelled")


async def run_without_timeout(orchestrator: Orchestrator, config: ScraperConfig):
    """Run orchestrator without timeout protection."""
    try:
        # Step 1: Setup directories
        config.setup_directories()
        
        # Step 2: Run orchestrator
        html_path = await orchestrator.run()
        return html_path
            
    except Exception as e:
        print(f"Operation failed: {e}")
        return None


async def main():
    """Main function to run the employee scraper."""
    parser = argparse.ArgumentParser(description="Scrape employee data from Ennead website (Sequential processing by default)")
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
    parser.add_argument("--parallel", action="store_true",
                       help="Use parallel processing with multiple browser contexts (faster but uses more resources)")
    parser.add_argument("--sequential", action="store_true", default=True,
                       help="Use sequential processing (DEFAULT) - more reliable but slower")
    parser.add_argument("--max-workers", type=int, default=3,
                       help="Maximum number of parallel workers (default: 3)")
    
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
        # Determine processing mode: sequential is default unless --parallel is specified
        use_parallel = args.parallel
        
        # Delegate to orchestrator without timeout protection
        orchestrator = Orchestrator(config, use_parallel=use_parallel, max_workers=args.max_workers)
        html_path = await run_without_timeout(orchestrator, config)
        
        if not html_path:
            print("❌ Scraping failed or timed out.")
            return
        
        print(f"✅ HTML report generated: {html_path}")
        
        if config.DEBUG_MODE:
            debug_dir = config.get_debug_output_path()
            print(f"\n🔍 DEBUG MODE OUTPUT:")
            print(f"   Debug directory: {debug_dir}")
            print(f"   DOM captures: {debug_dir / 'dom_captures'}")
            print(f"   Screenshots: {debug_dir / 'screenshots'}")
            print(f"   JSON output: {config.get_output_path()}")
            # Helpful pointers
            print(f"   Log file: {config.LOG_FILE}")
            print(f"   Selector report: {debug_dir / 'seating_chart' / 'selector_report.json'}")
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
