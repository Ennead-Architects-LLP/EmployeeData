import logging
import asyncio
from typing import Optional

from ..config.settings import ScraperConfig
from .unified_scraper import UnifiedEmployeeScraper

class ScraperOrchestrator:
    def __init__(self, config: Optional[ScraperConfig] = None, use_parallel: bool = False, max_workers: int = 1):
        self.config = config or ScraperConfig.from_env()
        self.logger = logging.getLogger(__name__)
        # Only sequential processing supported for stability
        self.use_parallel = False
        self.max_workers = 1

    async def run(self) -> bool:
        """Run the scraper to collect employee data and save JSON files"""
        self.logger.info("[START] Starting scraper orchestrator")
        self.config.setup_directories()

        try:
            # Step 1: Scrape employees
            self.logger.info("[STEP 1] Scraping employees...")
            async with UnifiedEmployeeScraper(
                base_url=self.config.BASE_URL,
                download_images=self.config.DOWNLOAD_IMAGES,
                headless=self.config.HEADLESS,
                timeout=self.config.TIMEOUT,
                config=self.config
            ) as scraper:
                employees = await scraper.scrape_all_employees()
            
            if not employees:
                self.logger.error("[ERROR] No employees scraped. Aborting.")
                return False
            
            # Step 2: Save individual JSON files
            self.logger.info("[STEP 2] Saving individual JSON files...")
            saved_count = await self._save_individual_employees(employees)
            self.logger.info(f"[SUCCESS] Saved {saved_count} employee JSON files")

            # Step 3: Save combined JSON file
            self.logger.info("[STEP 3] Saving combined JSON file...")
            combined_path = await self._save_combined_employees(employees)
            self.logger.info(f"[SUCCESS] Saved combined JSON to {combined_path}")

            self.logger.info(f"[SUCCESS] Scraper completed successfully - {len(employees)} employees processed")
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Scraper failed: {e}")
            return False
    
    async def _save_individual_employees(self, employees) -> int:
        """Save each employee as individual JSON file"""
        # Set output paths - always use docs folder relative to project root
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        output_path = project_root / "docs" / "assets"
        individual_employees_dir = output_path / "individual_employees"
        individual_employees_dir.mkdir(parents=True, exist_ok=True)
        
        saved_count = 0
        for employee in employees:
            try:
                employee_name = employee.human_name or "unknown"
                clean_name = employee_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                filename = f"{clean_name}.json"
                file_path = individual_employees_dir / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(employee.to_dict(), f, indent=2, ensure_ascii=False, default=str)
                
                saved_count += 1
                self.logger.debug(f"Saved individual file: {filename}")
                
            except Exception as e:
                self.logger.error(f"Error saving individual file for {employee_name}: {e}")
        
        return saved_count
    
    async def _save_combined_employees(self, employees) -> str:
        """Save all employees as combined JSON file"""
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        output_path = project_root / "docs" / "assets"
        output_path.mkdir(parents=True, exist_ok=True)
        
        combined_path = output_path / "employee_files_list.json"
        
        # Convert to list of dictionaries
        employees_data = [emp.to_dict() for emp in employees]
        
        with open(combined_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(employees_data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(combined_path)
