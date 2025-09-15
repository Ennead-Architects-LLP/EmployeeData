"""
Unified Employee Scraper
Combines SimpleEmployeeScraper and CompleteScraper into one flexible scraper
that can run in different modes for different use cases.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from urllib.parse import urljoin, urlparse
import json
from pathlib import Path

from .models import EmployeeData
from ..services.auth import AutoLogin
from ..services.image_downloader import ImageDownloader
from ..config.settings import ScraperConfig


class UnifiedEmployeeScraper:
    """
    Unified scraper that can operate in different modes:
    - SIMPLE: Fast, reliable, basic data only (for GitHub Actions)
    - COMPLETE: Comprehensive data extraction (for development/analysis)
    """
    
    # Scraper modes
    MODE_SIMPLE = "simple"
    MODE_COMPLETE = "complete"
    
    def __init__(self, 
                 mode: str = MODE_SIMPLE,
                 base_url: str = "https://ei.ennead.com/employees/1/all-employees",
                 download_images: bool = True,
                 headless: bool = True,
                 timeout: int = 30000,
                 config: Optional[ScraperConfig] = None):
        """
        Initialize the unified scraper.
        
        Args:
            mode: Scraper mode - 'simple' or 'complete'
            base_url: Base URL of the employee directory page
            download_images: Whether to download profile images
            headless: Whether to run browser in headless mode
            timeout: Page load timeout in milliseconds
            config: Scraper configuration object
        """
        self.mode = mode
        self.base_url = base_url
        self.download_images = download_images
        self.headless = headless
        self.timeout = timeout
        self.config = config or ScraperConfig.from_env()
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.image_downloader = ImageDownloader() if download_images else None
        self.auto_login = AutoLogin()
        
        # Browser components
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Scraped data
        self.employees: List[EmployeeData] = []
        
        # Selectors for different modes
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
        
        self.logger.info(f"Unified scraper initialized in '{mode}' mode")
    
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
            
            # Browser arguments based on mode
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
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            # In simple mode, disable images for faster loading
            if self.mode == self.MODE_SIMPLE:
                browser_args.append('--disable-images')
            
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Enhanced context with realistic browser settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
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
            
            # Add stealth measures
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            self.page.set_default_timeout(self.timeout)
            self.logger.info(f"[SUCCESS] Browser started in '{self.mode}' mode")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to start browser: {e}")
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
            self.logger.info("[SUCCESS] Browser closed successfully")
        except Exception as e:
            self.logger.error(f"[ERROR] Error closing browser: {e}")
    
    async def scrape_all_employees(self) -> List[EmployeeData]:
        """
        Scrape all employees from the directory.
        Behavior depends on the mode:
        - SIMPLE: Fast, basic data only
        - COMPLETE: Comprehensive data extraction
        """
        self.logger.info(f"Starting employee scraping in '{self.mode}' mode...")
        
        try:
            # Navigate to employee directory
            self.logger.info(f"Navigating to: {self.base_url}")
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Handle authentication if needed
            await self._handle_authentication()
            
            # Get all employee links
            employee_links = await self._get_employee_links()
            self.logger.info(f"Found {len(employee_links)} employees to scrape")
            
            if not employee_links:
                self.logger.warning("No employee links found")
                return []
            
            # Scrape each employee
            self.employees = []
            for i, (name, profile_url, image_url) in enumerate(employee_links, 1):
                try:
                    self.logger.info(f"Scraping employee {i}/{len(employee_links)}: {name}")
                    
                    # Scrape employee data based on mode
                    if self.mode == self.MODE_SIMPLE:
                        employee = await self._scrape_employee_simple(profile_url, name, image_url)
                    else:  # COMPLETE mode
                        employee = await self._scrape_employee_complete(profile_url, name, image_url)
                    
                    if employee:
                        self.employees.append(employee)
                        self.logger.info(f"[SUCCESS] Successfully scraped {name}")
                    else:
                        self.logger.warning(f"[WARNING] Failed to scrape {name}")
                    
                    # Delay between requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"[ERROR] Error scraping {name}: {e}")
                    continue
            
            # Validate results
            if len(self.employees) == 0:
                self.logger.error("[CRITICAL] Failed to get any employees")
                raise Exception("Failed to get any employees - this indicates a complete scraping failure")
            
            self.logger.info(f"[SUCCESS] Scraping completed. Total employees: {len(self.employees)}")
            return self.employees
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error during scraping: {e}")
            raise
    
    async def _handle_authentication(self):
        """Handle authentication if required"""
        current_url = self.page.url
        page_title = await self.page.title()
        
        # Check for login page indicators
        login_indicators = [
            "sign in", "login", "authentication", "microsoft", "oauth",
            "password", "username", "account"
        ]
        
        is_login_page = any(indicator in page_title.lower() or indicator in current_url.lower() 
                          for indicator in login_indicators)
        
        if is_login_page:
            self.logger.info(f"[INFO] Website requires authentication - attempting auto-login")
            
            if self.auto_login.load_credentials():
                self.logger.info("[INFO] Credentials loaded, attempting automatic login...")
                login_success = await self.auto_login.login(self.page, self.base_url)
                if login_success:
                    self.logger.info("[SUCCESS] Automatic login successful")
                    await self.page.goto(self.base_url)
                    await self.page.wait_for_load_state('networkidle')
                else:
                    self.logger.error("[ERROR] Automatic login failed")
                    raise Exception("Authentication required - automatic login failed")
            else:
                self.logger.error("[ERROR] No credentials available for authentication")
                raise Exception("Authentication required - no credentials available")
    
    async def _get_employee_links(self) -> List[tuple]:
        """Get all employee profile links from the directory page"""
        try:
            # Wait for employee cards to load
            await self.page.wait_for_selector(self.selectors['employee_cards'], timeout=15000)
            
            # Extract employee links
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
            raise
    
    async def _scrape_employee_simple(self, profile_url: str, name: str, image_url: str) -> Optional[EmployeeData]:
        """Scrape basic employee data (SIMPLE mode)"""
        try:
            await self.page.goto(profile_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Extract basic data
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
                    
                    return data;
                }}
            """)
            
            # Create EmployeeData object
            employee = EmployeeData(
                human_name=employee_data.get('human_name') or name,
                email=employee_data.get('email'),
                phone=employee_data.get('phone'),
                position=employee_data.get('position'),
                department=employee_data.get('department'),
                bio=employee_data.get('bio'),
                office_location=self._normalize_office_location(employee_data.get('office_location', '')),
                profile_url=profile_url,
                image_url=employee_data.get('image_url') or image_url
            )
            
            # Download image if enabled
            if self.download_images and employee.image_url and self.image_downloader:
                try:
                    local_path = await self.image_downloader.download_image(
                        employee.image_url, 
                        name.replace(' ', '_')
                    )
                    if local_path:
                        employee.image_local_path = local_path
                except Exception as e:
                    self.logger.warning(f"Failed to download image for {name}: {e}")
            
            return employee
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error scraping profile {profile_url}: {e}")
            return None
    
    async def _scrape_employee_complete(self, profile_url: str, name: str, image_url: str) -> Optional[EmployeeData]:
        """Scrape comprehensive employee data (COMPLETE mode)"""
        try:
            await self.page.goto(profile_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Start with basic data (same as simple mode)
            employee = await self._scrape_employee_simple(profile_url, name, image_url)
            if not employee:
                return None
            
            # Add advanced data extraction for complete mode
            # This is where you would add project extraction, education, etc.
            # For now, we'll just add some additional fields
            
            # Extract additional contact info
            additional_data = await self.page.evaluate("""
                () => {
                    const data = {};
                    
                    // Additional contact methods
                    data.mobile = document.querySelector('a[href^="tel:"]')?.href?.replace('tel:', '') || '';
                    data.teams_url = document.querySelector('a[href*="teams.microsoft.com"]')?.href || '';
                    data.linkedin_url = document.querySelector('a[href*="linkedin.com"]')?.href || '';
                    data.website_url = document.querySelector('a[href*="http"]:not([href*="ennead.com"])')?.href || '';
                    
                    return data;
                }
            """)
            
            # Update employee with additional data
            if additional_data.get('mobile'):
                employee.mobile = additional_data['mobile']
            if additional_data.get('teams_url'):
                employee.teams_url = additional_data['teams_url']
            if additional_data.get('linkedin_url'):
                employee.linkedin_url = additional_data['linkedin_url']
            if additional_data.get('website_url'):
                employee.website_url = additional_data['website_url']
            
            return employee
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error scraping complete profile {profile_url}: {e}")
            return None
    
    def _normalize_office_location(self, location: str) -> str:
        """Normalize office location names to standard format"""
        if not location:
            return ""
            
        location = location.strip().lower()
        
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
        
        if location in location_mapping:
            return location_mapping[location]
        
        for key, value in location_mapping.items():
            if key in location:
                return value
        
        return location.title()
    
    def get_mode_info(self) -> Dict[str, Any]:
        """Get information about the current scraper mode"""
        return {
            'mode': self.mode,
            'is_simple': self.mode == self.MODE_SIMPLE,
            'is_complete': self.mode == self.MODE_COMPLETE,
            'download_images': self.download_images,
            'headless': self.headless,
            'timeout': self.timeout
        }
