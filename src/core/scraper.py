"""
Main employee scraper using Playwright for the Ennead website.
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


class EmployeeScraper:
    """
    Main scraper class for extracting employee data from Ennead website.
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
        
        # Selectors (these may need to be updated based on actual page structure)
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
        """Async context manager entry."""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()
    
    async def start_browser(self):
        """Start the browser and create a new page."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                channel='msedge',  # Use Edge instead of Chrome
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            
            self.logger.info("Browser started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start browser: {str(e)}")
            raise
    
    async def close_browser(self):
        """Close the browser and cleanup resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            
            self.logger.info("Browser closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing browser: {str(e)}")
    
    async def navigate_to_employee_page(self) -> bool:
        """
        Navigate to the main employee directory page.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Navigating to: {self.base_url}")
            await self.page.goto(self.base_url, wait_until='networkidle')
            
            # Check if we were redirected to a login page
            current_url = self.page.url
            if 'login' in current_url.lower() or 'microsoftonline' in current_url.lower():
                self.logger.error(f"Redirected to login page: {current_url}")
                self.logger.error("The website requires authentication. Please log in manually or provide credentials.")
                return False
            
            # Wait for employee cards to load
            await self.page.wait_for_selector('body', timeout=self.timeout)
            
            self.logger.info("Successfully navigated to employee page")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to employee page: {str(e)}")
            return False
    
    async def get_employee_profile_links(self) -> List[str]:
        """
        Extract all employee profile links from the main page.
        
        Returns:
            List of profile URLs
        """
        try:
            # Wait for the page to load completely
            await self.page.wait_for_load_state('networkidle')
            
            # Try multiple selectors to find employee links
            profile_links = []
            
            # Method 1: Look for direct profile links
            links = await self.page.query_selector_all('a[href*="/employee/"], a[href*="/profile/"], a[href*="/staff/"]')
            for link in links:
                href = await link.get_attribute('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    profile_links.append(full_url)
            
            # Method 2: Look for clickable employee cards/images
            if not profile_links:
                employee_elements = await self.page.query_selector_all(
                    '.employee-card, .profile-card, .staff-card, [data-employee], .employee-item'
                )
                for element in employee_elements:
                    # Try to find a link within the element
                    link = await element.query_selector('a')
                    if link:
                        href = await link.get_attribute('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            profile_links.append(full_url)
                    else:
                        # If no link, try to make the element clickable
                        onclick = await element.get_attribute('onclick')
                        if onclick and 'employee' in onclick.lower():
                            # Extract URL from onclick or use element data
                            data_id = await element.get_attribute('data-id')
                            if data_id:
                                profile_url = f"{self.base_url.rsplit('/', 1)[0]}/employee/{data_id}"
                                profile_links.append(profile_url)
            
            # Remove duplicates
            profile_links = list(set(profile_links))
            
            self.logger.info(f"Found {len(profile_links)} employee profile links")
            return profile_links
            
        except Exception as e:
            self.logger.error(f"Error extracting profile links: {str(e)}")
            return []
    
    async def get_employee_office_locations(self) -> Dict[str, str]:
        """
        Extract office location mapping from the main directory page.
        This method looks for the office location filter dropdown data.
        
        Returns:
            Dictionary mapping employee profile URLs to office locations
        """
        try:
            office_locations = {}
            
            # Wait for the page to load completely
            await self.page.wait_for_load_state('networkidle')
            
            # Look for office location filter dropdown or data
            # Try to find the filter dropdown structure
            filter_elements = await self.page.query_selector_all(
                '[data-filter*="location"], [data-filter*="office"], .filter-location, .office-filter'
            )
            
            for element in filter_elements:
                # Try to extract location data from filter elements
                location_data = await element.get_attribute('data-locations')
                if location_data:
                    try:
                        import json
                        locations = json.loads(location_data)
                        # Process location data if it's structured
                        self.logger.info(f"Found location filter data: {locations}")
                    except:
                        pass
            
            # Alternative: Look for employee cards with location information
            employee_cards = await self.page.query_selector_all(
                '.employee-card, .profile-card, .staff-card, [data-employee], .employee-item'
            )
            
            for card in employee_cards:
                # Try to find location within each employee card
                location_element = await card.query_selector(
                    '.location, .office, .workplace, [data-location], .employee-location'
                )
                if location_element:
                    location_text = await location_element.text_content()
                    if location_text:
                        # Find the profile link for this card
                        link = await card.query_selector('a[href*="/employee/"]')
                        if link:
                            href = await link.get_attribute('href')
                            if href:
                                full_url = urljoin(self.base_url, href)
                                normalized_location = self._normalize_office_location(location_text.strip())
                                office_locations[full_url] = normalized_location
            
            self.logger.info(f"Extracted office locations for {len(office_locations)} employees from main page")
            return office_locations
            
        except Exception as e:
            self.logger.error(f"Error extracting office locations from main page: {str(e)}")
            return {}
    
    async def scrape_employee_profile(self, profile_url: str) -> Optional[EmployeeData]:
        """
        Scrape individual employee profile page.
        
        Args:
            profile_url: URL of the employee profile page
            
        Returns:
            EmployeeData object or None if failed
        """
        try:
            self.logger.info(f"Scraping profile: {profile_url}")
            
            # Navigate to profile page
            await self.page.goto(profile_url, wait_until='networkidle')
            await self.page.wait_for_load_state('networkidle')
            
            # Create employee data object
            employee = EmployeeData()
            employee.profile_url = profile_url
            
            # Extract profile ID from URL
            parsed_url = urlparse(profile_url)
            employee.profile_id = parsed_url.path.split('/')[-1]
            
            # Extract basic information
            await self._extract_basic_info(employee)
            
            # Extract contact information
            await self._extract_contact_info(employee)
            
            # Extract bio and additional info
            await self._extract_additional_info(employee)
            
            # Download profile image if enabled
            if self.download_images and self.image_downloader:
                await self._download_profile_image(employee)
            
            self.logger.info(f"Successfully scraped: {employee.get_display_name()}")
            return employee
            
        except Exception as e:
            self.logger.error(f"Error scraping profile {profile_url}: {str(e)}")
            return None
    
    async def _extract_basic_info(self, employee: EmployeeData):
        """Extract basic employee information."""
        try:
            # Extract name
            name_selectors = [
                'h1', 'h2', '.employee-name', '.profile-name', 
                '.staff-name', '[data-name]', '.name'
            ]
            
            for selector in name_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    name = await element.text_content()
                    if name and name.strip():
                        employee.real_name = name.strip()
                        break
            
            # Extract email
            email_element = await self.page.query_selector('a[href^="mailto:"]')
            if email_element:
                email = await email_element.get_attribute('href')
                if email:
                    employee.email = email.replace('mailto:', '')
            
            # Extract position/title
            title_selectors = [
                '.employee-title', '.profile-title', '.position', 
                '.job-title', '.role', '[data-title]'
            ]
            
            for selector in title_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    title = await element.text_content()
                    if title and title.strip():
                        employee.position = title.strip()
                        break
            
            # Extract department
            dept_selectors = [
                '.department', '.team', '.division', '.group',
                '[data-department]', '.org-unit'
            ]
            
            for selector in dept_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    dept = await element.text_content()
                    if dept and dept.strip():
                        employee.department = dept.strip()
                        break
            
        except Exception as e:
            self.logger.error(f"Error extracting basic info: {str(e)}")
    
    async def _extract_contact_info(self, employee: EmployeeData):
        """Extract contact information."""
        try:
            # Extract phone numbers
            phone_elements = await self.page.query_selector_all('a[href^="tel:"]')
            for element in phone_elements:
                phone = await element.get_attribute('href')
                if phone:
                    phone = phone.replace('tel:', '')
                    if not employee.phone:
                        employee.phone = phone
                    elif not employee.mobile:
                        employee.mobile = phone
            
            # Extract office location
            location_selectors = [
                '.office', '.location', '.address', '.workplace',
                '[data-location]', '.building', '.office-location',
                '.employee-location', '.staff-location', '.work-location',
                '.location-info', '.office-info', '.workplace-info',
                '[data-office]', '[data-workplace]', '.location-text',
                '.office-text', '.workplace-text', '.location-label',
                '.office-label', '.workplace-label'
            ]
            
            for selector in location_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    location = await element.text_content()
                    if location and location.strip():
                        # Clean up the location text
                        location = location.strip()
                        # Map common variations to standard names
                        location = self._normalize_office_location(location)
                        employee.office_location = location
                        break
            
            # If no location found with selectors, try to extract from page content
            if not employee.office_location:
                await self._extract_location_from_content(employee)
            
            # Extract LinkedIn URL
            linkedin_element = await self.page.query_selector('a[href*="linkedin.com"]')
            if linkedin_element:
                employee.linkedin_url = await linkedin_element.get_attribute('href')
            
            # Extract website URL
            website_element = await self.page.query_selector('a[href*="http"]:not([href*="linkedin.com"]):not([href*="mailto:"]):not([href*="tel:"])')
            if website_element:
                href = await website_element.get_attribute('href')
                if href and not href.startswith('mailto:') and not href.startswith('tel:'):
                    employee.website_url = href
            
        except Exception as e:
            self.logger.error(f"Error extracting contact info: {str(e)}")
    
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
    
    async def _extract_location_from_content(self, employee: EmployeeData):
        """
        Try to extract office location from page content using text analysis.
        
        Args:
            employee: EmployeeData object to update
        """
        try:
            # Get all text content from the page
            page_text = await self.page.text_content('body')
            if not page_text:
                return
            
            # Look for location patterns in the text
            location_patterns = [
                r'(?:office|location|workplace|based in|located in)[\s:]*([^,\n]+)',
                r'(new york|nyc|shanghai|california|ca|los angeles|san francisco)',
                r'(?:works?|based|located)[\s]*(?:in|at)[\s]*([^,\n]+)'
            ]
            
            import re
            for pattern in location_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1]
                    
                    location = self._normalize_office_location(match.strip())
                    if location and location.lower() in ['new york', 'shanghai', 'california']:
                        employee.office_location = location
                        self.logger.info(f"Extracted location from content: {location}")
                        return
                        
        except Exception as e:
            self.logger.error(f"Error extracting location from content: {str(e)}")
    
    async def _extract_additional_info(self, employee: EmployeeData):
        """Extract bio and additional information."""
        try:
            # Extract bio
            bio_selectors = [
                '.bio', '.about', '.description', '.employee-bio',
                '.profile-description', '.summary', '.introduction'
            ]
            
            for selector in bio_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    bio = await element.text_content()
                    if bio and bio.strip():
                        employee.bio = bio.strip()
                        break
            
        except Exception as e:
            self.logger.error(f"Error extracting additional info: {str(e)}")
    
    async def _download_profile_image(self, employee: EmployeeData):
        """Download the employee's profile image."""
        try:
            # Find profile image
            image_selectors = [
                'img.profile-image', '.employee-photo img', '.avatar img',
                '.profile-picture img', '.staff-photo img', 'img[alt*="profile"]',
                'img[alt*="photo"]', '.headshot img'
            ]
            
            for selector in image_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    image_url = await element.get_attribute('src')
                    if image_url:
                        # Convert relative URL to absolute
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif image_url.startswith('/'):
                            parsed_base = urlparse(self.base_url)
                            image_url = f"{parsed_base.scheme}://{parsed_base.netloc}{image_url}"
                        
                        employee.image_url = image_url
                        
                        # Download the image
                        local_path = await self.image_downloader.download_image(
                            image_url, employee.get_display_name()
                        )
                        employee.image_local_path = local_path
                        break
            
        except Exception as e:
            self.logger.error(f"Error downloading profile image: {str(e)}")
    
    async def scrape_all_employees(self) -> List[EmployeeData]:
        """
        Scrape all employees from the directory.
        
        Returns:
            List of EmployeeData objects
        """
        try:
            # Navigate to main page
            if not await self.navigate_to_employee_page():
                return []
            
            # Get all profile links
            profile_links = await self.get_employee_profile_links()
            
            if not profile_links:
                self.logger.warning("No employee profile links found")
                return []
            
            # Scrape each profile
            employees = []
            for i, profile_url in enumerate(profile_links, 1):
                self.logger.info(f"Scraping employee {i}/{len(profile_links)}")
                
                employee = await self.scrape_employee_profile(profile_url)
                if employee and employee.is_valid():
                    employees.append(employee)
                
                # Add small delay to be respectful
                await asyncio.sleep(1)
            
            self.employees = employees
            self.logger.info(f"Successfully scraped {len(employees)} employees")
            return employees
            
        except Exception as e:
            self.logger.error(f"Error scraping employees: {str(e)}")
            return []
    
    def save_to_json(self, filename: str = "employees_data.json"):
        """
        Save scraped employee data to JSON file.
        
        Args:
            filename: Output filename
        """
        try:
            output_path = Path(filename)
            
            # Convert employees to dictionaries
            employees_data = [emp.to_dict() for emp in self.employees]
            
            # Create output data structure
            output_data = {
                "metadata": {
                    "total_employees": len(self.employees),
                    "scraped_at": self.employees[0].scraped_at if self.employees else None,
                    "source_url": self.base_url,
                    "download_images": self.download_images
                },
                "employees": employees_data
            }
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(self.employees)} employees to {output_path}")
            
            # Also save individual employee files for easier access
            individual_dir = output_path.parent / "individual_employees"
            individual_dir.mkdir(exist_ok=True)
            
            for employee in self.employees:
                if employee.real_name:
                    safe_name = self.image_downloader._sanitize_filename(employee.real_name) if self.image_downloader else employee.real_name
                    individual_file = individual_dir / f"{safe_name}.json"
                    with open(individual_file, 'w', encoding='utf-8') as f:
                        json.dump(employee.to_dict(), f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {str(e)}")
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get statistics about the scraping process."""
        if not self.employees:
            return {"error": "No employees scraped yet"}
        
        stats = {
            "total_employees": len(self.employees),
            "valid_employees": len([emp for emp in self.employees if emp.is_valid()]),
            "employees_with_images": len([emp for emp in self.employees if emp.image_local_path]),
            "employees_with_emails": len([emp for emp in self.employees if emp.email]),
            "employees_with_phones": len([emp for emp in self.employees if emp.phone or emp.mobile]),
            "employees_with_bios": len([emp for emp in self.employees if emp.bio]),
            "departments": list(set([emp.department for emp in self.employees if emp.department])),
            "scraped_at": self.employees[0].scraped_at if self.employees else None
        }
        
        if self.image_downloader:
            stats.update(self.image_downloader.get_download_stats())
        
        return stats
