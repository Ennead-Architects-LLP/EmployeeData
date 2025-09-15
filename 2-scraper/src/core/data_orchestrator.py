"""
Data-only orchestrator for daily scraping
Focuses only on data collection, no HTML generation
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

from ..config.settings import ScraperConfig
from .unified_scraper import UnifiedEmployeeScraper
from ..services.image_downloader import ImageDownloader

class DataOrchestrator:
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
    
    async def load_existing_employees(self) -> List[Dict[str, Any]]:
        """Load existing employee data"""
        if self.employees_data_file.exists():
            try:
                with open(self.employees_data_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                self.logger.info(f"Loaded {len(existing_data)} existing employee records")
                return existing_data
            except Exception as e:
                self.logger.error(f"Error loading existing data: {e}")
                return []
        else:
            self.logger.info("No existing employee data found, starting fresh")
            return []
    
    def save_employees_data(self, employees: List[Dict[str, Any]]) -> bool:
        """Save employee data to JSON file"""
        try:
            with open(self.employees_data_file, 'w', encoding='utf-8') as f:
                json.dump(employees, f, indent=2, ensure_ascii=False, default=str)
            self.logger.info(f"Saved {len(employees)} employee records to {self.employees_data_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving employee data: {e}")
            return False
    
    def merge_employee_data(self, existing_employees: List[Dict[str, Any]], 
                           new_employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge new employee data with existing data, preserving computer info"""
        self.logger.info("Merging employee data...")
        
        # Create lookup by email
        existing_lookup = {}
        for emp in existing_employees:
            if emp.get('email'):
                existing_lookup[emp['email']] = emp
        
        merged_employees = []
        updated_count = 0
        new_count = 0
        
        for new_emp in new_employees:
            email = new_emp.get('email')
            if email and email in existing_lookup:
                # Update existing employee
                existing_emp = existing_lookup[email]
                
                # Preserve computer info
                if 'computer_info' in existing_emp:
                    new_emp['computer_info'] = existing_emp['computer_info']
                
                # Update other fields
                for key, value in new_emp.items():
                    if key != 'computer_info':
                        existing_emp[key] = value
                
                merged_employees.append(existing_emp)
                updated_count += 1
            else:
                # New employee
                merged_employees.append(new_emp)
                new_count += 1
        
        self.logger.info(f"Updated {updated_count} existing employees, added {new_count} new employees")
        return merged_employees
    
    async def download_profile_images(self, employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Download profile images for employees"""
        self.logger.info("Downloading profile images...")
        
        image_downloader = ImageDownloader(
            output_dir=str(self.images_dir),
            timeout=self.config.TIMEOUT
        )
        
        download_count = 0
        for employee in employees:
            if employee.get('profile_url'):
                try:
                    name = employee.get('human_name', 'unknown').replace(' ', '_')
                    local_path = f"{name}_profile.jpg"
                    
                    success = await image_downloader.download_image(
                        employee['profile_url'],
                        local_path
                    )
                    
                    if success:
                        employee['image_local_path'] = f"assets/images/{local_path}"
                        download_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"Error downloading image for {employee.get('human_name', 'Unknown')}: {e}")
        
        self.logger.info(f"Downloaded {download_count} profile images")
        return employees
    
    async def scrape_employees(self) -> List[Dict[str, Any]]:
        """Scrape employee data from EI website using simple sequential scraper"""
        self.logger.info("Starting sequential employee data scraping...")
        
        try:
            async with UnifiedEmployeeScraper(
                mode=UnifiedEmployeeScraper.MODE_SIMPLE,
                base_url=self.config.BASE_URL,
                download_images=False,  # We'll handle images separately
                headless=self.config.HEADLESS == "true",
                timeout=self.config.TIMEOUT,
                config=self.config
            ) as scraper:
                employees = await scraper.scrape_all_employees()
            
            if not employees:
                self.logger.error("No employees scraped")
                return []
            
            # Convert EmployeeData objects to dictionaries
            employee_dicts = [emp.to_dict() for emp in employees]
            self.logger.info(f"Scraped {len(employee_dicts)} employees")
            return employee_dicts
            
        except Exception as e:
            self.logger.error(f"Error scraping employee data: {e}")
            return []
    
    async def run(self) -> bool:
        """Run the complete data collection process"""
        self.logger.info("Starting data orchestrator")
        
        try:
            # Load existing data
            existing_employees = await self.load_existing_employees()
            
            # Scrape new data
            new_employees = await self.scrape_employees()
            
            if not new_employees:
                self.logger.warning("No new employee data scraped, keeping existing data")
                return True
            
            # Merge data
            merged_employees = self.merge_employee_data(existing_employees, new_employees)
            
            # Download images
            merged_employees = await self.download_profile_images(merged_employees)
            
            # Save data
            if self.save_employees_data(merged_employees):
                self.logger.info("Data collection completed successfully")
                return True
            else:
                self.logger.error("Failed to save employee data")
                return False
                
        except Exception as e:
            self.logger.error(f"Data collection failed: {e}")
            return False
