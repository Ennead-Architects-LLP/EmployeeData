#!/usr/bin/env python3
"""
Test scenario: Quick Debug No Images

This test runs the scraper in debug mode with:
- Very limited employee scraping (3 employees)
- Headless browser for speed
- No image downloading
- DOM capturing disabled for speed
- Minimal timeout for quick testing

Usage:
    python -m tests.test_quick_debug_no_images
    
    # Run with custom employee count
    python -m tests.test_quick_debug_no_images --debug-employees 5
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


class QuickDebugNoImagesTest:
    """Test class for quick debug testing without images."""
    
    def __init__(self):
        self.test_name = "quick_debug_no_images"
        self.start_time = None
        self.end_time = None
        
    def log_test_start(self, debug_employees=3):
        """Log test start information."""
        self.start_time = time.time()
        logger.info("="*80)
        logger.info(f"⚡ STARTING TEST: {self.test_name}")
        logger.info("="*80)
        logger.info("Configuration:")
        logger.info("  - Mode: Quick Debug (minimal setup)")
        logger.info("  - Browser: Headless (fast)")
        logger.info("  - Images: Disabled (fast)")
        logger.info("  - DOM Capture: Disabled (fast)")
        logger.info(f"  - Employee Limit: {debug_employees}")
        logger.info("  - Timeout: 10000ms (fast)")
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
    
    def build_command(self, debug_employees=3, **kwargs):
        """Build the command to run the scraper in quick debug mode."""
        # Base command optimized for speed
        cmd = [
            sys.executable, "-m", "src.main",
            "--debug",
            f"--debug-employees={debug_employees}",
            "--headless=true",
            "--debug-no-dom",
            "--no-images",
            "--timeout=10000",
            "--output=quick_debug_output"
        ]
        
        # Override with any provided kwargs
        if kwargs.get('timeout'):
            cmd = [arg for arg in cmd if not arg.startswith('--timeout')]
            cmd.append(f"--timeout={kwargs['timeout']}")
        
        if kwargs.get('base_url'):
            cmd.append(f"--base-url={kwargs['base_url']}")
        
        return cmd
    
    async def run_scraper(self, debug_employees=3, **kwargs):
        """Run the scraper with the specified parameters."""
        cmd = self.build_command(debug_employees=debug_employees, **kwargs)
        
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
    
    def check_output_files(self):
        """Check if expected output files were created."""
        expected_files = [
            Path("assets/quick_debug_output"),
            Path("debug/scraper.log")
        ]
        
        results = {}
        for file_path in expected_files:
            exists = file_path.exists()
            results[file_path] = exists
            if exists:
                if file_path.is_dir():
                    file_count = len(list(file_path.rglob('*')))
                    logger.info(f"✅ {file_path} exists ({file_count} files)")
                else:
                    size = file_path.stat().st_size
                    logger.info(f"✅ {file_path} exists ({size} bytes)")
            else:
                logger.warning(f"❌ {file_path} does not exist")
        
        return results
    
    async def run_test(self, debug_employees=3, **kwargs):
        """Run the complete test scenario."""
        self.log_test_start(debug_employees)
        
        try:
            # Run the scraper
            success, stdout, stderr = await self.run_scraper(debug_employees=debug_employees, **kwargs)
            
            if success:
                # Check output files
                output_files = self.check_output_files()
                
                # Log summary
                logger.info("📊 TEST SUMMARY:")
                logger.info(f"  - Scraper execution: {'✅ SUCCESS' if success else '❌ FAILED'}")
                logger.info(f"  - Output files created: {sum(output_files.values())}/{len(output_files)}")
                logger.info(f"  - Employee limit: {debug_employees}")
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
    
    parser = argparse.ArgumentParser(description="Test quick debug mode without images")
    parser.add_argument("--debug-employees", type=int, default=3, help="Number of employees to scrape (default: 3)")
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
    test = QuickDebugNoImagesTest()
    success = await test.run_test(debug_employees=args.debug_employees, **kwargs)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
