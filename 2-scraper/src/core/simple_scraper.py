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
            
            # Enhanced browser arguments to bypass anti-bot protection
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps',
                '--disable-popup-blocking',
                '--disable-extensions',
                '--disable-plugins',
                # '--disable-images',  # Keep images enabled for profile photos
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Enhanced context with more realistic browser settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # NYC coordinates
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            self.page = await self.context.new_page()
            
            # Add stealth measures to avoid detection
            await self.page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            self.page.set_default_timeout(self.timeout)
            self.logger.info("[SUCCESS] Browser started successfully with anti-bot protection bypass")
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
            self.logger.info(f"Navigating to: {self.base_url}")
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Check if we were redirected to a login page or unexpected page
            current_url = self.page.url
            page_title = await self.page.title()
            
            self.logger.info(f"Current URL: {current_url}")
            self.logger.info(f"Page title: {page_title}")
            
            # Check if we're on the expected page
            expected_url_indicators = ["employees", "directory", "staff", "people"]
            is_expected_page = any(indicator in current_url.lower() for indicator in expected_url_indicators)
            
            if not is_expected_page:
                self.logger.error(f"[ERROR] Redirected to unexpected page: {current_url}")
                self.logger.error(f"[ERROR] Expected URL should contain: {expected_url_indicators}")
                self.logger.error(f"[ERROR] Page title: {page_title}")
                
                # Check if it's a browser compatibility page
                if "browsers" in current_url.lower():
                    self.logger.error("[ERROR] Website redirected to browser compatibility page")
                    self.logger.error("[ERROR] This may indicate the website requires a specific browser or has anti-bot protection")
                
                raise Exception(f"Website redirected to unexpected page: {current_url}")
            
            login_indicators = [
                "sign in", "login", "authentication", "microsoft", "oauth",
                "password", "username", "account"
            ]
            
            is_login_page = any(indicator in page_title.lower() or indicator in current_url.lower() 
                              for indicator in login_indicators)
            
            if is_login_page:
                self.logger.error(f"[ERROR] Website requires authentication")
                self.logger.error(f"[ERROR] Current URL: {current_url}")
                self.logger.error(f"[ERROR] Page title: {page_title}")
                self.logger.error("[ERROR] Cannot proceed without authentication credentials")
                raise Exception("Website requires authentication - scraper cannot proceed without login credentials")
            
            # Also check for login page content indicators
            page_content = await self.page.content()
            if "microsoft" in page_content.lower() and ("sign in" in page_content.lower() or "login" in page_content.lower()):
                self.logger.error(f"[ERROR] Detected Microsoft login page in content")
                self.logger.error(f"[ERROR] Current URL: {current_url}")
                self.logger.error(f"[ERROR] Page title: {page_title}")
                self.logger.error("[ERROR] Cannot proceed without authentication credentials")
                raise Exception("Website requires authentication - detected Microsoft login page")
            
            # Get all employee links
            employee_links = await self._get_employee_links()
            self.logger.info(f"Found {len(employee_links)} employees to scrape")
            
            if not employee_links:
                self.logger.warning("No employee links found")
                # Try to get more debugging information
                page_content = await self.page.content()
                self.logger.debug(f"Page content length: {len(page_content)}")
                self.logger.debug(f"Page content preview: {page_content[:1000]}...")
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
            # First check if we're on a login page or if authentication is required
            current_url = self.page.url
            page_title = await self.page.title()
            
            # Check for common login page indicators
            login_indicators = [
                "sign in", "login", "authentication", "microsoft", "oauth",
                "password", "username", "account"
            ]
            
            is_login_page = any(indicator in page_title.lower() or indicator in current_url.lower() 
                              for indicator in login_indicators)
            
            if is_login_page:
                self.logger.error(f"[ERROR] Redirected to login page: {current_url}")
                self.logger.error(f"[ERROR] Page title: {page_title}")
                self.logger.error("[ERROR] Authentication required - scraper cannot proceed without credentials")
                raise Exception("Authentication required - website redirected to login page")
            
            # Wait for employee cards to load using selector system with longer timeout
            try:
                await self.page.wait_for_selector(self.selectors['employee_cards'], timeout=15000)
            except Exception as timeout_error:
                # Check if we're still on the right page
                current_url = self.page.url
                page_title = await self.page.title()
                
                if any(indicator in page_title.lower() or indicator in current_url.lower() 
                      for indicator in login_indicators):
                    self.logger.error(f"[ERROR] Page redirected to login during wait: {current_url}")
                    raise Exception("Page redirected to login during scraping")
                
                # If not a login redirect, it's a genuine timeout
                self.logger.error(f"[ERROR] Timeout waiting for employee cards: {timeout_error}")
                raise timeout_error
            
            # Extract employee links using selector system
            employee_links = await self.page.evaluate(f"""
                () => {{
                    const links = [];
                    const cards = document.querySelectorAll('{self.selectors['employee_cards']}');
                    
                    console.log('Found', cards.length, 'employee cards');
                    
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
            
            if not employee_links:
                self.logger.warning("[WARNING] No employee links found - checking page content")
                # Get page content for debugging
                page_content = await self.page.content()
                self.logger.debug(f"Page content preview: {page_content[:500]}...")
                
                # Check for alternative selectors
                alternative_selectors = [
                    '.person-card', '.staff-card', '.team-member', 
                    '[data-person]', '.card', 'li', '.list-item'
                ]
                
                for selector in alternative_selectors:
                    count = await self.page.evaluate(f"document.querySelectorAll('{selector}').length")
                    if count > 0:
                        self.logger.info(f"Found {count} elements with selector: {selector}")
            
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
