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
        
        # Selectors (comprehensive selector system for better reliability)
        self.selectors = {
            'employee_cards': '.employee-card, .profile-card, [data-employee]',
            'profile_image': 'img.profile-image, .employee-photo img, .avatar img',
            'employee_name': '.employee-name, .profile-name, h3, h4',
            'employee_title': '.employee-title, .profile-title, .position',
            'profile_link': 'a[href*="/employee/"], a[href*="/profile/"]',
            'email_link': 'a[href^="mailto:"]',
            'phone_link': 'a[href^="tel:"]',
            'bio_text': '.bio, .about, .description, .employee-bio',
            'contact_info': '.contact-info, .employee-contact',
            'department': '.department, .team, .division'
        }
    
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
            self.logger.info("[SUCCESS] Browser started successfully")
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to start browser: {e}")
            raise
    
    async def close_browser(self):
        """Close the browser and cleanup"""
        try:
            if self.page:
                try:
                    await self.page.close()
                except Exception as e:
                    self.logger.debug(f"Page already closed: {e}")
            if self.context:
                try:
                    await self.context.close()
                except Exception as e:
                    self.logger.debug(f"Context already closed: {e}")
            if self.browser:
                try:
                    await self.browser.close()
                except Exception as e:
                    self.logger.debug(f"Browser already closed: {e}")
            self.logger.info("[SUCCESS] Browser closed successfully")
        except Exception as e:
            self.logger.error(f"[ERROR] Error closing browser: {e}")
    
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
                        self.logger.info(f"[SUCCESS] Successfully scraped {name}")
                    else:
                        self.logger.warning(f"[WARNING] Failed to scrape {name}")
                    
                    # Small delay between requests to be respectful
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"[ERROR] Error scraping {name}: {e}")
                    continue
            
            # Check if we got any employees - this is a critical failure if we don't
            if len(self.employees) == 0:
                self.logger.error("[CRITICAL] Failed to get any employees - this indicates a complete scraping failure")
                raise Exception("Failed to get any employees - this indicates a complete scraping failure")
            
            self.logger.info(f"[SUCCESS] Scraping completed. Total employees: {len(self.employees)}")
            return self.employees
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error during scraping: {e}")
            # Re-raise the exception to propagate the error up the call stack
            raise
    
    async def _get_employee_links(self) -> List[tuple]:
        """Get all employee profile links from the directory page"""
        try:
            # Wait for employee cards to load using selector system
            await self.page.wait_for_selector(self.selectors['employee_cards'], timeout=10000)
            
            # Extract employee links using selector system
            employee_links = await self.page.evaluate(f"""
                () => {{
                    const links = [];
                    const cards = document.querySelectorAll('{self.selectors['employee_cards']}');
                    
                    cards.forEach(card => {{
                        const nameElement = card.querySelector('{self.selectors['employee_name']}');
                        const linkElement = card.querySelector('{self.selectors['profile_link']}');
                        const imageElement = card.querySelector('{self.selectors['profile_image']}');
                        
                        if (nameElement && linkElement) {{
                            const name = nameElement.textContent.trim();
                            const profileUrl = linkElement.href;
                            const imageUrl = imageElement ? imageElement.src : '';
                            
                            links.push([name, profileUrl, imageUrl]);
                        }}
                    }});
                    
                    return links;
                }}
            """)
            
            return employee_links
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error getting employee links: {e}")
            # Check if this is a timeout error
            if "Timeout" in str(e) or "timeout" in str(e).lower():
                self.logger.error("[ERROR] Timeout waiting for employee cards to load - this indicates a critical scraping failure")
            # Re-raise the exception to propagate the error up the call stack
            raise
    
    async def _scrape_employee_profile(self, profile_url: str, name: str, image_url: str) -> Optional[EmployeeData]:
        """Scrape individual employee profile data"""
        try:
            # Navigate to employee profile
            await self.page.goto(profile_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Extract employee data using selector system
            employee_data = await self.page.evaluate(f"""
                () => {{
                    const data = {{}};
                    
                    // Basic information
                    data.human_name = document.querySelector('{self.selectors['employee_name']}')?.textContent?.trim() || '';
                    data.email = document.querySelector('{self.selectors['email_link']}')?.href?.replace('mailto:', '') || '';
                    data.phone = document.querySelector('{self.selectors['phone_link']}')?.href?.replace('tel:', '') || '';
                    
                    // Position and department
                    data.position = document.querySelector('{self.selectors['employee_title']}')?.textContent?.trim() || '';
                    data.department = document.querySelector('{self.selectors['department']}')?.textContent?.trim() || '';
                    
                    // Bio
                    data.bio = document.querySelector('{self.selectors['bio_text']}')?.textContent?.trim() || '';
                    
                    // Office location
                    data.office_location = document.querySelector('.location, .office, .address')?.textContent?.trim() || '';
                    
                    // Profile image
                    const img = document.querySelector('{self.selectors['profile_image']}');
                    data.image_url = img ? img.src : '';
                    
                    // Additional info
                    data.profile_url = window.location.href;
                    
                    return data;
                }}
            """)
            
            # Normalize office location if present
            office_location = employee_data.get('office_location')
            if office_location:
                office_location = self._normalize_office_location(office_location)
            
            # Create EmployeeData object
            employee = EmployeeData(
                human_name=employee_data.get('human_name') or name,
                email=employee_data.get('email'),
                phone=employee_data.get('phone'),
                position=employee_data.get('position'),
                department=employee_data.get('department'),
                bio=employee_data.get('bio'),
                office_location=office_location,
                profile_url=employee_data.get('profile_url') or profile_url,
                image_url=employee_data.get('image_url') or image_url
            )
            
            return employee
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error scraping profile {profile_url}: {e}")
            return None
    
    def _normalize_office_location(self, location: str) -> str:
        """
        Normalize office location names to standard format.
        
        Args:
            location: Raw location string
            
        Returns:
            Normalized location string
        """
        location = location.strip().lower()
        
        # Map common variations to standard names
        location_mapping = {
            'new york': 'New York',
            'ny': 'New York',
            'nyc': 'New York',
            'new york city': 'New York',
            'shanghai': 'Shanghai',
            'california': 'California',
            'ca': 'California',
            'los angeles': 'California',
            'san francisco': 'California',
            'sf': 'California'
        }
        
        # Check for exact matches first
        if location in location_mapping:
            return location_mapping[location]
        
        # Check for partial matches
        for key, value in location_mapping.items():
            if key in location:
                return value
        
        # Return original if no mapping found
        return location.title()
