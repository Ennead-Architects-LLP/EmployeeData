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
                        
                        # Save individual JSON file immediately
                        saved_path = await self._save_individual_employee(employee)
                        
                        if saved_path:
                            print(f"✅ SUCCESS: {name} - JSON saved to {saved_path}")
                        else:
                            print(f"⚠️ WARNING: {name} - Failed to save JSON")
                        
                        self.logger.info(f"[SUCCESS] Successfully scraped and saved {name}")
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
    
    async def _scrape_employee_basic(self, profile_url: str, name: str, image_url: str) -> Optional[EmployeeData]:
        """Scrape basic employee data"""
        try:
            if self.page.url != profile_url:
                await self.page.goto(profile_url)
                await self.page.wait_for_load_state('networkidle')
            
            # Extract basic data
            employee_data = await self.page.evaluate(f"""
                () => {{
                    const data = {{}};
                    
                    // Basic information - use more specific selectors for employee name
                    data.human_name = document.querySelector('h1[class*="EntityHeader"], .EntityHeader h1, h1:not([class*="section"])')?.textContent?.trim() || 
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
            
            # Create EmployeeData object
            employee = EmployeeData(
                human_name=employee_data.get('human_name') or name,
                email=employee_data.get('email'),
                phone=employee_data.get('phone'),
                position=employee_data.get('position'),
                department=employee_data.get('department'),
                bio=employee_data.get('bio'),
                office_location=employee_data.get('office_location', ''),
                profile_url=profile_url,
                image_url=employee_data.get('image_url') or image_url
            )
            
            # Note: Image capture is handled in the comprehensive method
            
            return employee
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error scraping profile {profile_url}: {e}")
            return None
    
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
            
            # Capture DOM for debugging individual profile pages
            if hasattr(self, 'config') and self.config.DEBUG_MODE:
                await self._capture_debug_info(f"profile_page_{name.replace(' ', '_')}")
            
            # Debug: Check what name is being extracted
            debug_name = await self.page.evaluate("""
                () => {
                    const h1 = document.querySelector('h1');
                    const entityHeader = document.querySelector('h1[class*="EntityHeader"]');
                    const allH1s = document.querySelectorAll('h1');
                    return {
                        firstH1: h1?.textContent?.trim() || 'none',
                        entityHeader: entityHeader?.textContent?.trim() || 'none',
                        allH1s: Array.from(allH1s).map(h => h.textContent?.trim()).filter(t => t)
                    };
                }
            """)
            self.logger.info(f"    Debug name extraction: {debug_name}")
            
            # Start with basic data
            employee = await self._scrape_employee_basic(profile_url, name, image_url)
            if not employee:
                return None
            
            # Override the human_name with the name from the directory (more reliable)
            if name and name.strip():
                employee.human_name = name.strip()
                self.logger.info(f"    Using directory name: {name}")
            
            # Wait for the page content to load (education section specifically)
            try:
                await self.page.wait_for_selector('[data-kagridname="employeeDegrees"]', timeout=10000)
                self.logger.info("    Education section loaded")
            except Exception as e:
                self.logger.info(f"    Education section not found or timeout: {e}")
                # Try waiting for any education-related element
                try:
                    await self.page.wait_for_selector('h1:has-text("Education")', timeout=5000)
                    self.logger.info("    Education H1 found")
                except:
                    self.logger.info("    No education section found")
            
            # Extract comprehensive data
            self.logger.info("    Starting comprehensive data extraction...")
            comprehensive_data = await self.page.evaluate("""
                () => {
                    const data = {};
                    
                    // Additional contact methods
                    data.mobile = document.querySelector('a[href^="tel:"]')?.href?.replace('tel:', '') || '';
                    data.teams_url = document.querySelector('a[href*="teams.microsoft.com"]')?.href || '';
                    data.linkedin_url = document.querySelector('a[href*="linkedin.com"]')?.href || '';
                    data.website_url = document.querySelector('a[href*="http"]:not([href*="ennead.com"])')?.href || '';
                    
                    // Years with firm - look for specific patterns in the text content
                    const pageText = document.body.textContent || '';
                    const yearsMatch = pageText.match(/Years With Firm\\s*(\\d+)/i);
                    data.years_with_firm = yearsMatch ? parseInt(yearsMatch[1]) : null;
                    
                    // Seating assignment
                    
                    
                    // Professional memberships
                    data.memberships = [];
                    const membershipElements = document.querySelectorAll('.membership, .association, .organization');
                    membershipElements.forEach(el => {
                        const text = el.textContent?.trim();
                        if (text) data.memberships.push(text);
                    });
                    
                    // Education - use the correct selectors based on actual HTML structure
                    data.education = [];
                    
                    
                    // Find the education section using the data-kagridname attribute
                    const educationContainer = document.querySelector('[data-kagridname="employeeDegrees"]');
                    
                    if (educationContainer) {
                        // Try multiple approaches to find education data
                        
                        // Approach 1: Try the old working selectors with various class name patterns
                        const possibleSelectors = [
                            '.EntityFields__InfoFieldValue-sc-129sxys-5',
                            '.EntityFields_InfoFieldValue',
                            '[class*="InfoFieldValue"]',
                            '[class*="EntityFields"] [class*="Value"]',
                            'div[data-kafieldname*="institution"]',
                            'div[data-kafieldname*="degree"]',
                            'div[data-kafieldname*="specialty"]'
                        ];
                        
                        let educationRows = [];
                        let workingSelector = '';
                        
                        for (const selector of possibleSelectors) {
                            educationRows = educationContainer.querySelectorAll(selector);
                            if (educationRows.length > 0) {
                                workingSelector = selector;
                                break;
                            }
                        }
                        
                        
                        if (educationRows.length > 0) {
                            // Group by rows of 3 (institution, degree, specialty) - same as old scraper
                            for (let i = 0; i < educationRows.length; i += 3) {
                                if (i + 2 < educationRows.length) {
                                    const institution = educationRows[i].textContent?.trim() || '';
                                    const degree = educationRows[i + 1].textContent?.trim() || '';
                                    const specialty = educationRows[i + 2].textContent?.trim() || '';
                                    
                                    if (institution) {
                            data.education.push({
                                            'institution': institution,
                                            'degree': degree || 'Unknown',
                                            'specialty': specialty || 'Unknown'
                                        });
                                    }
                                }
                            }
                        } else {
                            // Approach 2: Try data-kafieldname selectors (like the old scraper)
                            const institutionEl = educationContainer.querySelector('[data-kafieldname="employeeDegrees|institution"]');
                            const degreeEl = educationContainer.querySelector('[data-kafieldname="employeeDegrees|degree"]');
                            const specialtyEl = educationContainer.querySelector('[data-kafieldname="employeeDegrees|specialty"]');
                            
                            
                            if (institutionEl && degreeEl && specialtyEl) {
                                const institution = institutionEl.textContent?.trim() || '';
                                const degree = degreeEl.textContent?.trim() || '';
                                const specialty = specialtyEl.textContent?.trim() || '';
                                
                                if (institution) {
                                    data.education.push({
                                        'institution': institution,
                                        'degree': degree || 'Unknown',
                                        'specialty': specialty || 'Unknown'
                                    });
                                }
                            } else {
                                // Approach 3: Fallback - parse the concatenated text directly from the container
                                const containerText = educationContainer.textContent?.trim() || '';
                                
                                // Parse the concatenated format: "InstitutionDegreeSpecialtyUniversity of MassachusettsUndergraduateArts in Classics/Minor in Arabic Studies"
                                if (containerText.includes('InstitutionDegreeSpecialty')) {
                                    const parts = containerText.split('InstitutionDegreeSpecialty');
                                    if (parts.length > 1) {
                                        const educationText = parts[1];
                                        
                                        // Look for University/College/Institute followed by degree
                                        const institutionMatch = educationText.match(/([A-Za-z\\s&]+University|[A-Za-z\\s&]+College|[A-Za-z\\s&]+Institute)/);
                                        const degreeMatch = educationText.match(/(Undergraduate|Graduate|Bachelor|Master|PhD|Doctorate|Associate)/i);
                                        
                                        if (institutionMatch) {
                                            const specialty = educationText.replace(institutionMatch[1], '').replace(degreeMatch ? degreeMatch[1] : '', '').trim();
                                            data.education.push({
                                                'institution': institutionMatch[1].trim(),
                                                'degree': degreeMatch ? degreeMatch[1].trim() : 'Unknown',
                                                'specialty': specialty || 'Unknown'
                                            });
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        // Fallback: look for any education-related elements
                        const educationH1 = document.querySelector('h1:has-text("Education")');
                        if (educationH1) {
                            const parentSection = educationH1.closest('.EntityFields');
                        }
                    }
                    
                    // Licenses and registrations - handle multiple employeeRegistrations|stateRegistered classes
                    data.licenses = [];
                    
                    // Look for all license containers using multiple selectors
                    const licenseContainers = document.querySelectorAll('[data-kagridname="employeeRegistrations"], [data-kagridname="stateRegistered"], .employeeRegistrations, .stateRegistered');
                    
                    licenseContainers.forEach((container, containerIndex) => {
                        // Try multiple approaches to extract license data
                        const approaches = [
                            // Approach 1: Look for field value elements and group by rows of 4
                            () => {
                                const licenseRows = container.querySelectorAll('.EntityFields__InfoFieldValue-sc-129sxys-5, .EntityFields_InfoFieldValue, [class*="InfoFieldValue"]');
                                const licenses = [];
                                for (let i = 0; i < licenseRows.length; i += 4) {
                                    if (i + 3 < licenseRows.length) {
                                        const licenseName = licenseRows[i].textContent?.trim() || '';
                                        const state = licenseRows[i + 1].textContent?.trim() || '';
                                        const number = licenseRows[i + 2].textContent?.trim() || '';
                                        const earned = licenseRows[i + 3].textContent?.trim() || '';
                                        
                                        if (licenseName) {
                                            licenses.push({
                                                'license': licenseName,
                                                'state': state || '',
                                                'number': number || '',
                                                'earned': earned || '',
                                                'source': `container_${containerIndex + 1}_approach_1`
                                            });
                                        }
                                    }
                                }
                                return licenses;
                            },
                            // Approach 2: Look for data-kafieldname attributes
                            () => {
                                const licenses = [];
                                const licenseFields = container.querySelectorAll('[data-kafieldname*="license"], [data-kafieldname*="registration"], [data-kafieldname*="state"]');
                                const fieldGroups = {};
                                
                                licenseFields.forEach(field => {
                                    const fieldName = field.getAttribute('data-kafieldname') || '';
                                    const fieldValue = field.textContent?.trim() || '';
                                    
                                    if (fieldValue) {
                                        // Group fields by their row index or parent
                                        const rowKey = field.closest('tr, .row, [class*="Row"]')?.textContent || 'default';
                                        if (!fieldGroups[rowKey]) {
                                            fieldGroups[rowKey] = {};
                                        }
                                        
                                        if (fieldName.includes('license') || fieldName.includes('registration')) {
                                            fieldGroups[rowKey].license = fieldValue;
                                        } else if (fieldName.includes('state')) {
                                            fieldGroups[rowKey].state = fieldValue;
                                        } else if (fieldName.includes('number')) {
                                            fieldGroups[rowKey].number = fieldValue;
                                        } else if (fieldName.includes('earned') || fieldName.includes('date')) {
                                            fieldGroups[rowKey].earned = fieldValue;
                                        }
                                    }
                                });
                                
                                Object.values(fieldGroups).forEach(license => {
                                    if (license.license) {
                                        licenses.push({
                                            'license': license.license,
                                            'state': license.state || '',
                                            'number': license.number || '',
                                            'earned': license.earned || '',
                                            'source': `container_${containerIndex + 1}_approach_2`
                                        });
                                    }
                                });
                                
                                return licenses;
                            },
                            // Approach 3: Look for table rows or grid items
                            () => {
                                const licenses = [];
                                const rows = container.querySelectorAll('tr, .row, [class*="Row"], [class*="GridItem"]');
                                
                                rows.forEach(row => {
                                    const cells = row.querySelectorAll('td, .cell, [class*="Cell"], [class*="Field"]');
                                    if (cells.length >= 2) {
                                        const licenseName = cells[0]?.textContent?.trim() || '';
                                        const state = cells[1]?.textContent?.trim() || '';
                                        const number = cells[2]?.textContent?.trim() || '';
                                        const earned = cells[3]?.textContent?.trim() || '';
                                        
                                        if (licenseName && licenseName.length > 1) {
                                            licenses.push({
                                                'license': licenseName,
                                                'state': state || '',
                                                'number': number || '',
                                                'earned': earned || '',
                                                'source': `container_${containerIndex + 1}_approach_3`
                                            });
                                        }
                                    }
                                });
                                
                                return licenses;
                            }
                        ];
                        
                        // Try each approach and collect results
                        approaches.forEach((approach, approachIndex) => {
                            try {
                                const approachLicenses = approach();
                                if (approachLicenses.length > 0) {
                                    data.licenses.push(...approachLicenses);
                                }
                            } catch (e) {
                                console.log(`Approach ${approachIndex + 1} failed for container ${containerIndex + 1}:`, e);
                            }
                        });
                    });
                    
                    // Remove duplicates based on license name and state
                    const uniqueLicenses = [];
                    const seen = new Set();
                    
                    data.licenses.forEach(license => {
                        const key = `${license.license}_${license.state}`.toLowerCase();
                        if (!seen.has(key)) {
                            seen.add(key);
                            uniqueLicenses.push(license);
                        }
                    });
                    
                    data.licenses = uniqueLicenses;
                    
                    // Fallback: look for any section with "License" in the title
                    if (data.licenses.length === 0) {
                        const allH1sForLicenses = document.querySelectorAll('h1.commonStyledComponents_BlockTitle');
                        let licensesSection = null;
                        for (let h1 of allH1sForLicenses) {
                            if (h1.textContent?.trim().includes('License')) {
                                licensesSection = h1.closest('.EntityFields');
                                break;
                            }
                        }
                        
                        if (licensesSection) {
                            const licenseItems = licensesSection.querySelectorAll('.EntityFields_InfoFieldValue');
                            licenseItems.forEach(item => {
                                const text = item.textContent?.trim();
                                if (text && text.length > 3 && !text.includes('License') && !text.includes('State') && !text.includes('Number')) {
                            data.licenses.push({
                                        'license': text,
                                        'state': '',
                                        'number': '',
                                        'earned': ''
                            });
                        }
                    });
                        }
                    }
                    
                    // Projects - extract from both locations as dictionary
                    data.projects = {};
                    
                    // Place 1: Direct project links under gridViewStyles__Field-sc-ipm8x5-22 bmVZMs field bold
                    const directProjectElements = document.querySelectorAll('.gridViewStyles__Field-sc-ipm8x5-22.bmVZMs.field.bold a[href*="/project/"]');
                    directProjectElements.forEach(el => {
                        const name = el.textContent?.trim();
                        const url = el.href;
                        if (name && url && name.length > 1) {
                            const projectKey = `proj_${Object.keys(data.projects).length + 1}`;
                            data.projects[projectKey] = {
                                'name': name,
                                'description': '',
                                'role': '',
                                'year': '',
                                'client': '',
                                'number': '',
                                'url': url,
                                'source': 'direct'
                            };
                        }
                    });
                    
                    // Place 2: Check for "Show All" button and navigate to detailed project table
                    const showAllButton = document.querySelector('.RoundedBox-sc-1nzfcbz-0.PillBox-sc-p125c4-0.fQdvmA.driLso.pill');
                    if (showAllButton && showAllButton.textContent?.trim().includes('Show All')) {
                        // Note: We'll handle the navigation to detailed project page in Python
                        // For now, just mark that we found the Show All button
                    }
                    
                    // Fallback: Look for other project links
                    const fallbackProjectElements = document.querySelectorAll('a[href*="/project/"]:not(.gridViewStyles__Field-sc-ipm8x5-22.bmVZMs.field.bold a)');
                    fallbackProjectElements.forEach(el => {
                        const name = el.textContent?.trim();
                        const url = el.href;
                        if (name && url && name.length > 1) {
                            // Check if we already have this project by URL
                            const existingProject = Object.values(data.projects).find(p => p.url === url);
                            if (!existingProject) {
                                const projectKey = `proj_${Object.keys(data.projects).length + 1}`;
                                data.projects[projectKey] = {
                                    'name': name,
                                    'description': '',
                                    'role': '',
                                    'year': '',
                                    'client': '',
                                    'number': '',
                                    'url': url,
                                    'source': 'fallback'
                                };
                            }
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
            
            self.logger.info(f"    Comprehensive data extracted: {len(comprehensive_data)} fields")
            self.logger.info(f"    Education debug fields: {[k for k in comprehensive_data.keys() if 'debug' in k]}")
            
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
            
            
            # Handle "Show All" projects button if found
            show_all_button = await self.page.query_selector('.RoundedBox-sc-1nzfcbz-0.PillBox-sc-p125c4-0.fQdvmA.driLso.pill')
            if show_all_button and await show_all_button.text_content() and 'Show All' in await show_all_button.text_content():
                try:
                    self.logger.info(f"    Found 'Show All' projects button for {name}, navigating to detailed project table...")
                    
                    # Click the "Show All" button
                    show_all_button = await self.page.query_selector('.RoundedBox-sc-1nzfcbz-0.PillBox-sc-p125c4-0.fQdvmA.driLso.pill')
                    if show_all_button:
                        await show_all_button.click()
                        # Prefer a targeted wait to reduce full page flashes
                        await self.page.wait_for_selector('table, .project, .projects, .k-grid', state='visible', timeout=5000)
                        
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
        """Scroll down to load all employees via infinite scroll"""
        try:
            previous_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 20  # Prevent infinite scrolling
            
            while scroll_attempts < max_scroll_attempts:
                # Count current employees
                current_count = await self.page.evaluate(f"""
                    () => {{
                        return document.querySelectorAll('{self.selectors['employee_cards']}').length;
                    }}
                """)
                
                self.logger.info(f"[INFO] Found {current_count} employees so far...")
                
                # If no new employees loaded, we're done
                if current_count == previous_count and scroll_attempts > 0:
                    self.logger.info(f"[INFO] No new employees loaded after scroll. Total: {current_count}")
                    break
                
                # Scroll to bottom
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Wait for new content to load
                await asyncio.sleep(2)
                await self.page.wait_for_load_state("networkidle", timeout=10000)
                
                previous_count = current_count
                scroll_attempts += 1
            
            self.logger.info(f"[SUCCESS] Finished scrolling. Total employees found: {previous_count}")
            
        except Exception as e:
            self.logger.warning(f"[WARNING] Error during scrolling: {e}")
            # Continue anyway - we'll work with whatever employees we found
    
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
