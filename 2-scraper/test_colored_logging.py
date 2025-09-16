#!/usr/bin/env python3
"""
Test script to verify colored logging works correctly.
"""

import sys
import os
import logging

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import ScraperConfig

# Import the setup_logging function directly
import main

def test_colored_logging():
    """Test the colored logging functionality."""
    print("Testing colored logging...")
    
    # Create a test configuration
    config = ScraperConfig()
    config.LOG_LEVEL = "DEBUG"
    config.LOG_FILE = "debug/test_colored_logging.log"
    config.LOG_FORMAT = "[%(levelname)s] %(message)s"
    
    # Setup logging with colors
    main.setup_logging(config)
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Test different log levels
    print("\nTesting different log levels:")
    logger.debug("This is a DEBUG message (should be cyan)")
    logger.info("This is an INFO message (should be green)")
    logger.warning("This is a WARNING message (should be yellow)")
    logger.error("This is an ERROR message (should be red)")
    logger.critical("This is a CRITICAL message (should be magenta)")
    
    print("\nColored logging test completed!")
    print("Check the console output above for colors.")
    print(f"Also check the log file: {config.LOG_FILE}")

if __name__ == "__main__":
    test_colored_logging()
