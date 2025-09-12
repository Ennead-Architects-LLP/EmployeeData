import logging
import asyncio
from typing import Optional

from ..config.settings import ScraperConfig
from .complete_scraper import CompleteScraper
from ..services.voice_announcer import voice_announcer

class Orchestrator:
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig.from_env()
        self.logger = logging.getLogger(__name__)

    async def run(self) -> str:
        self.logger.info("[START] Starting orchestrator")
        self.config.setup_directories()

        # Start timing for voice announcement
        voice_announcer.start_timing()

        scraper = CompleteScraper(self.config)

        try:
            # Step 1: Scrape employees without timeout
            self.logger.info("[STEP 1] Scraping employees...")
            employees = await scraper.scrape_all_employees()
            if not employees:
                self.logger.error("[ERROR] No employees scraped. Aborting.")
                voice_announcer.announce_error("No employees were scraped")
                return ""

            # Step 2: Save JSON without timeout
            self.logger.info("[STEP 2] Saving JSON...")
            json_path = await asyncio.to_thread(scraper.save_to_json, employees)
            self.logger.info(f"[SUCCESS] Saved JSON to {json_path}")

            # Step 3: Generate HTML without timeout
            self.logger.info("[STEP 3] Generating HTML...")
            html_path = await asyncio.to_thread(scraper.generate_html_report, json_path)
            self.logger.info(f"[SUCCESS] Generated HTML at {html_path}")

            # Step 4: Voice announcement - Independent step as requested
            self.logger.info("[STEP 4] Voice announcement...")
            employee_count = len(employees)
            voice_announcer.announce_completion(employee_count)
            self.logger.info(f"[SUCCESS] Voice announcement completed for {employee_count} employees")

            return html_path
            
        except Exception as e:
            self.logger.error(f"[ERROR] Orchestrator failed: {e}")
            voice_announcer.announce_error(f"Pipeline failed: {str(e)}")
            return ""
