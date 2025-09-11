import logging
import asyncio
from typing import Optional

from ..config.settings import ScraperConfig
from .complete_scraper import CompleteScraper

class Orchestrator:
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig.from_env()
        self.logger = logging.getLogger(__name__)

    async def run(self) -> str:
        self.logger.info("[START] Starting orchestrator")
        self.config.setup_directories()

        scraper = CompleteScraper(self.config)

        try:
            # Step 1: Scrape employees with timeout
            self.logger.info("[STEP 1] Scraping employees...")
            employees = await asyncio.wait_for(
                scraper.scrape_all_employees(), 
                timeout=1800.0
            )
            if not employees:
                self.logger.error("[ERROR] No employees scraped. Aborting.")
                return ""

            # Step 2: Save JSON with timeout
            self.logger.info("[STEP 2] Saving JSON...")
            json_path = await asyncio.wait_for(
                asyncio.to_thread(scraper.save_to_json, employees),
                timeout=5.0
            )
            self.logger.info(f"[SUCCESS] Saved JSON to {json_path}")

            # Step 3: Generate HTML with timeout
            self.logger.info("[STEP 3] Generating HTML...")
            html_path = await asyncio.wait_for(
                asyncio.to_thread(scraper.generate_html_report, json_path),
                timeout=10.0
            )
            self.logger.info(f"[SUCCESS] Generated HTML at {html_path}")

            return html_path
            
        except asyncio.TimeoutError:
            self.logger.error("[TIMEOUT] Orchestrator operation timed out")
            return ""
        except Exception as e:
            self.logger.error(f"[ERROR] Orchestrator failed: {e}")
            return ""
