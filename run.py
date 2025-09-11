import sys
import asyncio
from GetEmployeeData.__main__ import main as scraper_main

if __name__ == "__main__":
    # Pass through CLI args are already handled inside main's argparse
    asyncio.run(scraper_main())
