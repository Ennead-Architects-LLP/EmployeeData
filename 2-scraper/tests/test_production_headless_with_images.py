#!/usr/bin/env python3
"""
Test scenario: Production Headless with Images

This test runs the scraper in production mode with:
- Full employee scraping (no limits)
- Headless browser mode
- Image downloading enabled
- DOM capturing disabled (for performance)
- Standard production settings

Usage:
    python -m tests.test_production_headless_with_images
    
    # Run with custom parameters
    python -m tests.test_production_headless_with_images --timeout 20000
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


class ProductionHeadlessWithImagesTest:
    """Test class for production scraping with headless browser and images."""
    
    def __init__(self):
        self.test_name = "production_headless_with_images"
        self.start_time = None
        self.end_time = None
        
    def log_test_start(self):
        """Log test start information."""
        self.start_time = time.time()
        logger.info("="*80)
        logger.info(f"🚀 STARTING TEST: {self.test_name}")
        logger.info("="*80)
        logger.info("Configuration:")
        logger.info("  - Mode: Production (full scraping)")
        logger.info("  - Browser: Headless")
        logger.info("  - Images: Download enabled")
        logger.info("  - DOM Capture: Disabled")
        logger.info("  - Employee Limit: None (all employees)")
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
    
    def build_command(self, **kwargs):
        """Build the command to run the scraper."""
        # Base command
        cmd = [
            sys.executable, "-m", "src.main",
            "--headless=true",
            "--timeout=15000",
            "--output=production_headless_output"
        ]
        
        # Override with any provided kwargs
        if kwargs.get('timeout'):
            cmd = [arg for arg in cmd if not arg.startswith('--timeout')]
            cmd.append(f"--timeout={kwargs['timeout']}")
        
        if kwargs.get('base_url'):
            cmd.append(f"--base-url={kwargs['base_url']}")
        
        return cmd
    
    async def run_scraper(self, **kwargs):
        """Run the scraper with the specified parameters."""
        cmd = self.build_command(**kwargs)
        
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
            Path("assets/production_headless_output"),
            Path("debug/scraper.log"),
            Path("assets/images")
        ]
        
        results = {}
        for file_path in expected_files:
            exists = file_path.exists()
            results[file_path] = exists
            if exists:
                if file_path.is_dir():
                    file_count = len(list(file_path.rglob('*')))
                    logger.info(f"✅ {file_path} exists ({file_count} files)")
                    
                    # Special check for images directory
                    if file_path.name == "images":
                        image_files = [f for f in file_path.rglob('*') if f.is_file()]
                        total_size = sum(f.stat().st_size for f in image_files)
                        size_mb = total_size / (1024 * 1024)
                        logger.info(f"   - Total images: {len(image_files)}")
                        logger.info(f"   - Total size: {size_mb:.2f} MB")
                else:
                    size = file_path.stat().st_size
                    logger.info(f"✅ {file_path} exists ({size} bytes)")
            else:
                logger.warning(f"❌ {file_path} does not exist")
        
        return results
    
    async def run_test(self, **kwargs):
        """Run the complete test scenario."""
        self.log_test_start()
        
        try:
            # Run the scraper
            success, stdout, stderr = await self.run_scraper(**kwargs)
            
            if success:
                # Check output files
                output_files = self.check_output_files()
                
                # Log summary
                logger.info("📊 TEST SUMMARY:")
                logger.info(f"  - Scraper execution: {'✅ SUCCESS' if success else '❌ FAILED'}")
                logger.info(f"  - Output files created: {sum(output_files.values())}/{len(output_files)}")
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
    
    parser = argparse.ArgumentParser(description="Test production scraping with headless browser and images")
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
    test = ProductionHeadlessWithImagesTest()
    success = await test.run_test(**kwargs)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
