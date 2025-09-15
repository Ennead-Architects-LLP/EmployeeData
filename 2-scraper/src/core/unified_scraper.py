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
        
        # Scraped data
        self.employees: List[EmployeeData] = []
        
        # Selectors for comprehensive data extraction
        self.selectors = {
            'employee_cards': '.gridViewCell, .ActivityBox-sc-ik8ilm-0, .gridViewStyles__Cell-sc-ipm8x5-2',
            'profile_image': '.gridViewStyles__Img-sc-ipm8x5-8, .gridViewStyles__ImgBox-sc-ipm8x5-4 img',
            'employee_name': '.gridViewStyles__Field-sc-ipm8x5-22.csVUxd.field.bold a, .gridViewStyles__Field-sc-ipm8x5-22.bold a',
            'employee_title': '.gridViewStyles__Field-sc-ipm8x5-22.eVXxsE.field',
            'profile_link': 'a[href*="/employee/"]',
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
            
            # Apply debug limit if in debug mode
            if hasattr(self.config, 'DEBUG_MODE') and self.config.DEBUG_MODE:
                max_employees = getattr(self.config, 'DEBUG_MAX_EMPLOYEES', 10)
                employee_links = employee_links[:max_employees]
                self.logger.info(f"[DEBUG] Limited to {max_employees} employees for debugging")
            
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
                    
                    // Position and department - look for specific profile page elements
                    data.position = document.querySelector('.position, .title, .job-title, .role')?.textContent?.trim() || '';
                    data.department = document.querySelector('.department, .team, .division, .group')?.textContent?.trim() || '';
                    
                    // Bio - be more specific to avoid capturing page content
                    const bioEl = document.querySelector('.bio-content, .about-content, .description-content, .employee-bio-content, [data-bio]');
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
                office_location=self._normalize_office_location(employee_data.get('office_location', '')),
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
            
            # Extract comprehensive data
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
                    data.seat_assignment = document.querySelector('.seat, .desk, .location')?.textContent?.trim() || '';
                    
                    // Computer information - be more specific to avoid capturing page content
                    const computerEl = document.querySelector('.computer-info, .machine-info, .device-info, [data-computer]');
                    data.computer = computerEl ? computerEl.textContent?.trim() : null;
                    
                    // Professional memberships
                    data.memberships = [];
                    const membershipElements = document.querySelectorAll('.membership, .association, .organization');
                    membershipElements.forEach(el => {
                        const text = el.textContent?.trim();
                        if (text) data.memberships.push(text);
                    });
                    
                    // Education - find education section using the actual HTML structure
                    data.education = [];
                    const allH1s = document.querySelectorAll('h1.commonStyledComponents_BlockTitle');
                    let educationSection = null;
                    for (let h1 of allH1s) {
                        if (h1.textContent?.trim() === 'Education') {
                            // Find the parent container with EntityFields class
                            educationSection = h1.closest('.EntityFields');
                            break;
                        }
                    }
                    
                    if (educationSection) {
                        // Look for education data in the EntityFields_InfoFieldValue divs
                        const educationItems = educationSection.querySelectorAll('[data-kafieldname], .EntityFields_InfoFieldValue');
                        educationItems.forEach(item => {
                            const text = item.textContent?.trim();
                            if (text && (text.includes('University') || text.includes('College') || text.includes('Institute'))) {
                                // Handle the concatenated text format: "InstitutionDegreeSpecialtyUniversity of MassachusettsUndergraduateArts in Classics"
                                if (text.includes('InstitutionDegreeSpecialty')) {
                                    // Split by the pattern and extract the actual data
                                    const parts = text.split('InstitutionDegreeSpecialty');
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
                                                'specialty': specialty
                                            });
                                        }
                                    }
                                } else {
                                    // Handle normal format
                                    const institutionMatch = text.match(/([A-Za-z\\s&]+University|[A-Za-z\\s&]+College|[A-Za-z\\s&]+Institute)/);
                                    const degreeMatch = text.match(/(Undergraduate|Graduate|Bachelor|Master|PhD|Doctorate|Associate)/i);
                                    if (institutionMatch) {
                                        data.education.push({
                                            'institution': institutionMatch[1].trim(),
                                            'degree': degreeMatch ? degreeMatch[1].trim() : 'Unknown',
                                            'specialty': text.replace(institutionMatch[1], '').replace(degreeMatch ? degreeMatch[1] : '', '').trim()
                                        });
                                    }
                                }
                            }
                        });
                    }
                    
                    // Licenses and registrations - find licenses section using the actual HTML structure
                    data.licenses = [];
                    const allH1sForLicenses = document.querySelectorAll('h1.commonStyledComponents_BlockTitle');
                    let licensesSection = null;
                    for (let h1 of allH1sForLicenses) {
                        if (h1.textContent?.trim().includes('License')) {
                            // Find the parent container with EntityFields class
                            licensesSection = h1.closest('.EntityFields');
                            break;
                        }
                    }
                    
                    if (licensesSection) {
                        // Look for license data in the EntityFields_InfoFieldValue divs
                        const licenseItems = licensesSection.querySelectorAll('[data-kafieldname], .EntityFields_InfoFieldValue');
                        licenseItems.forEach(item => {
                            const text = item.textContent?.trim();
                            if (text && text.length > 3 && !text.includes('License') && !text.includes('State') && !text.includes('Number')) {
                                data.licenses.push({
                                    'name': text,
                                    'number': '',
                                    'state': '',
                                    'expiry': ''
                                });
                            }
                        });
                    }
                    
                    // Projects - look for project links and related elements
                    data.projects = [];
                    const projectElements = document.querySelectorAll('a[href*="/project/"], .project-item, .work-item, .portfolio-item, [data-project]');
                    projectElements.forEach(el => {
                        const link = el.querySelector('a[href*="/project/"]') || el;
                        const href = link.href || '';
                        const name = el.querySelector('.name, .title, .project-name, h3, h4')?.textContent?.trim() || 
                                    link.textContent?.trim() || '';
                        const description = el.querySelector('.description, .summary, .project-description')?.textContent?.trim() || '';
                        const role = el.querySelector('.role, .position, .project-role')?.textContent?.trim() || '';
                        const year = el.querySelector('.year, .date, .project-year')?.textContent?.trim() || '';
                        const client = el.querySelector('.client, .project-client')?.textContent?.trim() || '';
                        const number = el.querySelector('.number, .project-number')?.textContent?.trim() || '';
                        
                        if (name && href.includes('/project/')) {
                            data.projects.push({
                                'name': name,
                                'description': description,
                                'role': role,
                                'year': year,
                                'client': client,
                                'number': number,
                                'url': href
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
            
            # Capture preview image if enabled (avoid auth issues with full-resolution downloads)
            if self.download_images and self.image_downloader:
                try:
                    local_path = await self.image_downloader.capture_preview_image(
                        self.page, 
                        name,
                        image_selector='img[src*="/api/image/"]:not([src*="favicon"]):not([src*="logo"]):not([src*="icon"])'
                    )
                    if local_path:
                        employee.image_local_path = local_path
                except Exception as e:
                    self.logger.warning(f"Failed to capture preview image for {name}: {e}")
            
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
