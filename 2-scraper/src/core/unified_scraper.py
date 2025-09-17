"""
Unified Employee Scraper
Combines SimpleEmployeeScraper and CompleteScraper into one flexible scraper
that can run in different modes for different use cases.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Playwright
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
        if download_images:
            # Set the correct path for images to be saved in docs/assets/images
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            images_dir = project_root / "docs" / "assets" / "images"
            self.image_downloader = ImageDownloader(str(images_dir))
        else:
            self.image_downloader = None
        self.auto_login = AutoLogin()
        
        # Browser components
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None
        
        # Scraped data
        self.employees: List[EmployeeData] = []
        
        # Selectors for comprehensive data extraction
        self.selectors = {
            'employee_cards': '.gridViewCell, .ActivityBox-sc-ik8ilm-0, .gridViewStyles__Cell-sc-ipm8x5-2',
            'profile_image': '.EntityHeader__HeaderPhoto-sc-1yar8fm-1, .gridViewStyles__Img-sc-ipm8x5-8, .gridViewStyles__ImgBox-sc-ipm8x5-4 img',
            'employee_name': '.gridViewStyles__Field-sc-ipm8x5-22.csVUxd.field.bold a, .gridViewStyles__Field-sc-ipm8x5-22.bold a',
            'employee_title': '.EntityHeader__NormalLine-sc-1yar8fm-0, .gridViewStyles__Field-sc-ipm8x5-22.eVXxsE.field',
            'profile_link': 'a[href*="/employee/"]',
            'email_link': 'a[href^="mailto:"]',
            'phone_link': 'a[href^="tel:"]',
            'bio_text': '.EntityFields__InfoFieldValue-sc-129sxys-5, .bio, .about, .description, .employee-bio',
            'contact_info': '.contact-info, .employee-contact',
            'department': '.department, .team, .division'
        }
        
        self.logger.info("Unified scraper initialized with comprehensive data extraction")

    # --- Normalization helpers -------------------------------------------------
    def _normalize_position(self, position: Optional[str]) -> str:
        """Return a usable position string for UI.

        Empty/whitespace/None becomes the literal "Position not available" so
        downstream consumers can always display a consistent label.
        """
        try:
            if position and isinstance(position, str) and position.strip():
                return position.strip()
        except Exception:
            pass
        return "Position not available"

    def _sanitize_bio(self, bio: Optional[str]) -> Optional[str]:
        """Discard bios that look numeric-only or not meaningful.

        If the extracted bio is composed only of digits, punctuation, or
        trivial tokens (e.g., a lone year like "2022"), treat it as missing
        and return None.
        """
        if not bio:
            return None
        if not isinstance(bio, str):
            return None
        text = bio.strip()
        if not text:
            return None
        import re
        # If after removing common separators there are no letters, drop it
        letters = re.findall(r"[A-Za-z]", text)
        if len(letters) == 0:
            return None
        # Extremely short bios (<= 3 chars) are likely noise
        if len(text) <= 3:
            return None
        return text
    
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
            self.playwright = await async_playwright().start()
            
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
            
            self.browser = await self.playwright.chromium.launch(
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
            if self.playwright:
                await self.playwright.stop()
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
            
            # Apply explicit limit if provided
            if hasattr(self.config, 'LIMIT') and self.config.LIMIT is not None:
                limit_count = int(self.config.LIMIT)
                employee_links = employee_links[:limit_count]
                self.logger.info(f"[INFO] Limiting to first {limit_count} employees per --limit")
            
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
                        # Create basic employee data even if detailed scraping failed
                        employee = EmployeeData(
                            human_name=name,
                            profile_url=profile_url,
                            image_url=image_url,
                            scraped_at=datetime.now().isoformat()
                        )
                        self.employees.append(employee)
                        self.logger.warning(f"[WARNING] Failed to scrape detailed data for {name}, created basic entry")
                    
                    # Always save individual JSON file (regardless of scraping success)
                    saved_path = await self._save_individual_employee(employee)
                    
                    if saved_path:
                        print(f"✅ SUCCESS: {name} - JSON saved to {saved_path}")
                        self.logger.info(f"[SUCCESS] Individual JSON saved for {name}")
                    else:
                        print(f"⚠️ WARNING: {name} - Failed to save JSON")
                        self.logger.error(f"[ERROR] Failed to save individual JSON for {name}")
                    
                    # Delay between requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"[ERROR] Error scraping {name}: {e}")
                    
                    # Even if there's an exception, create basic employee data and save individual file
                    try:
                        employee = EmployeeData(
                            human_name=name,
                            profile_url=profile_url if 'profile_url' in locals() else None,
                            image_url=image_url if 'image_url' in locals() else None,
                            scraped_at=datetime.now().isoformat()
                        )
                        self.employees.append(employee)
                        
                        # Save individual JSON file even after exception
                        saved_path = await self._save_individual_employee(employee)
                        if saved_path:
                            print(f"✅ RECOVERY: {name} - Basic JSON saved after error")
                            self.logger.info(f"[RECOVERY] Created basic entry for {name} after error")
                        
                    except Exception as save_error:
                        self.logger.error(f"[CRITICAL] Failed to create basic entry for {name}: {save_error}")
                    
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
            
            # Scroll to load all employees (infinite scroll)
            self.logger.info("[INFO] Scrolling to load all employees...")
            await self._scroll_to_load_all_employees()
            
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
    
    
    async def _scrape_employee_comprehensive(self, profile_url: str, name: str, image_url: str) -> Optional[EmployeeData]:
        """Scrape comprehensive employee data with all available information"""
        try:
            await self.page.goto(profile_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Debug: Check if we're actually on the profile page
            current_url = self.page.url
            page_title = await self.page.title()
            self.logger.info(f"    Current URL after navigation: {current_url}")
            self.logger.info(f"    Page title: {page_title}")
            
            # Capture DOM for debugging individual profile pages - wait for content to load first
            if hasattr(self, 'config') and self.config.DEBUG_MODE:
                # Wait for the actual profile content to be visible
                try:
                    await self.page.wait_for_selector('h1:has-text("Personal Bio"), h1:has-text("Education"), h1:has-text("Projects")', timeout=10000)
                    self.logger.info("    Profile content is visible, capturing DOM...")
                    await asyncio.sleep(2)  # Additional wait for full rendering
                    await self._capture_debug_info(f"profile_page_{name.replace(' ', '_')}")
                except Exception as e:
                    self.logger.warning(f"    Could not wait for profile content: {e}")
                    # Capture anyway
                await self._capture_debug_info(f"profile_page_{name.replace(' ', '_')}")
            
            # Debug: Check what name is being extracted
            debug_name = await self.page.evaluate("""
                () => {
                    const h1 = document.querySelector('h1');
                    const entityHeader = document.querySelector('h1[class*="EntityHeader"], h1[class*="entityHeader"], h1[class*="header"], h1[class*="Header"]');
                    const allH1s = document.querySelectorAll('h1');
                    return {
                        firstH1: h1?.textContent?.trim() || 'none',
                        entityHeader: entityHeader?.textContent?.trim() || 'none',
                        allH1s: Array.from(allH1s).map(h => h.textContent?.trim()).filter(t => t)
                    };
                }
            """)
            self.logger.info(f"    Debug name extraction: {debug_name}")
            
            # Extract basic employee data inline
            basic_data = await self.page.evaluate(f"""
                () => {{
                    const data = {{}};
                    
                    // Basic information - use more specific selectors for employee name
                    data.human_name = document.querySelector('h1[class*="EntityHeader"], h1[class*="entityHeader"], h1[class*="header"], h1[class*="Header"], h1:not([class*="section"])')?.textContent?.trim() || 
                                     document.querySelector('h1')?.textContent?.trim() || '';
                    data.email = document.querySelector('a[href^="mailto:"]')?.href?.replace('mailto:', '') || '';
                    data.phone = document.querySelector('a[href^="tel:"]')?.href?.replace('tel:', '') || '';
                    
                    // Position and department - be more specific to avoid picking up the name
                    // Look for position/title elements that are NOT the main name
                    const positionSelectors = [
                        '.EntityHeader__NormalLine-sc-1yar8fm-0:not(:first-child)',
                        '.position:not(:first-child)',
                        '.title:not(:first-child)',
                        '.job-title:not(:first-child)',
                        '.role:not(:first-child)',
                        '[data-kafieldname*="title"]',
                        '[data-kafieldname*="position"]'
                    ];
                    
                    let position = '';
                    for (const selector of positionSelectors) {{
                        const el = document.querySelector(selector);
                        if (el && el.textContent?.trim() && el.textContent.trim() !== data.human_name) {{
                            position = el.textContent.trim();
                            break;
                        }}
                    }}
                    data.position = position;
                    
                    data.department = document.querySelector('.department, .team, .division, .group')?.textContent?.trim() || '';
                    
                    // Bio - use the correct class for bio content
                    const bioEl = document.querySelector('.EntityFields__InfoFieldValue-sc-129sxys-5, .bio-content, .about-content, .description-content, .employee-bio-content, [data-bio]');
                    data.bio = bioEl ? bioEl.textContent?.trim() : null;
                    
                    // Office location
                    data.office_location = document.querySelector('.location, .office, .address')?.textContent?.trim() || '';
                    
                    // Profile image
                    const img = document.querySelector('{self.selectors['profile_image']}');
                    data.image_url = img ? img.src : '';
                    
                    return data;
                }}
            """)
            
            # Create EmployeeData object with basic data
            employee = EmployeeData(
                human_name=basic_data.get('human_name') or name,
                email=basic_data.get('email'),
                phone=basic_data.get('phone'),
                position=self._normalize_position(basic_data.get('position')),
                department=basic_data.get('department'),
                bio=self._sanitize_bio(basic_data.get('bio')),
                office_location=basic_data.get('office_location', ''),
                profile_url=profile_url,
                image_url=basic_data.get('image_url') or image_url
            )
            
            # Override the human_name with the name from the directory (more reliable)
            if name and name.strip():
                employee.human_name = name.strip()
                self.logger.info(f"    Using directory name: {name}")
            
            # Wait for the page content to load - wait for profile content to appear
            try:
                # Wait for the main profile content to load
                await self.page.wait_for_selector('h1:has-text("Personal Bio"), h1:has-text("Education"), h1:has-text("Projects")', timeout=15000)
                self.logger.info("    Profile content loaded")
                
                # Additional wait for dynamic content to fully render
                await asyncio.sleep(3)
                
                # Try to wait for specific sections
                try:
                    await self.page.wait_for_selector('[data-kagridname="employeeDegrees"]', timeout=5000)
                    self.logger.info("    Education section loaded")
                except:
                    self.logger.info("    Education section not found")
                    
            except Exception as e:
                self.logger.info(f"    Profile content loading timeout: {e}")
                # Continue anyway - we'll try to extract what we can
            
            # Extract comprehensive data using text-based parsing
            self.logger.info("    Starting comprehensive data extraction using text-based parsing...")
            
            # Extract basic contact information using JavaScript (still reliable)
            basic_contact_data = await self.page.evaluate("""
                () => {
                    const data = {};
                    data.mobile = document.querySelector('a[href^="tel:"]')?.href?.replace('tel:', '') || '';
                    data.teams_url = document.querySelector('a[href*="teams.microsoft.com"]')?.href || '';
                    data.linkedin_url = document.querySelector('a[href*="linkedin.com"]')?.href || '';
                    data.website_url = document.querySelector('a[href*="http"]:not([href*="ennead.com"])')?.href || '';
                    return data;
                }
            """)
            
            # Initialize comprehensive_data with basic contact info
            comprehensive_data = basic_contact_data
            
            # Extract Personal Bio using text-based parsing
            self.logger.info("    Extracting Personal Bio using text-based parser...")
            bio_data = await self._parse_section_by_text("Personal Bio")
            if bio_data and 'value' in bio_data:
                employee.bio = self._sanitize_bio(bio_data['value'])
                self.logger.info(f"    Found Personal Bio: {len(employee.bio)} characters")
            
            # Extract Years with Firm using text-based parsing
            self.logger.info("    Extracting Years with Firm using text-based parser...")
            years_data = await self._parse_section_by_text("The Basics")
            if years_data:
                self.logger.info(f"    Years data keys: {list(years_data.keys())}")
                
                # Look for "Years With Firm" in the data
                for key, value in years_data.items():
                    if 'years' in key.lower() or 'firm' in key.lower():
                        try:
                            # Handle concatenated data like "Years With Firm3"
                            import re
                            if isinstance(value, str):
                                # Extract number from concatenated string
                                number_match = re.search(r'(\d+)', str(value))
                                if number_match:
                                    employee.years_with_firm = int(number_match.group(1))
                                    self.logger.info(f"    Found Years with Firm: {employee.years_with_firm}")
                                    break
                            else:
                                employee.years_with_firm = int(value)
                                self.logger.info(f"    Found Years with Firm: {employee.years_with_firm}")
                                break
                        except (ValueError, TypeError):
                            pass
                
                # Also check if there's a direct value
                if 'value' in years_data and 'Years With Firm' in years_data['value']:
                    import re
                    years_match = re.search(r'Years With Firm\s*(\d+)', years_data['value'])
                    if years_match:
                        employee.years_with_firm = int(years_match.group(1))
                        self.logger.info(f"    Found Years with Firm from text: {employee.years_with_firm}")
                
                # If still not found, try to extract from any value that contains a number
                if not employee.years_with_firm:
                    for key, value in years_data.items():
                        if isinstance(value, str) and re.search(r'\d+', value):
                            number_match = re.search(r'(\d+)', value)
                            if number_match:
                                employee.years_with_firm = int(number_match.group(1))
                                self.logger.info(f"    Found Years with Firm from number in '{key}': {employee.years_with_firm}")
                                break
            
            # Extract Memberships using text-based parsing
            self.logger.info("    Extracting Memberships using text-based parser...")
            memberships_data = await self._parse_section_by_text("Memberships")
            if memberships_data:
                if 'value' in memberships_data:
                    # Simple text format - split by common separators
                    text = memberships_data['value']
                    memberships = [m.strip() for m in text.split(',') if m.strip()]
                    employee.memberships = memberships
                    self.logger.info(f"    Found Memberships: {memberships}")
                else:
                    # Table format - extract membership names
                    memberships = []
                    for key, value in memberships_data.items():
                        if value and str(value).strip():
                            memberships.append(str(value).strip())
                    employee.memberships = memberships
                    self.logger.info(f"    Found Memberships: {memberships}")
            
            # Update employee with basic contact data
            if comprehensive_data.get('mobile'):
                employee.mobile = comprehensive_data['mobile']
            if comprehensive_data.get('teams_url'):
                employee.teams_url = comprehensive_data['teams_url']
            if comprehensive_data.get('linkedin_url'):
                employee.linkedin_url = comprehensive_data['linkedin_url']
            if comprehensive_data.get('website_url'):
                employee.website_url = comprehensive_data['website_url']
            # Extract education and licenses using the new text-based parser
            self.logger.info("    Extracting education data using text-based parser...")
            employee.education = await self._extract_education_data()
            
            self.logger.info("    Extracting licenses data using text-based parser...")
            employee.licenses = await self._extract_licenses_data()
            
            # Extract projects using text-based parser
            self.logger.info("    Extracting projects data using text-based parser...")
            employee.projects = await self._extract_projects_data()
            
            # Fallback to old method if new parser didn't find anything
            if not employee.education and comprehensive_data.get('education'):
                self.logger.info("    Fallback: Using old education extraction method")
                employee.education = comprehensive_data['education']
            
            if not employee.licenses and comprehensive_data.get('licenses'):
                self.logger.info("    Fallback: Using old licenses extraction method")
                employee.licenses = comprehensive_data['licenses']
            
            if not employee.projects and comprehensive_data.get('projects'):
                self.logger.info("    Fallback: Using old projects extraction method")
                employee.projects = comprehensive_data['projects']
            if comprehensive_data.get('recent_posts'):
                employee.recent_posts = comprehensive_data['recent_posts']
            
            
            # Handle "Show All" projects button if found
            self.logger.info(f"    Looking for 'Show All' projects button for {name}...")
            
            # Debug: Check what buttons/links are available on the page
            if hasattr(self, 'config') and self.config.DEBUG_MODE:
                available_buttons = await self.page.evaluate("""
                    () => {
                        const buttons = [];
                        const allButtons = document.querySelectorAll('button, a, [role="button"]');
                        allButtons.forEach((btn, index) => {
                            const text = btn.textContent?.trim() || '';
                            const classes = btn.className || '';
                            const href = btn.href || '';
                            if (text.toLowerCase().includes('show') || classes.toLowerCase().includes('show') || classes.toLowerCase().includes('pill')) {
                                buttons.push({
                                    index: index,
                                    tag: btn.tagName,
                                    text: text,
                                    classes: classes,
                                    href: href
                                });
                            }
                        });
                        return buttons;
                    }
                """)
                self.logger.info(f"    Available Show/Pill buttons for {name}: {available_buttons}")
            
            # Try multiple selectors for the Show All button
            show_all_selectors = [
                '.RoundedBox-sc-1nzfcbz-0.PillBox-sc-p125c4-0.fQdvmA.driLso.pill',  # Original specific selector
                'button:has-text("Show All")',  # More generic text-based selector
                'a:has-text("Show All")',       # Link-based selector
                '[class*="pill"]:has-text("Show All")',  # Class-based selector
                'button[class*="Show"]',        # Button with "Show" in class
                'a[class*="Show"]',             # Link with "Show" in class
                'button:has-text("Show")',      # Any button with "Show" text
                'a:has-text("Show")'            # Any link with "Show" text
            ]
            
            show_all_button = None
            working_selector = None
            
            for selector in show_all_selectors:
                try:
                    show_all_button = await self.page.query_selector(selector)
                    if show_all_button:
                        button_text = await show_all_button.text_content()
                        self.logger.info(f"    Found button with selector '{selector}': '{button_text}'")
                        if button_text and 'Show All' in button_text:
                            working_selector = selector
                            break
                        else:
                            show_all_button = None
                except Exception as e:
                    self.logger.debug(f"    Selector '{selector}' failed: {e}")
                    continue
            
            if show_all_button and working_selector:
                try:
                    self.logger.info(f"    Found 'Show All' projects button for {name} using selector: {working_selector}")
                    self.logger.info(f"    Button text: '{await show_all_button.text_content()}'")
                    
                    # Click the "Show All" button
                    await show_all_button.click()
                    self.logger.info(f"    Clicked 'Show All' button for {name}")
                    
                    # Wait for the detailed project table to load
                    try:
                        await self.page.wait_for_selector('table, .project, .projects, .k-grid', state='visible', timeout=10000)
                        self.logger.info(f"    Project table loaded for {name}")
                    except Exception as e:
                        self.logger.warning(f"    Project table not found after clicking Show All for {name}: {e}")
                        # Continue anyway - we might still find projects
                    
                    # Extract projects from the detailed table
                    detailed_projects = await self.page.evaluate("""
                        () => {
                            const projects = {};
                            const tableCells = document.querySelectorAll('.tableViewStyles__StyledCell-sc-nfq3ae-1.hZvVqM.styledTableCell');
                            
                            tableCells.forEach(cell => {
                                const projectLink = cell.querySelector('a[href*="/project/"]');
                                if (projectLink) {
                                    const name = projectLink.textContent?.trim();
                                    const url = projectLink.href;
                                    if (name && url && name.length > 1) {
                                        const projectKey = `proj_${Object.keys(projects).length + 1}`;
                                        projects[projectKey] = {
                                            'name': name,
                                            'description': '',
                                            'role': '',
                                            'year': '',
                                            'client': '',
                                            'number': '',
                                            'url': url,
                                            'source': 'detailed_table'
                                        };
                                    }
                                }
                            });
                            
                            return projects;
                        }
                    """)
                    
                    # Add detailed projects to existing projects (avoid duplicates)
                    for project_key, detailed_project in detailed_projects.items():
                        # Check if we already have this project by URL
                        existing_project = next((p for p in employee.projects.values() if p['url'] == detailed_project['url']), None)
                        if not existing_project:
                            employee.projects[project_key] = detailed_project
                    
                    self.logger.info(f"    Found {len(detailed_projects)} additional projects from detailed table")
                    
                    # Avoid go_back; stay on page and continue
                    
                except Exception as e:
                    self.logger.warning(f"    Failed to extract detailed projects for {name}: {e}")
            else:
                self.logger.info(f"    No 'Show All' button found for {name}")
            
            # Download the actual profile image using the extracted image URL
            if self.download_images and self.image_downloader and employee.image_url:
                try:
                    local_path = await self.image_downloader.download_image(
                        employee.image_url, 
                        name,
                        self.page  # Pass page for authenticated requests
                    )
                    if local_path:
                        employee.image_local_path = local_path
                        self.logger.info(f"Downloaded profile image for {name}: {local_path}")
                    else:
                        # Fallback to screenshot if download fails
                        local_path = await self.image_downloader.capture_preview_image(
                            self.page, 
                            name,
                            image_selector='img[src*="/api/image/"]:not([src*="favicon"]):not([src*="logo"]):not([src*="icon"])'
                        )
                        if local_path:
                            employee.image_local_path = local_path
                            self.logger.info(f"Captured preview image for {name}: {local_path}")
                except Exception as e:
                    self.logger.error(f"Failed to download image for {name}: {e}")
            
            # Print detailed extracted data in blue after comprehensive extraction
            self._print_extracted_data(employee, name)
            
            return employee
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error scraping comprehensive profile {profile_url}: {e}")
            return None
    
    def _print_extracted_data(self, employee: EmployeeData, name: str):
        """Print detailed extracted data in blue color"""
        print(f"\n🔵 DETAILED EXTRACTED DATA FOR {name.upper()}:")
        print(f"🔵 {'='*60}")
        
        # Basic Information
        print(f"🔵 📋 BASIC INFORMATION:")
        print(f"🔵   • Name: {employee.human_name}")
        print(f"🔵   • Position: {employee.position}")
        print(f"🔵   • Department: {employee.department}")
        print(f"🔵   • Years with Firm: {employee.years_with_firm}")
        print(f"🔵   • Office Location: {employee.office_location}")
        
        # Contact Information
        print(f"🔵 📞 CONTACT INFORMATION:")
        print(f"🔵   • Email: {employee.email}")
        print(f"🔵   • Phone: {employee.phone}")
        print(f"🔵   • Mobile: {employee.mobile}")
        print(f"🔵   • Teams URL: {employee.teams_url}")
        print(f"🔵   • LinkedIn URL: {employee.linkedin_url}")
        print(f"🔵   • Website URL: {employee.website_url}")
        
        # Bio and Personal Information
        print(f"🔵 📝 BIO & PERSONAL:")
        bio_preview = employee.bio[:100] + "..." if employee.bio and len(employee.bio) > 100 else employee.bio
        print(f"🔵   • Bio: {bio_preview}")
        
        # Education
        print(f"🔵 🎓 EDUCATION:")
        if employee.education:
            for i, edu in enumerate(employee.education, 1):
                print(f"🔵   • Education {i}: {edu.get('institution', 'N/A')} - {edu.get('degree', 'N/A')} - {edu.get('specialty', 'N/A')}")
        else:
            print(f"🔵   • No education data found")
        
        # Licenses
        print(f"🔵 📜 LICENSES:")
        if employee.licenses:
            for i, license in enumerate(employee.licenses, 1):
                print(f"🔵   • License {i}: {license.get('license', 'N/A')} - {license.get('state', 'N/A')} - {license.get('number', 'N/A')}")
        else:
            print(f"🔵   • No licenses data found")
        
        # Projects
        print(f"🔵 🏗️ PROJECTS:")
        if employee.projects:
            project_items = list(employee.projects.items())
            for i, (project_key, project) in enumerate(project_items[:3], 1):  # Show first 3 projects
                source_info = f" ({project.get('source', 'unknown')})" if project.get('source') else ""
                print(f"🔵   • Project {i}: {project.get('name', 'N/A')} - {project.get('role', 'N/A')}{source_info}")
            if len(project_items) > 3:
                print(f"🔵   • ... and {len(project_items) - 3} more projects")
        else:
            print(f"🔵   • No projects data found")
        
        # Memberships
        print(f"🔵 👥 MEMBERSHIPS:")
        if employee.memberships:
            for i, membership in enumerate(employee.memberships, 1):
                print(f"🔵   • Membership {i}: {membership}")
        else:
            print(f"🔵   • No memberships data found")
        
        # Image Information
        print(f"🔵 🖼️ IMAGE INFORMATION:")
        print(f"🔵   • Image URL: {employee.image_url}")
        print(f"🔵   • Local Image Path: {employee.image_local_path}")
        
        # Profile Information
        print(f"🔵 🔗 PROFILE INFORMATION:")
        print(f"🔵   • Profile URL: {employee.profile_url}")
        print(f"🔵   • Scraped At: {employee.scraped_at}")
        
        print(f"🔵 {'='*60}\n")
    
    # Removed office location normalization; use raw data only
    
    async def _save_individual_employee(self, employee: EmployeeData) -> str:
        """Save individual employee as JSON file immediately"""
        try:
            from pathlib import Path
            import json
            
            # Set output paths - always use docs folder relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            output_path = project_root / "docs" / "assets"
            individual_employees_dir = output_path / "individual_employees"
            individual_employees_dir.mkdir(parents=True, exist_ok=True)
            
            # Debug: Log the directory structure
            self.logger.info(f"[DEBUG] Project root: {project_root}")
            self.logger.info(f"[DEBUG] Output path: {output_path}")
            self.logger.info(f"[DEBUG] Individual employees dir: {individual_employees_dir}")
            self.logger.info(f"[DEBUG] Directory exists: {individual_employees_dir.exists()}")
            
            # Create filename from employee name
            employee_name = employee.human_name or "unknown"
            
            # Validate that this looks like a real employee name (not a section header)
            invalid_names = ['personal bio', 'the basics', 'education', 'contact info', 'recent posts', 'projects', 'i\'m a resource for']
            if employee_name.lower() in invalid_names:
                self.logger.warning(f"[SKIP] Skipping invalid employee name: {employee_name}")
                return ""
            
            clean_name = employee_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{clean_name}.json"
            file_path = individual_employees_dir / filename
            
            # Save the employee data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(employee.to_dict(), f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"[SAVED] Individual JSON: {filename}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to save individual JSON for {employee.human_name}: {e}")
            return ""
    
    async def _scroll_to_load_all_employees(self):
        """Scroll down to load all employees via infinite scroll with overlap"""
        try:
            previous_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 30  # Increased to allow more thorough scrolling
            no_new_content_count = 0  # Track consecutive attempts with no new content
            max_no_new_content = 3  # Stop after 3 consecutive attempts with no new content
            
            while scroll_attempts < max_scroll_attempts:
                # Count current employees
                current_count = await self.page.evaluate(f"""
                    () => {{
                        return document.querySelectorAll('{self.selectors['employee_cards']}').length;
                    }}
                """)
                
                self.logger.info(f"[INFO] Found {current_count} employees so far...")
                
                # If no new employees loaded, increment counter
                if current_count == previous_count and scroll_attempts > 0:
                    no_new_content_count += 1
                    self.logger.info(f"[INFO] No new employees loaded after scroll {scroll_attempts}. Count: {no_new_content_count}/{max_no_new_content}")
                    
                    # If we've had no new content for several attempts, we're done
                    if no_new_content_count >= max_no_new_content:
                        self.logger.info(f"[INFO] No new employees loaded for {max_no_new_content} consecutive attempts. Total: {current_count}")
                    break
                else:
                    # Reset counter if we found new content
                    no_new_content_count = 0
                
                # Scroll with overlap - scroll to 80% of current height instead of 100%
                current_height = await self.page.evaluate("document.body.scrollHeight")
                scroll_position = int(current_height * 0.8)  # Scroll to 80% of current height
                
                self.logger.info(f"[INFO] Scrolling to position {scroll_position} (80% of {current_height})")
                await self.page.evaluate(f"window.scrollTo(0, {scroll_position})")
                
                # Wait for content to load with longer delays
                await asyncio.sleep(3)  # Increased from 2 to 3 seconds
                
                # Wait for network to be idle
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=15000)  # Increased timeout
                except Exception as e:
                    self.logger.info(f"[INFO] Network idle timeout, continuing...")
                
                # Additional wait to ensure all content is loaded
                await asyncio.sleep(2)
                
                # Verify that we actually scrolled and content loaded
                new_height = await self.page.evaluate("document.body.scrollHeight")
                if new_height > current_height:
                    self.logger.info(f"[INFO] Page height increased from {current_height} to {new_height}")
                else:
                    self.logger.info(f"[INFO] Page height unchanged at {current_height}")
                
                previous_count = current_count
                scroll_attempts += 1
            
            # Final scroll to bottom to ensure we get everything
            self.logger.info(f"[INFO] Performing final scroll to bottom...")
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            
            # Get final count
            final_count = await self.page.evaluate(f"""
                () => {{
                    return document.querySelectorAll('{self.selectors['employee_cards']}').length;
                }}
            """)
            
            self.logger.info(f"[SUCCESS] Finished scrolling. Total employees found: {final_count}")
            
        except Exception as e:
            self.logger.warning(f"[WARNING] Error during scrolling: {e}")
            # Continue anyway - we'll work with whatever employees we found
    
    async def _capture_debug_info(self, reason: str):
        """Capture debug information when selectors fail"""
        try:
            # Create debug directory
            debug_dir = Path(__file__).parent.parent.parent.parent / "debug" / "dom_captures"
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            # Wait a bit more for content to fully render
            await asyncio.sleep(1)
            
            # Capture current page content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_file = debug_dir / f"debug_{reason}_{timestamp}.html"
            
            # Get the full HTML content after JavaScript has rendered
            html_content = await self.page.content()
            
            # Try to get a more readable version by evaluating the DOM structure
            try:
                readable_dom = await self.page.evaluate("""
                    () => {
                        // Get the main content area
                        const mainContent = document.querySelector('#page-content, [class*="profile"], [class*="Profile"], [class*="employee"], [class*="Employee"], [class*="content"], [class*="Content"], [class*="main"], [class*="Main"]');
                        if (mainContent) {
                            return mainContent.outerHTML;
                        }
                        // Fallback to body
                        return document.body.outerHTML;
                    }
                """)
                
                if readable_dom and len(readable_dom) > 1000:  # Make sure we got substantial content
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(f"<!-- Captured at {datetime.now().isoformat()} -->\n")
                        f.write(f"<!-- Reason: {reason} -->\n")
                        f.write("<!DOCTYPE html>\n<html><head><title>Profile Content</title></head><body>\n")
                        f.write(readable_dom)
                        f.write("\n</body></html>")
                    self.logger.info(f"[DEBUG] Captured readable DOM for {reason} to {html_file}")
                else:
                    # Fallback to full page content
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self.logger.info(f"[DEBUG] Captured full DOM for {reason} to {html_file}")
            except Exception as e:
                # Fallback to full page content
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.info(f"[DEBUG] Captured full DOM for {reason} to {html_file} (fallback)")
            
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
    
    async def _parse_section_by_text(self, section_name: str) -> Dict[str, Any]:
        """
        Parse a section by finding its header text, then extracting data below it.
        Handles both simple values and table structures.
        
        Args:
            section_name: The text to look for in headers (e.g., "Education", "Contact Info")
            
        Returns:
            Dict containing the parsed data:
            - For simple sections: {'value': 'extracted_text'}
            - For table sections: {'row_key': {'header1': 'value1', 'header2': 'value2'}}
        """
        try:
            # Find the section header by text
            section_data = await self.page.evaluate(f"""
                () => {{
                    const sectionName = '{section_name}';
                    const results = {{
                        found: false,
                        sectionType: 'none',
                        data: {{}},
                        rawText: ''
                    }};
                    
                    // Look for section headers (h1, h2, h3, h4, h5, h6, or elements with common header classes)
                    const headerSelectors = [
                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                        '[class*="header"]', '[class*="title"]', '[class*="section"]',
                        '[class*="block"]', '[class*="field"]'
                    ];
                    
                    let sectionHeader = null;
                    let sectionContainer = null;
                    
                    // Try to find the section header
                    for (const selector of headerSelectors) {{
                        const headers = document.querySelectorAll(selector);
                        for (const header of headers) {{
                            const text = header.textContent?.trim().toLowerCase() || '';
                            if (text.includes(sectionName.toLowerCase())) {{
                                sectionHeader = header;
                                sectionContainer = header.closest('.EntityFields, .section, .block, .field, .container, div');
                                break;
                            }}
                        }}
                        if (sectionHeader) break;
                    }}
                    
                    if (!sectionHeader) {{
                        return results;
                    }}
                    
                    results.found = true;
                    results.rawText = sectionContainer ? sectionContainer.textContent : '';
                    
                    // Determine if this is a table or simple section
                    const tableElements = sectionContainer ? sectionContainer.querySelectorAll('table, [class*="table"], [class*="grid"], [class*="Table"], [class*="Grid"]') : [];
                    const rowElements = sectionContainer ? sectionContainer.querySelectorAll('tr, [class*="row"], [class*="Row"], [class*="tr"], [class*="Tr"]') : [];
                    
                    if (tableElements.length > 0 || rowElements.length > 0) {{
                        // This is a table section
                        results.sectionType = 'table';
                        
                        // Try to extract table data
                        const table = tableElements[0] || sectionContainer;
                        const rows = table.querySelectorAll('tr, [class*="row"], [class*="Row"], [class*="tr"], [class*="Tr"]');
                        
                        if (rows.length > 0) {{
                            // Extract headers from first row
                            const firstRow = rows[0];
                            const headers = [];
                            const headerCells = firstRow.querySelectorAll('th, td, [class*="cell"], [class*="Cell"], [class*="header"], [class*="Header"], [class*="th"], [class*="Th"], [class*="td"], [class*="Td"]');
                            
                            headerCells.forEach(cell => {{
                                const text = cell.textContent?.trim();
                                if (text) headers.push(text);
                            }});
                            
                            // If no headers found, try to infer from data rows
                            if (headers.length === 0 && rows.length > 1) {{
                                const dataRow = rows[1];
                                const dataCells = dataRow.querySelectorAll('td, [class*="cell"], [class*="Cell"], [class*="td"], [class*="Td"]');
                                headers.length = dataCells.length;
                                headers.fill('column');
                                headers.forEach((_, i) => headers[i] = `column_${{i + 1}}`);
                            }}
                            
                            // Extract data rows
                            for (let i = 1; i < rows.length; i++) {{
                                const row = rows[i];
                                const cells = row.querySelectorAll('td, [class*="cell"], [class*="Cell"], [class*="td"], [class*="Td"]');
                                const rowData = {{}};
                                let rowKey = '';
                                
                                cells.forEach((cell, cellIndex) => {{
                                    const text = cell.textContent?.trim();
                                    if (text) {{
                                        const header = headers[cellIndex] || `column_${{cellIndex + 1}}`;
                                        rowData[header] = text;
                                        
                                        // Use first column as row key
                                        if (cellIndex === 0) {{
                                            rowKey = text;
                                        }}
                                    }}
                                }});
                                
                                if (rowKey && Object.keys(rowData).length > 0) {{
                                    results.data[rowKey] = rowData;
                                }}
                            }}
                        }} else {{
                            // No clear table structure, try to parse as key-value pairs
                            const fieldElements = sectionContainer.querySelectorAll('[class*="field"], [class*="Field"], [data-kafieldname], [class*="value"], [class*="Value"], [class*="text"], [class*="Text"]');
                            fieldElements.forEach(field => {{
                                const text = field.textContent?.trim();
                                if (text && text.length > 1) {{
                                    // Try to split on common separators
                                    const parts = text.split(/[:\\-\\|]/);
                                    if (parts.length >= 2) {{
                                        const key = parts[0].trim();
                                        const value = parts.slice(1).join(':').trim();
                                        if (key && value) {{
                                            results.data[key] = value;
                                        }}
                                    }} else {{
                                        // Single value, use as key
                                        results.data[text] = text;
                                    }}
                                }}
                            }});
                        }}
                    }} else {{
                        // This is a simple section
                        results.sectionType = 'simple';
                        
                        // Extract simple text content
                        const textElements = sectionContainer.querySelectorAll('p, span, div, [class*="value"], [class*="Value"], [class*="text"], [class*="Text"], [class*="content"], [class*="Content"]');
                        const texts = [];
                        
                        textElements.forEach(el => {{
                            const text = el.textContent?.trim();
                            if (text && text.length > 1 && !text.includes(sectionName)) {{
                                texts.push(text);
                            }}
                        }});
                        
                        if (texts.length > 0) {{
                            results.data['value'] = texts.join(' ').trim();
                        }} else {{
                            // Fallback: use raw text content
                            const rawText = sectionContainer.textContent?.trim() || '';
                            if (rawText && !rawText.includes(sectionName)) {{
                                results.data['value'] = rawText;
                            }}
                        }}
                    }}
                    
                    return results;
                }}
            """)
            
            self.logger.info(f"    Section '{section_name}' parsing result: found={section_data['found']}, type={section_data['sectionType']}, data_keys={list(section_data['data'].keys())}")
            
            return section_data['data'] if section_data['found'] else {}
            
        except Exception as e:
            self.logger.error(f"    Error parsing section '{section_name}': {e}")
            return {}
    
    async def _extract_education_data(self) -> List[Dict[str, str]]:
        """Extract education data using text-based section parsing"""
        try:
            # Try multiple section names for education
            education_section_names = ["Education", "Educational Background", "Academic Background", "Degrees"]
            education_data = {}
            
            for section_name in education_section_names:
                education_data = await self._parse_section_by_text(section_name)
                if education_data:
                    self.logger.info(f"    Found education section: {section_name}")
                    break
            
            if not education_data:
                self.logger.info("    No education section found")
                return []
            
            # Convert the parsed data to the expected format
            education_list = []
            
            if 'value' in education_data:
                # Simple text format - try to parse it
                text = education_data['value']
                self.logger.info(f"    Education text content: {text[:200]}...")
                
                # Handle concatenated table data like "InstitutionDegreeSpecialtyUniversity of MassachusettsUndergraduateArts in Classics"
                import re
                
                # First try to split by common patterns
                if 'Institution' in text and 'Degree' in text and 'Specialty' in text:
                    # This looks like concatenated table data
                    # Try to find the actual data after the headers
                    data_start = text.find('University')  # Look for first university name
                    if data_start > 0:
                        data_text = text[data_start:]
                        # Try to split by capital letters that start new words
                        parts = re.split(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', data_text)
                        
                        # Look for university, degree, specialty pattern
                        university_idx = -1
                        degree_idx = -1
                        specialty_idx = -1
                        
                        for i, part in enumerate(parts):
                            if 'University' in part or 'College' in part:
                                university_idx = i
                            elif part in ['Undergraduate', 'Graduate', 'Bachelor', 'Master', 'PhD', 'Doctorate']:
                                degree_idx = i
                            elif i > degree_idx and degree_idx > 0:
                                specialty_idx = i
                                break
                        
                        if university_idx >= 0:
                            institution = ' '.join(parts[university_idx:degree_idx]) if degree_idx > university_idx else parts[university_idx]
                            degree = ' '.join(parts[degree_idx:specialty_idx]) if specialty_idx > degree_idx else (parts[degree_idx] if degree_idx >= 0 else 'Unknown')
                            specialty = ' '.join(parts[specialty_idx:]) if specialty_idx >= 0 else 'Unknown'
                            
                            education_list.append({
                                'institution': institution.strip(),
                                'degree': degree.strip(),
                                'specialty': specialty.strip()
                            })
                        else:
                            # Fallback: try to find university names
                            university_matches = re.findall(r'([A-Z][^.!?]*(?:University|College|Institute|School)[^.!?]*)', text, re.IGNORECASE)
                            for university in university_matches:
                                education_list.append({
                                    'institution': university.strip(),
                                    'degree': 'Unknown',
                                    'specialty': 'Unknown'
                                })
                    else:
                        # No university found, try other patterns
                        parts = re.split(r'\s*-\s*|\s*\|\s*', text)
                if len(parts) >= 2:
                    education_list.append({
                        'institution': parts[0].strip(),
                        'degree': parts[1].strip() if len(parts) > 1 else 'Unknown',
                        'specialty': parts[2].strip() if len(parts) > 2 else 'Unknown'
                    })
                else:
                    # Try other patterns like "University - Degree - Specialty"
                    parts = re.split(r'\s*-\s*|\s*\|\s*', text)
                    if len(parts) >= 2:
                        education_list.append({
                            'institution': parts[0].strip(),
                            'degree': parts[1].strip() if len(parts) > 1 else 'Unknown',
                            'specialty': parts[2].strip() if len(parts) > 2 else 'Unknown'
                        })
                    else:
                        # Try to find university/college names in the text
                        university_matches = re.findall(r'([A-Z][^.!?]*(?:University|College|Institute|School)[^.!?]*)', text, re.IGNORECASE)
                        for university in university_matches:
                            education_list.append({
                                'institution': university.strip(),
                                'degree': 'Unknown',
                                'specialty': 'Unknown'
                            })
            else:
                # Table format - convert to education list
                self.logger.info(f"    Education table data keys: {list(education_data.keys())}")
                
                # Filter out header rows and concatenated data
                filtered_data = {}
                for row_key, row_data in education_data.items():
                    # Skip header rows
                    if row_key.lower() in ['institution', 'degree', 'specialty']:
                        continue
                    # Skip concatenated data that contains all headers
                    if isinstance(row_data, str) and 'InstitutionDegreeSpecialty' in row_data:
                        continue
                    filtered_data[row_key] = row_data
                
                self.logger.info(f"    Filtered education data keys: {list(filtered_data.keys())}")
                
                # Try to find proper education records
                institution = None
                degree = None
                specialty = None
                
                for row_key, row_data in filtered_data.items():
                    if isinstance(row_data, dict):
                        # This is a proper row with structured data
                        institution = row_data.get('institution', row_data.get('Institution', row_data.get('column_1', '')))
                        degree = row_data.get('degree', row_data.get('Degree', row_data.get('column_2', '')))
                        specialty = row_data.get('specialty', row_data.get('Specialty', row_data.get('column_3', '')))
                        
                        if institution and institution.strip():
                            education_list.append({
                                'institution': institution.strip(),
                                'degree': degree.strip() if degree else 'Unknown',
                                'specialty': specialty.strip() if specialty else 'Unknown'
                            })
                    else:
                        # Handle string data - try to identify what type it is
                        text = str(row_data).strip()
                        if text and len(text) > 3:
                            # Check if this looks like an institution name
                            if any(word in text.lower() for word in ['university', 'college', 'institute', 'school']):
                                institution = text
                            elif text.lower() in ['undergraduate', 'graduate', 'bachelor', 'master', 'phd', 'doctorate']:
                                degree = text
                            elif text and not any(word in text.lower() for word in ['institution', 'degree', 'specialty']):
                                # This might be a specialty or degree
                                if not degree:
                                    degree = text
                                elif not specialty:
                                    specialty = text
                
                # If we found individual pieces, combine them
                if institution and (degree or specialty):
                    education_list.append({
                        'institution': institution.strip(),
                        'degree': degree.strip() if degree else 'Unknown',
                        'specialty': specialty.strip() if specialty else 'Unknown'
                    })
                elif not education_list:
                    # Fallback: add any substantial text as institution
                    for row_key, row_data in filtered_data.items():
                        if isinstance(row_data, str) and len(row_data.strip()) > 5:
                            education_list.append({
                                'institution': row_data.strip(),
                                'degree': 'Unknown',
                                'specialty': 'Unknown'
                            })
            
            self.logger.info(f"    Extracted {len(education_list)} education records")
            return education_list
            
        except Exception as e:
            self.logger.error(f"    Error extracting education data: {e}")
            return []
    
    async def _extract_licenses_data(self) -> List[Dict[str, str]]:
        """Extract licenses data using text-based section parsing"""
        try:
            licenses_data = await self._parse_section_by_text("License")
            
            if not licenses_data:
                return []
            
            licenses_list = []
            
            if 'value' in licenses_data:
                # Simple text format
                text = licenses_data['value']
                # Try to parse license information
                licenses_list.append({
                    'license': text,
                    'state': '',
                    'number': '',
                    'earned': ''
                })
            else:
                # Table format
                for row_key, row_data in licenses_data.items():
                    licenses_list.append({
                        'license': row_data.get('license', row_data.get('License', row_data.get('column_1', row_key))),
                        'state': row_data.get('state', row_data.get('State', row_data.get('column_2', ''))),
                        'number': row_data.get('number', row_data.get('Number', row_data.get('column_3', ''))),
                        'earned': row_data.get('earned', row_data.get('Earned', row_data.get('column_4', '')))
                    })
            
            return licenses_list
            
        except Exception as e:
            self.logger.error(f"    Error extracting licenses data: {e}")
            return []
    
    async def _extract_projects_data(self) -> Dict[str, Dict[str, str]]:
        """Extract projects data using text-based parsing and merge with detailed table data"""
        try:
            self.logger.info("    Extracting projects data using text-based parser...")
            
            # Try different section names for projects
            section_names = ["Projects", "Project", "Work", "Portfolio", "Experience"]
            projects_data = None
            section_found = None
            
            for section_name in section_names:
                projects_data = await self._parse_section_by_text(section_name)
                # Check if we got the structured result or raw data
                if projects_data and 'found' in projects_data:
                    # Structured result from _parse_section_by_text
                    found_value = projects_data.get('found')
                    self.logger.info(f"    Section '{section_name}': found={found_value}, type={projects_data.get('sectionType', 'none')}")
                    if found_value:
                        section_found = section_name
                        self.logger.info(f"    Breaking on section: {section_name}")
                        break
                elif projects_data and len(projects_data) > 0:
                    # Raw data - assume it's found if we have data
                    self.logger.info(f"    Section '{section_name}': found=True (raw data), keys={list(projects_data.keys())}")
                    section_found = section_name
                    self.logger.info(f"    Breaking on section: {section_name}")
                    break
                else:
                    self.logger.info(f"    Section '{section_name}': found=False")
            
            if not projects_data or (not projects_data.get('found') and len(projects_data) == 0):
                self.logger.info("    No projects section found")
                return {}
            
            self.logger.info(f"    Found projects section: {section_found}")
            
            # Extract projects from text-based parsing
            text_projects = await self._parse_text_based_projects(projects_data)
            
            # Note: Detailed table projects are handled separately in the main scraping flow
            # to avoid clicking the "Show All" button twice and changing page state
            
            # Add project links directly from the page
            project_links = await self.page.evaluate("""
                () => {
                    const projectLinks = [];
                    // Look for project links anywhere on the page (more robust)
                    const allLinks = document.querySelectorAll('a[href*="/project/"]');
                    allLinks.forEach(link => {
                        const href = link.getAttribute('href');
                        const text = link.textContent?.trim();
                        if (href && text && text.length > 3) {
                            projectLinks.push({
                                url: href.startsWith('http') ? href : 'https://ei.ennead.com' + href,
                                name: text,
                                project_number: href.split('/').pop() || ''
                            });
                        }
                    });
                    return projectLinks;
                }
            """)
            
            self.logger.info(f"    Found {len(project_links)} project links directly from page")
            
            # Try to match project links with existing projects
            for link in project_links:
                link_name = link.get('name', '')
                link_url = link.get('url', '')
                link_number = link.get('project_number', '')
                
                # Try to find a matching project in our dict
                matched = False
                for proj_key, proj_data in text_projects.items():
                    if self._are_projects_similar(proj_data['name'], link_name):
                        # Update with URL and number if we found a match
                        if not proj_data['url']:
                            proj_data['url'] = link_url
                        if not proj_data['number']:
                            proj_data['number'] = link_number
                        matched = True
                        break
                
                # If no match found, add as new project
                if not matched and link_name:
                    project_counter = len(text_projects) + 1
                    text_projects[f"proj_{project_counter}"] = {
                        'name': link_name,
                        'description': '',
                        'role': '',
                        'year': '',
                        'client': '',
                        'number': link_number,
                        'url': link_url,
                        'source': 'text_parsing'
                    }
            
            merged_projects = text_projects
            
            self.logger.info(f"    Extracted {len(merged_projects)} unique projects after merging and deduplication")
            return merged_projects
            
        except Exception as e:
            self.logger.error(f"    Error extracting projects data: {e}")
            return {}
    
    async def _parse_text_based_projects(self, projects_data):
        """Parse projects from text-based data"""
        projects_dict = {}
        
        if projects_data.get('type') == 'simple':
            # Simple text format - try to extract project names
            text_content = projects_data.get('value', '')
            if text_content:
                # Look for project names in the text
                import re
                # Simple regex to find potential project names (capitalized words)
                project_matches = re.findall(r'[A-Z][a-zA-Z\s&,.-]+(?:Project|Building|Center|Museum|School|University|Hospital|Library|Campus|Development|Design|Study|Plan|Master|Complex|Facility|Institute|Center|Office|Park|Tower|Hall|Theater|Theatre|Arena|Stadium|Gallery|Museum|Library|School|University|Hospital|Center|Building|Development|Design|Study|Plan|Master|Complex|Facility|Institute|Office|Park|Tower|Hall|Theater|Theatre|Arena|Stadium|Gallery)', text_content)
                
                for i, project_name in enumerate(project_matches, 1):
                    if len(project_name.strip()) > 5:  # Filter out very short matches
                        projects_dict[f"proj_{i}"] = {
                            'name': project_name.strip(),
                            'description': '',
                            'role': '',
                            'year': '',
                            'client': '',
                            'number': '',
                            'url': '',
                            'source': 'text_parsing'
                        }
        
        else:
            # Table format - convert to projects list
            self.logger.info(f"    Projects table data keys: {list(projects_data.keys())}")
            
            # Filter out header rows and concatenated data
            filtered_data = {}
            for row_key, row_data in projects_data.items():
                # Skip header rows
                if row_key.lower() in ['project', 'name', 'title', 'description', 'role', 'year', 'client', 'number', 'url']:
                    continue
                # Skip concatenated data that contains all headers
                if isinstance(row_data, str) and any(header in row_data for header in ['ProjectName', 'ProjectTitle', 'ProjectDescription']):
                    continue
                filtered_data[row_key] = row_data
            
            self.logger.info(f"    Filtered projects data keys: {list(filtered_data.keys())}")
            
            # Try to find proper project records
            project_counter = 1
            
            for row_key, row_data in filtered_data.items():
                if isinstance(row_data, dict):
                    # This is a proper row with structured data
                    project_name = row_data.get('project', row_data.get('name', row_data.get('title', row_data.get('column_1', ''))))
                    project_description = row_data.get('description', row_data.get('column_2', ''))
                    project_role = row_data.get('role', row_data.get('column_3', ''))
                    project_year = row_data.get('year', row_data.get('column_4', ''))
                    project_client = row_data.get('client', row_data.get('column_5', ''))
                    project_number = row_data.get('number', row_data.get('column_6', ''))
                    project_url = row_data.get('url', row_data.get('column_7', ''))
                    
                    if project_name and project_name.strip():
                        projects_dict[f"proj_{project_counter}"] = {
                            'name': project_name.strip(),
                            'description': project_description.strip() if project_description else '',
                            'role': project_role.strip() if project_role else '',
                            'year': project_year.strip() if project_year else '',
                            'client': project_client.strip() if project_client else '',
                            'number': project_number.strip() if project_number else '',
                            'url': project_url.strip() if project_url else '',
                            'source': 'text_parsing'
                        }
                        project_counter += 1
                else:
                    # Handle string data - try to identify what type it is
                    text = str(row_data).strip()
                    if text and len(text) > 3:
                        # Check if this looks like a project name (not just a number)
                        if not text.isdigit() and not text.startswith('proj_'):
                            # Clean up concatenated project names
                            cleaned_name = self._clean_project_name(text)
                            
                            projects_dict[f"proj_{project_counter}"] = {
                                'name': cleaned_name,
                                'description': '',
                                'role': '',
                                'year': '',
                                'client': '',
                                'number': '',
                                'url': '',
                                'source': 'text_parsing'
                            }
                            project_counter += 1
            
            # If we found individual pieces, combine them
            if not projects_dict:
                # Fallback: add any substantial text as project name
                for row_key, row_data in filtered_data.items():
                    if isinstance(row_data, str) and len(row_data.strip()) > 5:
                        projects_dict[f"proj_{project_counter}"] = {
                            'name': row_data.strip(),
                            'description': '',
                            'role': '',
                            'year': '',
                            'client': '',
                            'number': '',
                            'url': '',
                            'source': 'text_parsing'
                        }
                        project_counter += 1
        
        return projects_dict
    
    async def _extract_detailed_table_projects(self):
        """Extract projects from detailed table (Show All page)"""
        try:
            # Look for 'Show All' button and click it
            show_all_button = await self.page.query_selector('a:has-text("Show All")')
            if not show_all_button:
                self.logger.info("    No 'Show All' button found for detailed projects")
                return {}
            
            self.logger.info("    Found 'Show All' button, clicking to get detailed projects...")
            await show_all_button.click()
            
            # Wait for the detailed table to load
            try:
                await self.page.wait_for_selector('table, .project, .projects, .k-grid', timeout=10000)
                self.logger.info("    Detailed projects table loaded")
            except Exception as e:
                self.logger.warning(f"    Project table not found after clicking Show All: {e}")
                return {}
            
            # Extract projects from the detailed table
            detailed_projects = await self.page.evaluate("""
                () => {
                    const projects = [];
                    
                    // Look for various table structures
                    const tables = document.querySelectorAll('table, .k-grid, .project-grid, .projects-table');
                    
                    tables.forEach(table => {
                        const rows = table.querySelectorAll('tr, .project-row, .k-grid-row');
                        
                        rows.forEach((row, index) => {
                            // Skip header rows
                            if (index === 0) return;
                            
                            const cells = row.querySelectorAll('td, .project-cell, .k-grid-cell');
                            if (cells.length >= 2) {
                                const project = {
                                    name: cells[0]?.textContent?.trim() || '',
                                    description: cells[1]?.textContent?.trim() || '',
                                    role: cells[2]?.textContent?.trim() || '',
                                    year: cells[3]?.textContent?.trim() || '',
                                    client: cells[4]?.textContent?.trim() || '',
                                    number: cells[5]?.textContent?.trim() || '',
                                    url: ''
                                };
                                
                                // Try to find project link
                                const link = row.querySelector('a[href*="/project/"]');
                                if (link) {
                                    project.url = link.href;
                                    project.number = link.href.split('/').pop() || '';
                                }
                                
                                if (project.name && project.name.length > 3) {
                                    projects.push(project);
                                }
                            }
                        });
                    });
                    
                    return projects;
                }
            """)
            
            # Convert to projects dict
            projects_dict = {}
            for i, project in enumerate(detailed_projects, 1):
                if project.get('name'):
                    projects_dict[f"proj_{i}"] = {
                        'name': project['name'],
                        'description': project.get('description', ''),
                        'role': project.get('role', ''),
                        'year': project.get('year', ''),
                        'client': project.get('client', ''),
                        'number': project.get('number', ''),
                        'url': project.get('url', ''),
                        'source': 'detailed_table'
                    }
            
            self.logger.info(f"    Found {len(projects_dict)} projects from detailed table")
            return projects_dict
            
        except Exception as e:
            self.logger.error(f"    Error extracting detailed table projects: {e}")
            return {}
    
    def _clean_project_name(self, text):
        """Clean up concatenated project names"""
        cleaned_name = text
        
        # Remove common suffixes that might be concatenated
        for suffix in ['Project', 'Building', 'Center', 'Museum', 'School', 'University', 'Hospital', 'Library', 'Campus', 'Development', 'Design', 'Study', 'Plan', 'Master', 'Complex', 'Facility', 'Institute', 'Office', 'Park', 'Tower', 'Hall', 'Theater', 'Theatre', 'Arena', 'Stadium', 'Gallery']:
            if text.endswith(suffix + suffix):
                cleaned_name = text.replace(suffix + suffix, suffix)
                break
        
        # Remove client names that might be concatenated
        # Look for patterns like "Project NameClient Name" or "Project NameClient"
        import re
        # Pattern to find where project name ends and client name begins
        pattern = r'([A-Z][a-zA-Z\s&,.-]+?)([A-Z][a-zA-Z\s&,.-]+?)(?:\d+|$)'
        match = re.search(pattern, cleaned_name)
        if match and len(match.group(1)) > 10:  # First group is likely the project name
            cleaned_name = match.group(1).strip()
        
        return cleaned_name
    
    async def _merge_and_deduplicate_projects(self, text_projects, detailed_projects):
        """Merge text-based and detailed table projects, removing duplicates"""
        merged_projects = {}
        project_counter = 1
        
        # First, add all text-based projects
        for proj_key, proj_data in text_projects.items():
            merged_projects[f"proj_{project_counter}"] = proj_data
            project_counter += 1
        
        # Then add detailed table projects, checking for duplicates
        for proj_key, proj_data in detailed_projects.items():
            # Check if this project already exists (by name similarity)
            is_duplicate = False
            for existing_key, existing_data in merged_projects.items():
                if self._are_projects_similar(proj_data['name'], existing_data['name']):
                    # Update existing project with more complete data
                    if not existing_data['url'] and proj_data['url']:
                        existing_data['url'] = proj_data['url']
                    if not existing_data['number'] and proj_data['number']:
                        existing_data['number'] = proj_data['number']
                    if not existing_data['description'] and proj_data['description']:
                        existing_data['description'] = proj_data['description']
                    if not existing_data['role'] and proj_data['role']:
                        existing_data['role'] = proj_data['role']
                    if not existing_data['year'] and proj_data['year']:
                        existing_data['year'] = proj_data['year']
                    if not existing_data['client'] and proj_data['client']:
                        existing_data['client'] = proj_data['client']
                    existing_data['source'] = 'merged'
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged_projects[f"proj_{project_counter}"] = proj_data
                project_counter += 1
        
        # Also try to get project links directly from the page
        project_links = await self.page.evaluate("""
            () => {
                const projectLinks = [];
                // Look for project links anywhere on the page (more robust)
                const allLinks = document.querySelectorAll('a[href*="/project/"]');
                allLinks.forEach(link => {
                    const href = link.getAttribute('href');
                    const text = link.textContent?.trim();
                    if (href && text && text.length > 3) {
                        projectLinks.push({
                            url: href.startsWith('http') ? href : 'https://ei.ennead.com' + href,
                            name: text,
                            project_number: href.split('/').pop() || ''
                        });
                    }
                });
                return projectLinks;
            }
        """)
        
        self.logger.info(f"    Found {len(project_links)} project links directly from page")
        
        # Try to match project links with existing projects
        for link in project_links:
            link_name = link.get('name', '')
            link_url = link.get('url', '')
            link_number = link.get('project_number', '')
            
            # Try to find a matching project in our dict
            matched = False
            for proj_key, proj_data in merged_projects.items():
                if self._are_projects_similar(proj_data['name'], link_name):
                    # Update with URL and number if we found a match
                    if not proj_data['url']:
                        proj_data['url'] = link_url
                    if not proj_data['number']:
                        proj_data['number'] = link_number
                    matched = True
                    break
            
            # If no match found, add as new project
            if not matched and link_name:
                merged_projects[f"proj_{project_counter}"] = {
                    'name': link_name,
                    'description': '',
                    'role': '',
                    'year': '',
                    'client': '',
                    'number': link_number,
                    'url': link_url,
                    'source': 'text_parsing'
                }
                project_counter += 1
        
        return merged_projects
    
    def _are_projects_similar(self, name1, name2):
        """Check if two project names are similar (to detect duplicates)"""
        if not name1 or not name2:
            return False
        
        # Normalize names for comparison
        norm1 = name1.lower().strip()
        norm2 = name2.lower().strip()
        
        # Exact match
        if norm1 == norm2:
            return True
        
        # One name contains the other
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        # Check for significant word overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        # Remove common words that don't help with matching
        common_words = {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'project', 'building', 'center', 'museum', 'school', 'university', 'hospital', 'library', 'campus', 'development', 'design', 'study', 'plan', 'master', 'complex', 'facility', 'institute', 'office', 'park', 'tower', 'hall', 'theater', 'theatre', 'arena', 'stadium', 'gallery'}
        
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        if not words1 or not words2:
            return False
        
        # Calculate overlap
        overlap = len(words1.intersection(words2))
        total_words = len(words1.union(words2))
        
        # If more than 50% of words overlap, consider them similar
        return overlap / total_words > 0.5
    
    async def _extract_section_data(self, section_name: str, field_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Extract data from any section using text-based parsing.
        
        Args:
            section_name: The section header text to look for
            field_mapping: Optional mapping of field names (e.g., {'column_1': 'institution', 'column_2': 'degree'})
            
        Returns:
            Dict containing the parsed data
        """
        try:
            section_data = await self._parse_section_by_text(section_name)
            
            if not section_data:
                return {}
            
            # Apply field mapping if provided
            if field_mapping and 'value' not in section_data:
                mapped_data = {}
                for row_key, row_data in section_data.items():
                    mapped_row = {}
                    for old_key, new_key in field_mapping.items():
                        if old_key in row_data:
                            mapped_row[new_key] = row_data[old_key]
                        else:
                            # Try case variations
                            for key in row_data.keys():
                                if key.lower() == old_key.lower():
                                    mapped_row[new_key] = row_data[key]
                                    break
                    if mapped_row:
                        mapped_data[row_key] = mapped_row
                    else:
                        mapped_data[row_key] = row_data
                return mapped_data
            
            return section_data
            
        except Exception as e:
            self.logger.error(f"    Error extracting section '{section_name}': {e}")
            return {}

    def get_scraper_info(self) -> Dict[str, Any]:
        """Get information about the scraper configuration"""
        return {
            'comprehensive_mode': True,
            'download_images': self.download_images,
            'headless': self.headless,
            'timeout': self.timeout,
            'base_url': self.base_url
        }
