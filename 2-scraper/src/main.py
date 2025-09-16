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
from .core.orchestrator import ScraperOrchestrator
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
  --debug-employees N     Set number of employees to scrape (default: 3)
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


async def run_without_timeout(orchestrator: ScraperOrchestrator, config: ScraperConfig):
    """Run orchestrator without timeout protection."""
    try:
        # Step 1: Setup directories
        config.setup_directories()
        
        # Step 2: Run orchestrator
        success = await orchestrator.run()
        return success
            
    except Exception as e:
        print(f"Operation failed: {e}")
        return None
    finally:
        # Ensure any remaining resources are cleaned up
        try:
            import asyncio
            # Give a moment for any pending operations to complete
            await asyncio.sleep(0.1)
        except:
            pass


async def main():
    """Main function to run the employee scraper."""
    parser = argparse.ArgumentParser(description="Scrape employee data from Ennead website")
    # Minimal, mix-and-match flags per project policy
    parser.add_argument("--headless", action="store_true", help="Run browser headless (no UI)")
    parser.add_argument("--debug", action="store_true", help="Set logging level to DEBUG")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of employees to process")
    parser.add_argument("--dom", action="store_true", help="Capture DOM/screenshots during scraping")
    # Essentials retained
    parser.add_argument("--timeout", type=int, default=15000, help="Page load timeout in milliseconds")
    parser.add_argument("--base-url", type=str, default="https://ei.ennead.com/employees/1/all-employees", help="Base URL of the employee directory")
    # Parallel processing removed - only sequential processing supported for stability
    
    args = parser.parse_args()
    
    # Note: cleanup and debug-help modes removed per simplified CLI policy
    
    # Create configuration
    config = ScraperConfig.from_env()
    config.HEADLESS = args.headless
    # Images always on by default in simplified CLI
    config.DOWNLOAD_IMAGES = True
    config.TIMEOUT = args.timeout
    config.BASE_URL = args.base_url
    
    # Configure simplified runtime flags
    config.DEBUG_MODE = args.debug
    if args.debug:
        # Set logging to DEBUG later via setup_logging
        pass
    config.LIMIT = args.limit
    config.DOM_CAPTURE = args.dom
    
    # Setup directories and logging
    config.setup_directories()
    # Adjust logging level if --debug
    if args.debug:
        config.LOG_LEVEL = "DEBUG"
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
        logger.info("DEBUG logging enabled")
    if config.LIMIT is not None:
        logger.info(f"Limit set to {config.LIMIT} employees")
    if config.DOM_CAPTURE:
        logger.info("DOM capture enabled")
    
    try:
        # Use only sequential processing for stability
        # Delegate to orchestrator without timeout protection
        orchestrator = ScraperOrchestrator(config, use_parallel=False, max_workers=1)
        success = await run_without_timeout(orchestrator, config)
        
        if not success:
            print("❌ Scraping failed or timed out.")
            return
        
        print(f"✅ Scraping completed successfully!")
        
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
    # Suppress asyncio warnings about unclosed transports
    import warnings
    import os
    import sys
    from contextlib import redirect_stderr
    from io import StringIO
    
    # Suppress all ResourceWarnings from asyncio
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", message="unclosed transport")
    warnings.filterwarnings("ignore", message="unclosed file")
    
    # Set environment variable to suppress asyncio warnings
    os.environ['PYTHONWARNINGS'] = 'ignore::ResourceWarning'
    
    # Run the async main function with proper cleanup
    try:
        # Redirect stderr to suppress asyncio warnings
        with redirect_stderr(StringIO()):
            asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Scraper interrupted by user")
    except Exception as e:
        print(f"[ERROR] Scraper failed: {e}")
    finally:
        # Ensure all asyncio tasks are properly cleaned up
        try:
            import asyncio
            # Cancel any remaining tasks
            tasks = [t for t in asyncio.all_tasks() if not t.done()]
            if tasks:
                for task in tasks:
                    task.cancel()
                # Wait for tasks to complete cancellation
                asyncio.gather(*tasks, return_exceptions=True)
            # Give a moment for cleanup
            asyncio.sleep(0.1)
        except:
            pass
