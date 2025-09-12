"""
Simple sequential employee scraper - no parallel processing, no chunking, no batch files
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from urllib.parse import urljoin, urlparse
import json
from pathlib import Path

from .models import EmployeeData
from ..services.image_downloader import ImageDownloader


class SimpleEmployeeScraper:
    """
    Simple sequential scraper for extracting employee data from Ennead website.
    No parallel processing, no chunking, no batch files.
    """
    
    def __init__(self, 
                 base_url: str = "https://ei.ennead.com/employees/1/all-employees",
                 download_images: bool = True,
                 headless: bool = True,
                 timeout: int = 30000):
        """
        Initialize the employee scraper.
        
        Args:
            base_url: Base URL of the employee directory page
            download_images: Whether to download profile images
            headless: Whether to run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.base_url = base_url
        self.download_images = download_images
        self.headless = headless
        self.timeout = timeout
        
        # Initialize components
        self.image_downloader = ImageDownloader() if download_images else None
        self.logger = logging.getLogger(__name__)
        
        # Browser components
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Scraped data
        self.employees: List[EmployeeData] = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_browser()
    
    async def start_browser(self):
        """Start the browser and create context"""
        try:
            self.logger.info("Starting browser...")
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            self.logger.info("✅ Browser started successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to start browser: {e}")
            raise
    
    async def close_browser(self):
        """Close the browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            self.logger.info("✅ Browser closed successfully")
        except Exception as e:
            self.logger.error(f"❌ Error closing browser: {e}")
    
    async def scrape_all_employees(self) -> List[EmployeeData]:
        """
        Scrape all employees from the directory sequentially.
        No parallel processing, no chunking, no batch files.
        """
        self.logger.info("Starting sequential employee scraping...")
        
        try:
            # Navigate to employee directory
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Get all employee links
            employee_links = await self._get_employee_links()
            self.logger.info(f"Found {len(employee_links)} employees to scrape")
            
            if not employee_links:
                self.logger.warning("No employee links found")
                return []
            
            # Scrape each employee sequentially
            self.employees = []
            for i, (name, profile_url, image_url) in enumerate(employee_links, 1):
                try:
                    self.logger.info(f"Scraping employee {i}/{len(employee_links)}: {name}")
                    
                    # Scrape employee data
                    employee = await self._scrape_employee_profile(profile_url, name, image_url)
                    
                    if employee:
                        self.employees.append(employee)
                        self.logger.info(f"✅ Successfully scraped {name}")
                    else:
                        self.logger.warning(f"⚠️  Failed to scrape {name}")
                    
                    # Small delay between requests to be respectful
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error scraping {name}: {e}")
                    continue
            
            self.logger.info(f"✅ Scraping completed. Total employees: {len(self.employees)}")
            return self.employees
            
        except Exception as e:
            self.logger.error(f"❌ Error during scraping: {e}")
            return []
    
    async def _get_employee_links(self) -> List[tuple]:
        """Get all employee profile links from the directory page"""
        try:
            # Wait for employee cards to load
            await self.page.wait_for_selector('.employee-card, .person-card, [data-employee]', timeout=10000)
            
            # Extract employee links
            employee_links = await self.page.evaluate("""
                () => {
                    const links = [];
                    const cards = document.querySelectorAll('.employee-card, .person-card, [data-employee]');
                    
                    cards.forEach(card => {
                        const nameElement = card.querySelector('h3, .name, .employee-name');
                        const linkElement = card.querySelector('a[href*="/employees/"]');
                        const imageElement = card.querySelector('img');
                        
                        if (nameElement && linkElement) {
                            const name = nameElement.textContent.trim();
                            const profileUrl = linkElement.href;
                            const imageUrl = imageElement ? imageElement.src : '';
                            
                            links.push([name, profileUrl, imageUrl]);
                        }
                    });
                    
                    return links;
                }
            """)
            
            return employee_links
            
        except Exception as e:
            self.logger.error(f"❌ Error getting employee links: {e}")
            return []
    
    async def _scrape_employee_profile(self, profile_url: str, name: str, image_url: str) -> Optional[EmployeeData]:
        """Scrape individual employee profile data"""
        try:
            # Navigate to employee profile
            await self.page.goto(profile_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Extract employee data
            employee_data = await self.page.evaluate("""
                () => {
                    const data = {};
                    
                    // Basic information
                    data.real_name = document.querySelector('h1, .employee-name, .profile-name')?.textContent?.trim() || '';
                    data.email = document.querySelector('a[href^="mailto:"]')?.href?.replace('mailto:', '') || '';
                    data.phone = document.querySelector('a[href^="tel:"]')?.href?.replace('tel:', '') || '';
                    
                    // Position and department
                    data.position = document.querySelector('.position, .job-title, .title')?.textContent?.trim() || '';
                    data.department = document.querySelector('.department, .dept')?.textContent?.trim() || '';
                    
                    // Bio
                    data.bio = document.querySelector('.bio, .about, .description')?.textContent?.trim() || '';
                    
                    // Office location
                    data.office_location = document.querySelector('.location, .office, .address')?.textContent?.trim() || '';
                    
                    // Profile image
                    const img = document.querySelector('.profile-image img, .employee-photo img, .avatar img');
                    data.image_url = img ? img.src : '';
                    
                    // Additional info
                    data.profile_url = window.location.href;
                    
                    return data;
                }
            """)
            
            # Create EmployeeData object
            employee = EmployeeData(
                real_name=employee_data.get('real_name') or name,
                email=employee_data.get('email'),
                phone=employee_data.get('phone'),
                position=employee_data.get('position'),
                department=employee_data.get('department'),
                bio=employee_data.get('bio'),
                office_location=employee_data.get('office_location'),
                profile_url=employee_data.get('profile_url') or profile_url,
                image_url=employee_data.get('image_url') or image_url
            )
            
            return employee
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping profile {profile_url}: {e}")
            return None
