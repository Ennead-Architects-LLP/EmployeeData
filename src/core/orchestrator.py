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
            # Step 1: Scrape employees without timeout
            self.logger.info("[STEP 1] Scraping employees...")
            employees = await scraper.scrape_all_employees()
            if not employees:
                self.logger.error("[ERROR] No employees scraped. Aborting.")
                return ""

            # Step 2: Save JSON without timeout
            self.logger.info("[STEP 2] Saving JSON...")
            json_path = await asyncio.to_thread(scraper.save_to_json, employees)
            self.logger.info(f"[SUCCESS] Saved JSON to {json_path}")

            # Step 3: Generate HTML without timeout
            self.logger.info("[STEP 3] Generating HTML...")
            html_path = await asyncio.to_thread(scraper.generate_html_report, json_path)
            self.logger.info(f"[SUCCESS] Generated HTML at {html_path}")

            return html_path
            
        except Exception as e:
            self.logger.error(f"[ERROR] Orchestrator failed: {e}")
            return ""
