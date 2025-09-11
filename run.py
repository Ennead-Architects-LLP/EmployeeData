import sys
import asyncio
from app import Orchestrator  # thin facade to internal modules
from GetEmployeeData.modules.config import ScraperConfig

if __name__ == "__main__":
    config = ScraperConfig.from_env()
    asyncio.run(Orchestrator(config).run())
