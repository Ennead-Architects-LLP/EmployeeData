#!/usr/bin/env python3
"""
Test scenario: Credentials Setup

This test runs the credentials setup process to ensure:
- Credentials GUI can be launched
- Credentials can be saved properly
- Configuration is accessible

Usage:
    python -m tests.test_credentials_setup
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


class CredentialsSetupTest:
    """Test class for credentials setup functionality."""
    
    def __init__(self):
        self.test_name = "credentials_setup"
        self.start_time = None
        self.end_time = None
        
    def log_test_start(self):
        """Log test start information."""
        self.start_time = time.time()
        logger.info("="*80)
        logger.info(f"🔐 STARTING TEST: {self.test_name}")
        logger.info("="*80)
        logger.info("Configuration:")
        logger.info("  - Mode: Credentials Setup")
        logger.info("  - Function: Test credentials GUI and setup")
        logger.info("  - Purpose: Verify credentials can be configured")
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
    
    def build_command(self):
        """Build the command to run the credentials setup."""
        cmd = [
            sys.executable, "-m", "src.main",
            "--setup-credentials"
        ]
        return cmd
    
    async def run_credentials_setup(self):
        """Run the credentials setup process."""
        cmd = self.build_command()
        
        logger.info(f"Running command: {' '.join(cmd)}")
        logger.info("Note: This will launch a GUI for credentials setup")
        logger.info("The test will wait for the process to complete...")
        
        try:
            # Run the credentials setup
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
                    logger.info(f"[SETUP] {line_str}")
            
            async def read_stderr():
                async for line in process.stderr:
                    line_str = line.decode().strip()
                    stderr_lines.append(line_str)
                    logger.error(f"[SETUP ERROR] {line_str}")
            
            # Read output concurrently
            await asyncio.gather(
                read_stdout(),
                read_stderr(),
                process.wait()
            )
            
            return_code = process.returncode
            
            # Log final status
            if return_code == 0:
                logger.info("Credentials setup completed successfully")
            else:
                logger.error(f"Credentials setup failed with return code: {return_code}")
            
            return return_code == 0, stdout_lines, stderr_lines
            
        except Exception as e:
            logger.error(f"Failed to run credentials setup: {e}")
            return False, [], [str(e)]
    
    def check_credentials_files(self):
        """Check if credentials files were created or modified."""
        # Check for common credentials file locations
        possible_files = [
            Path("src/config/credentials.py"),
            Path("../token.json"),  # Relative to 2-scraper directory
            Path("token.json"),
            Path(".env"),
            Path("credentials.json")
        ]
        
        results = {}
        for file_path in possible_files:
            exists = file_path.exists()
            results[file_path] = exists
            
            if exists:
                if file_path.is_file():
                    size = file_path.stat().st_size
                    mod_time = file_path.stat().st_mtime
                    logger.info(f"✅ {file_path} exists ({size} bytes, modified: {time.ctime(mod_time)})")
                else:
                    logger.info(f"✅ {file_path} exists (directory)")
            else:
                logger.info(f"ℹ️  {file_path} does not exist")
        
        return results
    
    def test_credentials_import(self):
        """Test if credentials can be imported and accessed."""
        try:
            # Try to import credentials module
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            
            from config.credentials import get_credentials, show_credentials_gui
            logger.info("✅ Credentials module imported successfully")
            
            # Try to get credentials (may be empty if not set)
            creds = get_credentials()
            if creds:
                logger.info(f"✅ Credentials retrieved: {list(creds.keys())}")
            else:
                logger.info("ℹ️  No credentials currently set")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Failed to import credentials module: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error accessing credentials: {e}")
            return False
    
    async def run_test(self):
        """Run the complete test scenario."""
        self.log_test_start()
        
        try:
            # Test credentials import first
            import_success = self.test_credentials_import()
            
            # Run credentials setup
            setup_success, stdout, stderr = await self.run_credentials_setup()
            
            # Check credentials files
            credentials_files = self.check_credentials_files()
            
            # Log summary
            logger.info("📊 TEST SUMMARY:")
            logger.info(f"  - Credentials import: {'✅ SUCCESS' if import_success else '❌ FAILED'}")
            logger.info(f"  - Setup execution: {'✅ SUCCESS' if setup_success else '❌ FAILED'}")
            logger.info(f"  - Credentials files found: {sum(credentials_files.values())}/{len(credentials_files)}")
            logger.info(f"  - Total output lines: {len(stdout)}")
            logger.info(f"  - Error lines: {len(stderr)}")
            
            # Test is successful if import works and setup completes
            success = import_success and setup_success
            
            self.log_test_end(success)
            return success
                
        except Exception as e:
            error_msg = f"Test execution failed: {e}"
            self.log_test_end(False, error_msg)
            return False


async def main():
    """Main function to run the test."""
    # Run the test
    test = CredentialsSetupTest()
    success = await test.run_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
