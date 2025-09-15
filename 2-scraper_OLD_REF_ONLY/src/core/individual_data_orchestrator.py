"""
Individual employee data orchestrator
Processes each employee individually and updates their individual JSON file
No big collected JSON file - only individual employee files
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

from ..config.settings import ScraperConfig
from .simple_scraper import SimpleEmployeeScraper
from ..services.image_downloader import ImageDownloader

class IndividualDataOrchestrator:
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig.from_env()
        self.logger = logging.getLogger(__name__)
        
        # Set output paths
        self.output_path = Path("../docs/assets")
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Individual employee files directory
        self.individual_employees_dir = self.output_path / "individual_employees"
        self.individual_employees_dir.mkdir(exist_ok=True)
        
        self.images_dir = self.output_path / "images"
        self.images_dir.mkdir(exist_ok=True)
    
    def get_employee_filename(self, employee_name: str) -> str:
        """Generate filename for individual employee JSON file"""
        # Clean name for filename
        clean_name = employee_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        return f"{clean_name}.json"
    
    def load_individual_employee(self, employee_name: str) -> Optional[Dict[str, Any]]:
        """Load individual employee data from JSON file"""
        filename = self.get_employee_filename(employee_name)
        file_path = self.individual_employees_dir / filename
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading employee {employee_name}: {e}")
                return None
        return None
    
    def save_individual_employee(self, employee_data: Dict[str, Any]) -> bool:
        """Save individual employee data to JSON file"""
        try:
            employee_name = employee_data.get('human_name', 'unknown')
            filename = self.get_employee_filename(employee_name)
            file_path = self.individual_employees_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(employee_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved employee data: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving employee {employee_name}: {e}")
            return False
    
    def merge_employee_data(self, existing_data: Optional[Dict[str, Any]], 
                           new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge new employee data with existing data, preserving computer info"""
        if not existing_data:
            return new_data
        
        # Start with existing data
        merged_data = existing_data.copy()
        
        # Preserve computer info if it exists
        if 'computer_info' in existing_data:
            merged_data['computer_info'] = existing_data['computer_info']
        
        # Update other fields with new data
        for key, value in new_data.items():
            if key != 'computer_info' and value:  # Don't overwrite computer info
                merged_data[key] = value
        
        return merged_data
    
    async def download_employee_image(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Download profile image for individual employee"""
        if not employee_data.get('profile_url'):
            return employee_data
        
        try:
            image_downloader = ImageDownloader(
                output_dir=str(self.images_dir),
                timeout=self.config.TIMEOUT
            )
            
            name = employee_data.get('human_name', 'unknown').replace(' ', '_')
            local_path = f"{name}_profile.jpg"
            
            success = await image_downloader.download_image(
                employee_data['profile_url'],
                local_path
            )
            
            if success:
                employee_data['image_local_path'] = f"assets/images/{local_path}"
                self.logger.info(f"Downloaded image for {employee_data.get('human_name', 'Unknown')}")
            
        except Exception as e:
            self.logger.warning(f"Error downloading image for {employee_data.get('human_name', 'Unknown')}: {e}")
        
        return employee_data
    
    async def process_employee(self, employee_data: Dict[str, Any]) -> bool:
        """Process individual employee: load existing, merge, download image, save"""
        try:
            employee_name = employee_data.get('human_name', 'unknown')
            self.logger.info(f"Processing employee: {employee_name}")
            
            # Load existing data
            existing_data = self.load_individual_employee(employee_name)
            
            # Merge data (preserving computer info)
            merged_data = self.merge_employee_data(existing_data, employee_data)
            
            # Download image
            merged_data = await self.download_employee_image(merged_data)
            
            # Save individual employee file
            if self.save_individual_employee(merged_data):
                self.logger.info(f"[SUCCESS] Successfully processed {employee_name}")
                return True
            else:
                self.logger.error(f"[ERROR] Failed to save {employee_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"[ERROR] Error processing employee {employee_data.get('human_name', 'Unknown')}: {e}")
            return False
    
    async def scrape_employees(self) -> List[Dict[str, Any]]:
        """Scrape employee data from EI website using simple sequential scraper"""
        self.logger.info("Starting sequential employee data scraping...")
        
        try:
            async with SimpleEmployeeScraper(
                base_url=self.config.BASE_URL,
                download_images=False,  # We'll handle images separately
                headless=self.config.HEADLESS == "true",
                timeout=self.config.TIMEOUT
            ) as scraper:
                employees = await scraper.scrape_all_employees()
            
            if not employees:
                self.logger.error("No employees scraped")
                raise Exception("Failed to scrape any employees - this indicates a critical scraping failure")
            
            # Convert EmployeeData objects to dictionaries
            employee_dicts = [emp.to_dict() for emp in employees]
            self.logger.info(f"Scraped {len(employee_dicts)} employees")
            return employee_dicts
            
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Error scraping employee data: {e}")
            
            # Check if this is an authentication error
            if "authentication" in error_message.lower() or "login" in error_message.lower():
                self.logger.error("[CRITICAL] Authentication required - website now requires login")
                self.logger.error("[CRITICAL] The scraper cannot proceed without valid credentials")
                self.logger.error("[CRITICAL] Please check if the website requires authentication")
                raise Exception("Authentication required - website requires login credentials")
            
            # Re-raise the exception to propagate the error up the call stack
            raise
    
    async def run(self) -> bool:
        """Run the complete data collection process for individual employees"""
        self.logger.info("Starting individual employee data orchestrator")
        
        try:
            # Scrape employee data
            employees = await self.scrape_employees()
            
            if not employees:
                self.logger.error("No employees scraped, this indicates a critical failure")
                return False
            
            # Process each employee individually
            processed_count = 0
            failed_count = 0
            
            for employee in employees:
                if await self.process_employee(employee):
                    processed_count += 1
                else:
                    failed_count += 1
            
            self.logger.info(f"Processing completed: {processed_count} successful, {failed_count} failed")
            
            if processed_count > 0:
                self.logger.info("Individual employee data collection completed successfully")
                return True
            else:
                self.logger.error("No employees were successfully processed")
                return False
                
        except Exception as e:
            self.logger.error(f"Individual employee data collection failed: {e}")
            return False
