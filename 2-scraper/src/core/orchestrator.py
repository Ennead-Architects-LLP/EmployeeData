import logging
import asyncio
from typing import Optional

from ..config.settings import ScraperConfig
from .unified_scraper import UnifiedEmployeeScraper
from ..services.voice_announcer import voice_announcer

class Orchestrator:
    def __init__(self, config: Optional[ScraperConfig] = None, use_parallel: bool = False, max_workers: int = 1):
        self.config = config or ScraperConfig.from_env()
        self.logger = logging.getLogger(__name__)
        # Only sequential processing supported for stability
        self.use_parallel = False
        self.max_workers = 1

    async def run(self) -> str:
        self.logger.info("[START] Starting orchestrator")
        self.config.setup_directories()

        # Start timing for voice announcement
        voice_announcer.start_timing()

        scraper = UnifiedEmployeeScraper(
            mode=UnifiedEmployeeScraper.MODE_COMPLETE,
            config=self.config
        )

        try:
            # Step 1: Scrape employees (sequential only for stability)
            self.logger.info("[STEP 1] Scraping employees with incremental saving...")
            employees = await scraper.scrape_all_employees()
            if not employees:
                self.logger.error("[ERROR] No employees scraped. Aborting.")
                voice_announcer.announce_error("No employees were scraped")
                return ""
            
            # Step 1.5: Verify all research tasks are completed
            self.logger.info("[STEP 1.5] Verifying task completion...")
            verification_results = await scraper.verify_all_tasks_completed(140, employees)  # Expected 140 employees
            if not verification_results['all_tasks_completed']:
                self.logger.warning("[WARNING] Not all research tasks completed successfully")
                voice_announcer.announce_error(f"Only {verification_results['completion_rate']:.1f}% of tasks completed")
                # Continue anyway, but log the issues

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
