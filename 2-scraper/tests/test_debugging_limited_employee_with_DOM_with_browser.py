#!/usr/bin/env python3
"""
Test scenario: Debugging Limited Employee with DOM and Browser

This test runs the scraper in debug mode with:
- Limited employee scraping (configurable, default 10)
- Browser with GUI visible (headless=false)
- DOM capturing enabled for debugging
- Screenshot capturing enabled
- Image downloading enabled
- Enhanced logging for debugging

Usage:
    python -m tests.test_debugging_limited_employee_with_DOM_with_browser
    
    # Run with custom parameters
    python -m tests.test_debugging_limited_employee_with_DOM_with_browser --debug-employees 5
    python -m tests.test_debugging_limited_employee_with_DOM_with_browser --no-images
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
import logging

# Setup logging for this test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DebuggingLimitedEmployeeTest:
    """Test class for debugging with limited employees, DOM capture, and visible browser."""
    
    def __init__(self):
        self.test_name = "debugging_limited_employee_with_DOM_with_browser"
        self.start_time = None
        self.end_time = None
        
    def log_test_start(self, debug_employees=10, headless=False, dom_capture=True):
        """Log test start information."""
        self.start_time = time.time()
        logger.info("="*80)
        logger.info(f"🔍 STARTING TEST: {self.test_name}")
        logger.info("="*80)
        logger.info("Configuration:")
        logger.info("  - Mode: Debug (limited employees)")
        logger.info(f"  - Browser: {'Headless' if headless else 'Visible GUI'}")
        logger.info("  - Images: Download enabled")
        logger.info(f"  - DOM Capture: {'Enabled' if dom_capture else 'Disabled'}")
        logger.info(f"  - Employee Limit: {debug_employees}")
        logger.info("  - Screenshots: Enabled (debug mode)")
        logger.info("  - Timeout: 15000ms")
        logger.info("="*80)
    
    def log_test_end(self, success: bool, error_msg: str = None):
        """Log test end information."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time if self.start_time else 0
        
        logger.info("="*80)
        if success:
            logger.info(f"✅ TEST COMPLETED: {self.test_name}")
            logger.info("Result: SUCCESS")
        else:
            logger.info(f"❌ TEST FAILED: {self.test_name}")
            logger.info("Result: FAILED")
            if error_msg:
                logger.error(f"Error: {error_msg}")
        
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info("="*80)
    
    def build_command(self, debug_employees=10, headless=False, no_images=False, dom_capture=True, **kwargs):
        """Build the command to run the scraper in debug mode."""
        # Base command with debug mode
        cmd = [
            sys.executable, "-m", "src.main",
            "--debug",
            f"--debug-employees={debug_employees}",
            f"--headless={'true' if headless else 'false'}",
            "--timeout=15000",
            "--output=debug_test_output"
        ]
        
        # DOM capture options
        if dom_capture:
            cmd.append("--debug-dom")
        else:
            cmd.append("--debug-no-dom")
        
        # Image options
        if no_images:
            cmd.append("--no-images")
        
        # Override with any provided kwargs
        if kwargs.get('timeout'):
            cmd = [arg for arg in cmd if not arg.startswith('--timeout')]
            cmd.append(f"--timeout={kwargs['timeout']}")
        
        if kwargs.get('base_url'):
            cmd.append(f"--base-url={kwargs['base_url']}")
        
        return cmd
    
    async def run_scraper(self, debug_employees=10, headless=False, no_images=False, dom_capture=True, **kwargs):
        """Run the scraper with the specified parameters."""
        cmd = self.build_command(
            debug_employees=debug_employees,
            headless=headless,
            no_images=no_images,
            dom_capture=dom_capture,
            **kwargs
        )
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            # Run the scraper
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(__file__).parent.parent  # Run from 2-scraper directory
            )
            
            # Capture output in real-time
            stdout_lines = []
            stderr_lines = []
            
            async def read_stdout():
                async for line in process.stdout:
                    line_str = line.decode().strip()
                    stdout_lines.append(line_str)
                    logger.info(f"[SCRAPER] {line_str}")
            
            async def read_stderr():
                async for line in process.stderr:
                    line_str = line.decode().strip()
                    stderr_lines.append(line_str)
                    logger.error(f"[SCRAPER ERROR] {line_str}")
            
            # Read output concurrently
            await asyncio.gather(
                read_stdout(),
                read_stderr(),
                process.wait()
            )
            
            return_code = process.returncode
            
            # Log final status
            if return_code == 0:
                logger.info("Scraper completed successfully")
            else:
                logger.error(f"Scraper failed with return code: {return_code}")
            
            return return_code == 0, stdout_lines, stderr_lines
            
        except Exception as e:
            logger.error(f"Failed to run scraper: {e}")
            return False, [], [str(e)]
    
    def check_debug_output_files(self, debug_employees):
        """Check if expected debug output files were created."""
        debug_dir = Path("debug")
        expected_files = {
            "log_file": debug_dir / "scraper.log",
            "dom_captures": debug_dir / "dom_captures",
            "screenshots": debug_dir / "screenshots",
            "seating_chart": debug_dir / "seating_chart",
            "json_output": Path("assets/debug_test_output"),
            "images": Path("assets/images")
        }
        
        results = {}
        for name, file_path in expected_files.items():
            exists = file_path.exists()
            results[name] = exists
            
            if exists:
                if file_path.is_dir():
                    file_count = len(list(file_path.rglob('*')))
                    logger.info(f"✅ {name}: {file_path} exists ({file_count} files)")
                    
                    # Special checks for debug directories
                    if name == "dom_captures" and dom_capture:
                        html_files = list(file_path.glob("*.html"))
                        logger.info(f"   - HTML files: {len(html_files)}")
                    
                    if name == "screenshots":
                        png_files = list(file_path.glob("*.png"))
                        logger.info(f"   - PNG files: {len(png_files)}")
                    
                    if name == "images":
                        image_files = list(file_path.rglob("*"))
                        logger.info(f"   - Image files: {len(image_files)}")
                else:
                    size = file_path.stat().st_size
                    logger.info(f"✅ {name}: {file_path} exists ({size} bytes)")
            else:
                logger.warning(f"❌ {name}: {file_path} does not exist")
        
        return results
    
    def analyze_debug_output(self, debug_employees):
        """Analyze the debug output for quality and completeness."""
        logger.info("🔍 ANALYZING DEBUG OUTPUT:")
        
        # Check JSON output structure
        json_dir = Path("assets/debug_test_output")
        if json_dir.exists():
            json_files = list(json_dir.glob("*.json"))
            logger.info(f"  - JSON files created: {len(json_files)}")
            
            if json_files:
                # Read first JSON file to check structure
                try:
                    import json
                    with open(json_files[0], 'r') as f:
                        data = json.load(f)
                    
                    logger.info(f"  - Sample employee data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                except Exception as e:
                    logger.warning(f"  - Could not analyze JSON structure: {e}")
        
        # Check DOM captures
        dom_dir = Path("debug/dom_captures")
        if dom_dir.exists():
            html_files = list(dom_dir.glob("*.html"))
            logger.info(f"  - DOM capture files: {len(html_files)}")
            
            if html_files:
                # Check file sizes
                total_size = sum(f.stat().st_size for f in html_files)
                avg_size = total_size / len(html_files)
                logger.info(f"  - Average DOM file size: {avg_size:.0f} bytes")
        
        # Check screenshots
        screenshots_dir = Path("debug/screenshots")
        if screenshots_dir.exists():
            png_files = list(screenshots_dir.glob("*.png"))
            logger.info(f"  - Screenshot files: {len(png_files)}")
            
            if png_files:
                # Check file sizes
                total_size = sum(f.stat().st_size for f in png_files)
                avg_size = total_size / len(png_files)
                logger.info(f"  - Average screenshot size: {avg_size:.0f} bytes")
    
    async def run_test(self, debug_employees=10, headless=False, no_images=False, dom_capture=True, **kwargs):
        """Run the complete test scenario."""
        self.log_test_start(debug_employees, headless, dom_capture)
        
        try:
            # Run the scraper
            success, stdout, stderr = await self.run_scraper(
                debug_employees=debug_employees,
                headless=headless,
                no_images=no_images,
                dom_capture=dom_capture,
                **kwargs
            )
            
            if success:
                # Check output files
                output_files = self.check_debug_output_files(debug_employees)
                
                # Analyze debug output
                self.analyze_debug_output(debug_employees)
                
                # Log summary
                logger.info("📊 TEST SUMMARY:")
                logger.info(f"  - Scraper execution: {'✅ SUCCESS' if success else '❌ FAILED'}")
                logger.info(f"  - Debug files created: {sum(output_files.values())}/{len(output_files)}")
                logger.info(f"  - Employee limit: {debug_employees}")
                logger.info(f"  - DOM capture: {'✅ Enabled' if dom_capture else '❌ Disabled'}")
                logger.info(f"  - Browser mode: {'Headless' if headless else 'Visible'}")
                logger.info(f"  - Total output lines: {len(stdout)}")
                logger.info(f"  - Error lines: {len(stderr)}")
                
                self.log_test_end(True)
                return True
            else:
                error_msg = "\n".join(stderr[-5:]) if stderr else "Unknown error"
                self.log_test_end(False, error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Test execution failed: {e}"
            self.log_test_end(False, error_msg)
            return False


async def main():
    """Main function to run the test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test debugging with limited employees, DOM capture, and visible browser")
    parser.add_argument("--debug-employees", type=int, default=10, help="Number of employees to scrape (default: 10)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--no-images", action="store_true", help="Skip downloading images")
    parser.add_argument("--no-dom", action="store_true", help="Disable DOM capturing")
    parser.add_argument("--timeout", type=int, help="Custom timeout in milliseconds")
    parser.add_argument("--base-url", type=str, help="Custom base URL")
    
    args = parser.parse_args()
    
    # Convert args to kwargs
    kwargs = {}
    if args.timeout:
        kwargs['timeout'] = args.timeout
    if args.base_url:
        kwargs['base_url'] = args.base_url
    
    # Run the test
    test = DebuggingLimitedEmployeeTest()
    success = await test.run_test(
        debug_employees=args.debug_employees,
        headless=args.headless,
        no_images=args.no_images,
        dom_capture=not args.no_dom,
        **kwargs
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
