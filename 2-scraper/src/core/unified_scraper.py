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
from datetime import datetime

from .models import EmployeeData
from ..services.auth import AutoLogin
from ..services.image_downloader import ImageDownloader
from ..config.settings import ScraperConfig


class UnifiedEmployeeScraper:
    """
    Unified scraper that provides comprehensive data extraction.
    Extracts all available employee information including basic data,
    professional information, projects, education, licenses, and more.
    """
    
    def __init__(self, 
                 base_url: str = "https://ei.ennead.com/employees/1/all-employees",
                 download_images: bool = True,
                 headless: bool = True,
                 timeout: int = 30000,
                 config: Optional[ScraperConfig] = None):
        """
        Initialize the unified scraper.
        
        Args:
            base_url: Base URL of the employee directory page
            download_images: Whether to download profile images
            headless: Whether to run browser in headless mode
            timeout: Page load timeout in milliseconds
            config: Scraper configuration object
        """
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
        
        # Selectors for comprehensive data extraction
        self.selectors = {
            'employee_cards': '.employee-card, .profile-card, [data-employee], .directory_employees .content, .directory_employees [class*="card"], .directory_employees [class*="item"]',
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
        
        self.logger.info("Unified scraper initialized with comprehensive data extraction")
    
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
            
            # Browser arguments for comprehensive scraping
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
            
            # Always enable images for comprehensive data extraction
            # browser_args.append('--disable-images')  # Removed to enable image loading
            
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
            self.logger.info("[SUCCESS] Browser started with comprehensive data extraction")
            
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
        Scrape all employees from the directory with comprehensive data extraction.
        Extracts all available employee information including basic data,
        professional information, projects, education, licenses, and more.
        """
        self.logger.info("Starting comprehensive employee data scraping...")
        
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
                    
                    # Scrape employee data with comprehensive extraction
                    employee = await self._scrape_employee_comprehensive(profile_url, name, image_url)
                    
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
            # Wait for page to fully load (SPA content)
            self.logger.info("[INFO] Waiting for dynamic content to load...")
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(3)  # Additional wait for dynamic content
            
            # Wait for employee cards to load
            try:
                await self.page.wait_for_selector(self.selectors['employee_cards'], timeout=30000)
            except Exception as e:
                # If selector fails, capture DOM for debugging
                self.logger.error(f"[ERROR] Selector failed: {e}")
                if hasattr(self, 'config') and self.config.DEBUG_MODE:
                    await self._capture_debug_info("selector_failed")
                raise
            
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
    
    async def _scrape_employee_basic(self, profile_url: str, name: str, image_url: str) -> Optional[EmployeeData]:
        """Scrape basic employee data"""
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
    
    async def _scrape_employee_comprehensive(self, profile_url: str, name: str, image_url: str) -> Optional[EmployeeData]:
        """Scrape comprehensive employee data with all available information"""
        try:
            await self.page.goto(profile_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Start with basic data
            employee = await self._scrape_employee_basic(profile_url, name, image_url)
            if not employee:
                return None
            
            # Extract comprehensive data
            comprehensive_data = await self.page.evaluate("""
                () => {
                    const data = {};
                    
                    // Additional contact methods
                    data.mobile = document.querySelector('a[href^="tel:"]')?.href?.replace('tel:', '') || '';
                    data.teams_url = document.querySelector('a[href*="teams.microsoft.com"]')?.href || '';
                    data.linkedin_url = document.querySelector('a[href*="linkedin.com"]')?.href || '';
                    data.website_url = document.querySelector('a[href*="http"]:not([href*="ennead.com"])')?.href || '';
                    
                    // Years with firm
                    const yearsText = document.querySelector('.years-with-firm, .tenure, .experience')?.textContent || '';
                    const yearsMatch = yearsText.match(/(\d+)/);
                    data.years_with_firm = yearsMatch ? parseInt(yearsMatch[1]) : null;
                    
                    // Seating assignment
                    data.seat_assignment = document.querySelector('.seat, .desk, .location')?.textContent?.trim() || '';
                    
                    // Computer information
                    data.computer = document.querySelector('.computer, .machine, .device')?.textContent?.trim() || '';
                    
                    // Professional memberships
                    data.memberships = [];
                    const membershipElements = document.querySelectorAll('.membership, .association, .organization');
                    membershipElements.forEach(el => {
                        const text = el.textContent?.trim();
                        if (text) data.memberships.push(text);
                    });
                    
                    // Education
                    data.education = [];
                    const educationElements = document.querySelectorAll('.education-item, .degree, .school');
                    educationElements.forEach(el => {
                        const degree = el.querySelector('.degree, .title')?.textContent?.trim() || '';
                        const school = el.querySelector('.school, .institution')?.textContent?.trim() || '';
                        const year = el.querySelector('.year, .date')?.textContent?.trim() || '';
                        if (degree || school) {
                            data.education.push({
                                'degree': degree,
                                'school': school,
                                'year': year
                            });
                        }
                    });
                    
                    // Licenses and registrations
                    data.licenses = [];
                    const licenseElements = document.querySelectorAll('.license, .certification, .registration');
                    licenseElements.forEach(el => {
                        const name = el.querySelector('.name, .title')?.textContent?.trim() || '';
                        const number = el.querySelector('.number, .id')?.textContent?.trim() || '';
                        const state = el.querySelector('.state, .jurisdiction')?.textContent?.trim() || '';
                        const expiry = el.querySelector('.expiry, .expires')?.textContent?.trim() || '';
                        if (name) {
                            data.licenses.push({
                                'name': name,
                                'number': number,
                                'state': state,
                                'expiry': expiry
                            });
                        }
                    });
                    
                    // Projects
                    data.projects = [];
                    const projectElements = document.querySelectorAll('.project, .work-item, .portfolio-item');
                    projectElements.forEach(el => {
                        const name = el.querySelector('.name, .title')?.textContent?.trim() || '';
                        const description = el.querySelector('.description, .summary')?.textContent?.trim() || '';
                        const role = el.querySelector('.role, .position')?.textContent?.trim() || '';
                        const year = el.querySelector('.year, .date')?.textContent?.trim() || '';
                        if (name) {
                            data.projects.push({
                                'name': name,
                                'description': description,
                                'role': role,
                                'year': year
                            });
                        }
                    });
                    
                    // Recent posts/activity
                    data.recent_posts = [];
                    const postElements = document.querySelectorAll('.post, .activity, .update');
                    postElements.forEach(el => {
                        const title = el.querySelector('.title, .subject')?.textContent?.trim() || '';
                        const content = el.querySelector('.content, .text')?.textContent?.trim() || '';
                        const date = el.querySelector('.date, .timestamp')?.textContent?.trim() || '';
                        if (title || content) {
                            data.recent_posts.push({
                                'title': title,
                                'content': content,
                                'date': date
                            });
                        }
                    });
                    
                    return data;
                }
            """)
            
            # Update employee with comprehensive data
            if comprehensive_data.get('mobile'):
                employee.mobile = comprehensive_data['mobile']
            if comprehensive_data.get('teams_url'):
                employee.teams_url = comprehensive_data['teams_url']
            if comprehensive_data.get('linkedin_url'):
                employee.linkedin_url = comprehensive_data['linkedin_url']
            if comprehensive_data.get('website_url'):
                employee.website_url = comprehensive_data['website_url']
            if comprehensive_data.get('years_with_firm'):
                employee.years_with_firm = comprehensive_data['years_with_firm']
            if comprehensive_data.get('seat_assignment'):
                employee.seat_assignment = comprehensive_data['seat_assignment']
            if comprehensive_data.get('computer'):
                employee.computer = comprehensive_data['computer']
            if comprehensive_data.get('memberships'):
                employee.memberships = comprehensive_data['memberships']
            if comprehensive_data.get('education'):
                employee.education = comprehensive_data['education']
            if comprehensive_data.get('licenses'):
                employee.licenses = comprehensive_data['licenses']
            if comprehensive_data.get('projects'):
                employee.projects = comprehensive_data['projects']
            if comprehensive_data.get('recent_posts'):
                employee.recent_posts = comprehensive_data['recent_posts']
            
            return employee
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error scraping comprehensive profile {profile_url}: {e}")
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
    
    async def _capture_debug_info(self, reason: str):
        """Capture debug information when selectors fail"""
        try:
            # Create debug directory
            debug_dir = Path(__file__).parent.parent.parent.parent / "debug" / "dom_captures"
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            # Capture current page content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_file = debug_dir / f"debug_{reason}_{timestamp}.html"
            
            html_content = await self.page.content()
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"[DEBUG] Captured DOM for {reason} to {html_file}")
            
            # Also capture a screenshot
            screenshot_file = debug_dir / f"debug_{reason}_{timestamp}.png"
            await self.page.screenshot(path=str(screenshot_file))
            self.logger.info(f"[DEBUG] Captured screenshot to {screenshot_file}")
            
            # Analyze what's actually on the page
            await self._analyze_page_structure(debug_dir, timestamp)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to capture debug info: {e}")
    
    async def _analyze_page_structure(self, debug_dir: Path, timestamp: str):
        """Analyze the actual page structure to find correct selectors"""
        try:
            # Get all elements with common patterns
            analysis = await self.page.evaluate("""
                () => {
                    const results = {
                        allElements: [],
                        links: [],
                        cards: [],
                        containers: [],
                        textContent: []
                    };
                    
                    // Find all elements with common patterns
                    const allElements = document.querySelectorAll('*');
                    allElements.forEach((el, index) => {
                        if (index < 100) { // Limit to first 100 elements
                            const tagName = el.tagName.toLowerCase();
                            const className = el.className || '';
                            const id = el.id || '';
                            const href = el.href || '';
                            const text = el.textContent?.trim().substring(0, 50) || '';
                            
                            results.allElements.push({
                                tag: tagName,
                                class: className,
                                id: id,
                                href: href,
                                text: text
                            });
                            
                            // Look for links
                            if (tagName === 'a' && href) {
                                results.links.push({
                                    href: href,
                                    text: text,
                                    class: className
                                });
                            }
                            
                            // Look for card-like elements (fix className check)
                            if (typeof className === 'string' && (className.includes('card') || className.includes('item') || 
                                className.includes('employee') || className.includes('person'))) {
                                results.cards.push({
                                    tag: tagName,
                                    class: className,
                                    id: id,
                                    text: text
                                });
                            }
                            
                            // Look for container elements
                            if (typeof className === 'string' && (className.includes('container') || className.includes('wrapper') ||
                                className.includes('content') || className.includes('main'))) {
                                results.containers.push({
                                    tag: tagName,
                                    class: className,
                                    id: id,
                                    text: text
                                });
                            }
                        }
                    });
                    
                    return results;
                }
            """)
            
            # Save analysis
            analysis_file = debug_dir / f"page_analysis_{timestamp}.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2)
            
            self.logger.info(f"[DEBUG] Page analysis saved to {analysis_file}")
            
            # Log key findings
            self.logger.info(f"[DEBUG] Found {len(analysis['links'])} links")
            self.logger.info(f"[DEBUG] Found {len(analysis['cards'])} card-like elements")
            self.logger.info(f"[DEBUG] Found {len(analysis['containers'])} container elements")
            
            # Show sample links
            if analysis['links']:
                self.logger.info("[DEBUG] Sample links found:")
                for link in analysis['links'][:5]:
                    self.logger.info(f"  - {link['href']} ({link['text']})")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to analyze page structure: {e}")
    
    def get_scraper_info(self) -> Dict[str, Any]:
        """Get information about the scraper configuration"""
        return {
            'comprehensive_mode': True,
            'download_images': self.download_images,
            'headless': self.headless,
            'timeout': self.timeout,
            'base_url': self.base_url
        }
