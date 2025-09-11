#!/usr/bin/env python3
"""
Entry point for the Employee Data Scraper.
This is the main script to run the scraper with the new professional structure.

To use with virtual environment:
    .venv\Scripts\python.exe run.py --debug --debug-employees 1 --debug-no-dom --no-images
"""

import sys
import asyncio
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import main

if __name__ == "__main__":
    asyncio.run(main())