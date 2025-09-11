"""
Complete employee scraper that finds individual profile URLs and extracts detailed information.
"""

# Standard library imports
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict

# Third-party imports
from playwright.async_api import async_playwright

# Local imports
from .models import EmployeeData
from ..config.settings import ScraperConfig
from ..services.auth import AutoLogin
from ..services.image_downloader import ImageDownloader
from ..services.html_generator import HTMLReportGenerator
from ..services.seating_scraper import SeatingChartScraper
from .data_merger import DataMerger


class CompleteScraper:
    """
    Complete employee scraper that handles login, finds profile URLs, and extracts detailed information.
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        """
        Initialize the complete scraper.
        
        Args:
            config: Scraper configuration object
        """
        self.config = config or ScraperConfig()
        self.logger = logging.getLogger(__name__)
        self.auto_login = AutoLogin()
        self.image_downloader = ImageDownloader(self.config.IMAGE_DOWNLOAD_DIR)
        self.html_generator = HTMLReportGenerator(self.config.OUTPUT_DIR)
        self.seating_scraper = SeatingChartScraper(headless=self.config.HEADLESS, timeout=self.config.TIMEOUT, debug_mode=self.config.DEBUG_MODE)
        self.data_merger = DataMerger()
        
        # Setup debug directories if in debug mode
        if self.config.DEBUG_MODE:
            self.config.setup_debug_directories()
    
    async def find_employee_profile_links(self, page) -> List[Tuple[str, str, str]]:
        """
        Find all employee profile links from the main directory page.
        Scrolls down to load all employees if the page uses lazy loading.
        Also extracts office location from the main page.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of tuples (profile_url, employee_name, office_location)
        """
        self.logger.info("Finding employee profile links...")
        
        # First, try to extract office location data from the filter dropdown
        office_location_mapping = await self._extract_office_location_filter_data(page)
        
        # Scroll down to load all employees (in case of lazy loading)
        await self._scroll_to_load_all_employees(page)
        
        # Get all links on the page after scrolling
        all_links = await page.query_selector_all('a')
        self.logger.info(f"Found {len(all_links)} total links after scrolling")
        
        employee_links = []
        seen_urls = set()  # To avoid duplicates
        
        for link in all_links:
            try:
                href = await link.get_attribute('href')
                text = await link.text_content()
                
                if href and text:
                    # Look for links that contain employee profile URLs
                    if 'employee/' in href and len(text.strip()) > 2 and len(text.strip()) < 50:
                        # Check if the text looks like a name (capitalized words)
                        if text.strip().count(' ') <= 3 and text.strip().split()[0][0].isupper():
                            # Convert relative URL to absolute if needed
                            if href.startswith('/'):
                                href = f"https://ei.ennead.com{href}"
                            elif not href.startswith('http'):
                                href = f"https://ei.ennead.com/{href}"
                            
                            # Avoid duplicates
                            if href not in seen_urls:
                                seen_urls.add(href)
                                
                                # Try to extract office location from the main page
                                office_location = await self._extract_office_location_from_main_page(link)
                                
                                # If we couldn't find location from the main page, try the filter mapping
                                if not office_location and office_location_mapping:
                                    office_location = office_location_mapping.get(href, "")
                                
                                employee_links.append((href, text.strip(), office_location))
                                self.logger.info(f"  Found employee link: {text.strip()} -> {href} (Office: {office_location or 'Not found'})")
            
            except Exception as e:
                continue
        
        self.logger.info(f"Found {len(employee_links)} unique employee profile links")
        
        # Apply debug mode limiting if enabled
        if self.config.DEBUG_MODE and len(employee_links) > self.config.DEBUG_MAX_EMPLOYEES:
            self.logger.info(f"DEBUG MODE: Limiting to first {self.config.DEBUG_MAX_EMPLOYEES} employees")
            employee_links = employee_links[:self.config.DEBUG_MAX_EMPLOYEES]
        
        return employee_links
    
    async def _extract_office_location_from_main_page(self, employee_link) -> str:
        """
        Extract office location from the main page for an employee.
        
        Args:
            employee_link: The employee link element from the main page
            
        Returns:
            Office location string or empty string if not found
        """
        try:
            # Method 1: Look for data attributes that might contain office location
            data_location = await employee_link.get_attribute('data-office-location')
            if data_location:
                return self._normalize_office_location(data_location)
            
            # Method 2: Look in the same row/container for location information
            parent = await employee_link.evaluate_handle('el => el.closest("tr, div, li, [class*=\"employee\"], [class*=\"card\"]")')
            if parent:
                parent_text = await parent.text_content()
                if parent_text:
                    # Look for common office location patterns
                    lines = [line.strip() for line in parent_text.split('\n') if line.strip()]
                    for line in lines:
                        # Skip the name itself
                        if line == await employee_link.text_content():
                            continue
                        # Look for location patterns (cities, states, office names)
                        if any(keyword in line.lower() for keyword in ['office', 'location', 'nyc', 'new york', 'california', 'ca', 'ny', 'shanghai']):
                            normalized = self._normalize_office_location(line)
                            if normalized.lower() in ['new york', 'shanghai', 'california']:
                                return normalized
            
            # Method 3: Look for nearby elements with location info
            nearby_elements = await employee_link.evaluate_handle('''
                el => {
                    const parent = el.closest('tr, div, li, [class*="employee"], [class*="card"]');
                    if (parent) {
                        const siblings = Array.from(parent.children);
                        const linkIndex = siblings.indexOf(el);
                        // Look at elements after the link
                        for (let i = linkIndex + 1; i < siblings.length; i++) {
                            const text = siblings[i].textContent?.trim();
                            if (text && text.length > 0 && text.length < 50) {
                                // Check if it looks like a location
                                const lowerText = text.toLowerCase();
                                if (lowerText.includes('new york') || lowerText.includes('nyc') || 
                                    lowerText.includes('california') || lowerText.includes('ca') ||
                                    lowerText.includes('shanghai') || lowerText.includes('office') ||
                                    lowerText.includes('location')) {
                                    return text;
                                }
                            }
                        }
                    }
                    return null;
                }
            ''')
            
            if nearby_elements:
                location_text = await nearby_elements.text_content()
                if location_text and location_text.strip():
                    normalized = self._normalize_office_location(location_text.strip())
                    if normalized.lower() in ['new york', 'shanghai', 'california']:
                        return normalized
            
            # Method 4: Look for CSS classes that might indicate office location
            parent_classes = await parent.get_attribute('class') if parent else None
            if parent_classes:
                # Check if parent has location-related classes
                if any(loc in parent_classes.lower() for loc in ['ny', 'nyc', 'newyork', 'california', 'ca', 'shanghai']):
                    for loc in ['ny', 'nyc', 'newyork', 'california', 'ca', 'shanghai']:
                        if loc in parent_classes.lower():
                            return self._normalize_office_location(loc)
            
        except Exception as e:
            self.logger.debug(f"Error extracting office location: {e}")
        
        return ""
    
    def _normalize_office_location(self, location: str) -> str:
        """
        Normalize office location names to standard format.
        
        Args:
            location: Raw location string
            
        Returns:
            Normalized location string
        """
        if not location:
            return ""
            
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
    
    async def _extract_office_location_filter_data(self, page) -> Dict[str, str]:
        """
        Extract office location data by clicking through each location checkbox
        and mapping employees to their office locations.
        This is the only way to get office location data since it's not visible in employee cards.
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary mapping employee profile URLs to office locations
        """
        try:
            self.logger.info("Extracting office location data using location filter checkboxes...")
            
            # DEBUG: Capture DOM before starting office location extraction
            if self.config.DEBUG_MODE:
                await self._capture_dom_for_debug(page, "office_location_extraction_start", "Starting office location extraction using filter")
            
            # Look for the Office Location filter button/dropdown
            office_filter_selectors = [
                'div[data-key="text_default_1"]',  # Specific selector for Office Location filter
                'div[data-key="text_default_1"] div',  # The inner div that's clickable
                'div[data-key="text_default_1"] .pill',  # The pill element inside
                'button:has-text("Office Location")',
                'div:has-text("Office Location")',
                '[data-filter="office-location"]',
                '[data-filter="location"]',
                '.filter-button:has-text("Office Location")',
                'button[title*="Office Location"]',
                'button[aria-label*="Office Location"]',
                '.office-location-filter',
                '.location-filter',
                '.office-filter',
                '[class*="office-location"]',
                '[class*="location-filter"]',
                '[class*="office-filter"]',
                'button[class*="filter"]',
                'div[class*="filter"]',
                'span[class*="filter"]'
            ]
            
            office_filter_element = None
            for selector in office_filter_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        office_filter_element = element
                        self.logger.info(f"Found office location filter with selector: {selector}")
                        break
                except:
                    continue
            
            if not office_filter_element:
                self.logger.error("Office location filter not found - cannot extract office location data")
                return {}
            
            # Click on the filter to open the dropdown
            await office_filter_element.click()
            await asyncio.sleep(3)  # Wait longer for dropdown to open
            
            # DEBUG: Capture DOM after clicking office location filter
            if self.config.DEBUG_MODE:
                await self._capture_dom_for_debug(page, "office_location_filter_opened", "Office Location filter dropdown opened")
            
            # Look for checkboxes for location selection (they look like radio buttons but are actually checkboxes)
            self.logger.info("Looking for location checkboxes...")
            location_checkboxes = []
            
            try:
                # Wait for the dropdown to appear
                await asyncio.sleep(2)
                
                # Look for checkboxes (they may be styled to look like radio buttons)
                checkboxes = await page.query_selector_all('input[type="checkbox"]')
                if checkboxes:
                    self.logger.info(f"SUCCESS: Found {len(checkboxes)} checkboxes")
                    location_checkboxes = checkboxes
                else:
                    self.logger.info("FAILED: No checkboxes found")
                    
                    # Fallback: look for any clickable elements that might be location options
                    location_elements = await page.query_selector_all('div:has-text("New York"), div:has-text("Shanghai"), div:has-text("California")')
                    if location_elements:
                        self.logger.info(f"Found {len(location_elements)} potential location elements")
                        location_checkboxes = location_elements
                        
            except Exception as e:
                self.logger.info(f"FAILED: {e}")
            
            # Look for the dropdown content with office location checkboxes
            # Try multiple approaches to find the dropdown
            dropdown_selectors = [
                # Standard dropdown selectors
                '[role="menu"]',
                '[role="listbox"]',
                '.dropdown-menu',
                '.filter-dropdown',
                '.office-location-options',
                '.location-options',
                '.filter-options',
                
                # Generic dropdown patterns
                'div[class*="dropdown"]',
                'div[class*="menu"]',
                'div[class*="portal"]',
                'div[class*="overlay"]',
                'div[class*="popup"]',
                'div[class*="modal"]',
                'div[class*="dialog"]',
                
                # Look for any div that appeared after clicking
                'div[style*="position: absolute"]',
                'div[style*="position: fixed"]',
                'div[style*="z-index"]',
                
                # Look for any element that might contain checkboxes
                'div:has(input[type="checkbox"])',
                'ul:has(input[type="checkbox"])',
                'ol:has(input[type="checkbox"])',
                
                # Look for any element with "office" or "location" in class
                '[class*="office"]',
                '[class*="location"]',
                '[class*="filter"]',
                
                # Look for overlay/portal containers that might be outside main DOM
                'body > div:not(#s6-app)',
                'html > body > div:not(#s6-app)',
                'div[data-portal]',
                'div[data-overlay]',
                'div[data-modal]',
                'div[data-dropdown]',
                'div[data-menu]',
                'div[data-popup]',
                'div[data-tooltip]',
                'div[data-popover]',
                
                # Look for elements that might be dynamically created overlays
                'div[class*="Mui"]',  # Material-UI components
                'div[class*="ant"]',  # Ant Design components
                'div[class*="chakra"]',  # Chakra UI components
                'div[class*="semantic"]',  # Semantic UI components
                
                # Look for any element that might be the dropdown with positioning
                'div[style*="top:"]',
                'div[style*="left:"]',
                'div[style*="right:"]',
                'div[style*="bottom:"]',
                
                # Look for elements that might be React portals
                'div[id*="portal"]',
                'div[id*="overlay"]',
                'div[id*="modal"]',
                'div[id*="dropdown"]',
                'div[id*="menu"]',
                'div[id*="popup"]',
                'div[id*="tooltip"]',
                'div[id*="popover"]'
            ]
            
            dropdown_content = None
            for selector in dropdown_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        dropdown_content = element
                        self.logger.info(f"Found dropdown content with selector: {selector}")
                        break
                except:
                    continue
            
            # Use the checkboxes we found
            if not location_checkboxes:
                self.logger.info("No location checkboxes found")
                # DEBUG: Capture DOM when no checkboxes are found
                if self.config.DEBUG_MODE:
                    await self._capture_dom_for_debug(page, "office_location_no_checkboxes", "No location checkboxes found in dropdown")
                return {}
            
            # Dictionary to store employee URL to office location mapping
            employee_location_mapping = {}
            
            # Hardcoded location order based on the UI: New York (140), Shanghai (19), California (7)
            location_names = ["New York", "Shanghai", "California"]
            
            # Click through each location checkbox in the hardcoded order
            for i, location_name in enumerate(location_names):
                try:
                    if i < len(location_checkboxes):
                        checkbox = location_checkboxes[i]
                        self.logger.info(f"Processing location {i+1}: {location_name}")
                        
                        # Click the checkbox to filter by this location
                        # Try multiple click methods to ensure it works
                        try:
                            # Method 1: Direct click
                            await checkbox.click()
                        except:
                            try:
                                # Method 2: Force click with JavaScript
                                await page.evaluate("(element) => element.click()", checkbox)
                            except:
                                # Method 3: Click the label if checkbox is not directly clickable
                                label = await page.query_selector(f'label[for="{await checkbox.get_attribute("id")}"]')
                                if label:
                                    await label.click()
                                else:
                                    # Method 4: Click the parent element
                                    parent = await checkbox.query_selector('xpath=..')
                                    if parent:
                                        await parent.click()
                        await asyncio.sleep(2)  # Wait for page to filter
                        
                        # Click Apply button if it exists
                        apply_button = await page.query_selector('button:has-text("Apply")')
                        if apply_button:
                            await apply_button.click()
                            await asyncio.sleep(2)  # Wait for filter to apply
                        
                        # DEBUG: Capture DOM after clicking location checkbox
                        if self.config.DEBUG_MODE:
                            await self._capture_dom_for_debug(page, f"office_location_filtered_{location_name.replace(' ', '_').lower()}", f"Filtered by location: {location_name}")
                        
                        # Get all visible employee names/links for this location
                        employee_links = await self._get_visible_employee_links(page)
                        self.logger.info(f"Found {len(employee_links)} employees for location: {location_name}")
                        
                        # Map each employee to this location
                        for employee_url in employee_links:
                            employee_location_mapping[employee_url] = location_name
                        
                        # Safe reset strategy: uncheck the currently checked checkbox
                        # The checked item jumps to first position after clicking Apply
                        checked_checkboxes = await page.query_selector_all('input[type="checkbox"]:checked')
                        if checked_checkboxes:
                            await checked_checkboxes[0].click()  # Uncheck the first (currently checked) item
                            await asyncio.sleep(1)
                        
                        # Clear the filter by clicking Cancel
                        cancel_button = await page.query_selector('button:has-text("Cancel")')
                        if cancel_button:
                            await cancel_button.click()
                            await asyncio.sleep(1)
                        else:
                            # Reopen the filter to clear it
                            await office_filter_element.click()
                            await asyncio.sleep(1)
                    else:
                        self.logger.warning(f"Not enough checkboxes found for location {location_name}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing location {location_name}: {e}")
                    continue
            
            # Close the dropdown
            await page.click('body')
            await asyncio.sleep(0.5)
            
            self.logger.info(f"Successfully mapped {len(employee_location_mapping)} employees to office locations")
            return employee_location_mapping
            
        except Exception as e:
            self.logger.error(f"Error extracting office location filter data: {e}")
            return {}
    
    async def _extract_office_locations_from_employee_cards(self, page) -> Dict[str, str]:
        """
        Alternative method to extract office location data directly from employee cards.
        This method looks for office location information within individual employee cards
        on the main directory page.
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary mapping employee profile URLs to office locations
        """
        try:
            self.logger.info("Attempting to extract office location data from employee cards...")
            
            # Look for employee cards/containers
            employee_card_selectors = [
                '.employee-card',
                '.employee-item',
                '.employee-container',
                '[class*="employee"]',
                '[class*="card"]',
                '[class*="item"]'
            ]
            
            employee_cards = []
            for selector in employee_card_selectors:
                try:
                    cards = await page.query_selector_all(selector)
                    if cards:
                        employee_cards = cards
                        self.logger.info(f"Found {len(cards)} employee cards with selector: {selector}")
                        break
                except:
                    continue
            
            if not employee_cards:
                self.logger.info("No employee cards found")
                return {}
            
            employee_location_mapping = {}
            
            # Process each employee card to extract location information
            for i, card in enumerate(employee_cards[:20]):  # Limit to first 20 for debugging
                try:
                    # Look for employee link within the card
                    employee_link = await card.query_selector('a[href*="/employee/"]')
                    if not employee_link:
                        continue
                    
                    href = await employee_link.get_attribute('href')
                    if not href:
                        continue
                    
                    if href.startswith('/'):
                        href = f"https://ei.ennead.com{href}"
                    
                    # Look for office location information within the card
                    location_selectors = [
                        '.office-location',
                        '.location',
                        '.office',
                        '[class*="location"]',
                        '[class*="office"]',
                        '.employee-location',
                        '.work-location'
                    ]
                    
                    location_text = None
                    for loc_selector in location_selectors:
                        try:
                            loc_element = await card.query_selector(loc_selector)
                            if loc_element:
                                location_text = await loc_element.text_content()
                                if location_text and location_text.strip():
                                    location_text = location_text.strip()
                                    break
                        except:
                            continue
                    
                    # If no specific location element found, try to extract from card text
                    if not location_text:
                        try:
                            card_text = await card.text_content()
                            if card_text:
                                # Look for common location patterns in the text
                                location_patterns = [
                                    r'(New York|NY)',
                                    r'(Los Angeles|LA)',
                                    r'(San Francisco|SF)',
                                    r'(Chicago|IL)',
                                    r'(Boston|MA)',
                                    r'(Seattle|WA)',
                                    r'(Denver|CO)',
                                    r'(Austin|TX)',
                                    r'(Miami|FL)',
                                    r'(Philadelphia|PA)'
                                ]
                                
                                for pattern in location_patterns:
                                    match = re.search(pattern, card_text, re.IGNORECASE)
                                    if match:
                                        location_text = match.group(1)
                                        break
                        except:
                            continue
                    
                    if location_text:
                        employee_location_mapping[href] = location_text
                        self.logger.info(f"Found location '{location_text}' for employee card {i}")
                    
                except Exception as e:
                    self.logger.warning(f"Error processing employee card {i}: {e}")
                    continue
            
            self.logger.info(f"Extracted office locations for {len(employee_location_mapping)} employees from cards")
            return employee_location_mapping
            
        except Exception as e:
            self.logger.error(f"Error extracting office location data from employee cards: {e}")
            return {}
    
    async def _get_checkbox_location_name(self, checkbox) -> str:
        """
        Extract the location name from a checkbox element.
        
        Args:
            checkbox: Playwright element handle for the checkbox
            
        Returns:
            Location name string or empty string if not found
        """
        try:
            # Try to get the label text
            label = await checkbox.evaluate_handle('el => el.closest("label")')
            if label:
                label_text = await label.text_content()
                if label_text:
                    # Clean up the text (remove checkbox symbols, counts, etc.)
                    clean_text = label_text.strip()
                    # Remove common patterns like "(140)", "(19)", "(7)"
                    import re
                    clean_text = re.sub(r'\s*\(\d+\)\s*', '', clean_text)
                    if clean_text:
                        return clean_text
            
            # Try to get text from parent element
            parent = await checkbox.evaluate_handle('el => el.parentElement')
            if parent:
                parent_text = await parent.text_content()
                if parent_text:
                    # Clean up the text (remove checkbox symbols, counts, etc.)
                    clean_text = parent_text.strip()
                    import re
                    clean_text = re.sub(r'\s*\(\d+\)\s*', '', clean_text)
                    if clean_text:
                        return clean_text
            
            # Try to get text from sibling elements
            siblings = await checkbox.evaluate_handle('el => el.parentElement.children')
            if siblings:
                for i in range(await siblings.evaluate('el => el.length')):
                    sibling = await siblings.evaluate_handle(f'el => el.children[{i}]')
                    if sibling:
                        sibling_text = await sibling.text_content()
                        if sibling_text and sibling_text.strip():
                            clean_text = sibling_text.strip().replace('☐', '').replace('☑', '').replace('✓', '').strip()
                            if clean_text:
                                return clean_text
            
            # Try to get text from the next sibling element
            next_sibling = await checkbox.evaluate_handle('el => el.nextElementSibling')
            if next_sibling:
                next_text = await next_sibling.text_content()
                if next_text and next_text.strip():
                    clean_text = next_text.strip().replace('☐', '').replace('☑', '').replace('✓', '').strip()
                    if clean_text:
                        return clean_text
            
            # Try to get text from the previous sibling element
            prev_sibling = await checkbox.evaluate_handle('el => el.previousElementSibling')
            if prev_sibling:
                prev_text = await prev_sibling.text_content()
                if prev_text and prev_text.strip():
                    clean_text = prev_text.strip().replace('☐', '').replace('☑', '').replace('✓', '').strip()
                    if clean_text:
                        return clean_text
            
            # Try to get text from any nearby text node
            nearby_text = await checkbox.evaluate_handle('''el => {
                let text = "";
                let current = el;
                for (let i = 0; i < 3; i++) {
                    if (current && current.textContent) {
                        text = current.textContent.trim();
                        if (text && text.length > 0 && text.length < 100) {
                            break;
                        }
                    }
                    current = current.parentElement;
                }
                return text;
            }''')
            if nearby_text:
                clean_text = nearby_text.strip().replace('☐', '').replace('☑', '').replace('✓', '').strip()
                if clean_text:
                    return clean_text
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Error getting checkbox location name: {e}")
            return ""
    
    async def _get_visible_employee_links(self, page) -> List[str]:
        """
        Get all visible employee profile links on the current page.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of employee profile URLs
        """
        try:
            # Wait for the page to update after filtering
            await page.wait_for_load_state('networkidle')
            
            # Find all employee profile links
            employee_link_selectors = [
                'a[href*="/employee/"]',
                '.employee-card a[href*="/employee/"]',
                '.profile-card a[href*="/employee/"]',
                '[data-employee] a[href*="/employee/"]'
            ]
            
            employee_links = []
            for selector in employee_link_selectors:
                try:
                    links = await page.query_selector_all(selector)
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and href not in employee_links:
                            if href.startswith('/'):
                                href = f"https://ei.ennead.com{href}"
                            employee_links.append(href)
                except:
                    continue
            
            return employee_links
            
        except Exception as e:
            self.logger.error(f"Error getting visible employee links: {e}")
            return []
    
    async def _scroll_to_load_all_employees(self, page):
        """
        Scroll down the page to load all employees (for lazy loading scenarios).
        
        Args:
            page: Playwright page object
        """
        self.logger.info("Scrolling to load all employees...")
        
        # Get initial count of employee links
        initial_links = await page.query_selector_all('a[href*="employee/"]')
        initial_count = len(initial_links)
        self.logger.info(f"Initial employee links found: {initial_count}")
        
        # Scroll down multiple times to trigger lazy loading
        scroll_attempts = 0
        max_scroll_attempts = 10
        last_count = initial_count
        
        while scroll_attempts < max_scroll_attempts:
            # Scroll to bottom of page
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)  # Wait for content to load
            
            # Check if new content was loaded
            current_links = await page.query_selector_all('a[href*="employee/"]')
            current_count = len(current_links)
            
            self.logger.info(f"Scroll attempt {scroll_attempts + 1}: Found {current_count} employee links")
            
            # If no new links were loaded, we've reached the end
            if current_count == last_count:
                self.logger.info("No new employees loaded, stopping scroll")
                break
            
            last_count = current_count
            scroll_attempts += 1
        
        # Final scroll to top to ensure we can see all content
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        
        final_links = await page.query_selector_all('a[href*="employee/"]')
        final_count = len(final_links)
        self.logger.info(f"Final employee links found after scrolling: {final_count}")
        
        return final_count
    
    async def _try_expand_projects_section(self, page, employee_name: str):
        """
        Try to find and click on the projects section to expand it and show more details.
        
        Args:
            page: Playwright page object
            employee_name: Name of the employee for logging
        """
        self.logger.info(f"Attempting to expand projects section for {employee_name}")
        
        # Try multiple selectors to find the projects section that can be clicked
        project_section_selectors = [
            # Look for clickable elements containing "Projects" text
            'div:has-text("Projects")',
            'span:has-text("Projects")',
            'button:has-text("Projects")',
            'a:has-text("Projects")',
            # Look for expandable sections
            'div[class*="expandable"]:has-text("Projects")',
            'div[class*="collapsible"]:has-text("Projects")',
            'div[class*="accordion"]:has-text("Projects")',
            # Look for sections with project count
            'div:has-text("projects")',
            'span:has-text("projects")',
            # Look for specific project-related classes
            'div[class*="project"]',
            'div[class*="Project"]'
        ]
        
        for selector in project_section_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        # Check if element is visible and clickable
                        is_visible = await element.is_visible()
                        if not is_visible:
                            continue
                            
                        # Get the text content to verify it's project-related
                        text_content = await element.text_content()
                        if text_content and ('project' in text_content.lower() or 'Project' in text_content):
                            self.logger.info(f"Found potential projects section: '{text_content.strip()}'")
                            
                            # Try to click on the element
                            await element.click()
                            await asyncio.sleep(1)  # Wait for expansion
                            
                            # Check if more project links appeared after clicking
                            project_links_after = await page.query_selector_all('a[href*="/project/"]')
                            if len(project_links_after) > 0:
                                self.logger.info(f"Successfully expanded projects section for {employee_name}, found {len(project_links_after)} project links")
                                return True
                                
                    except Exception as e:
                        # Element might not be clickable, continue to next
                        continue
                        
            except Exception as e:
                # Selector might not work, continue to next
                continue
        
        self.logger.info(f"Could not expand projects section for {employee_name}")
        return False
    
    async def _extract_projects_from_table(self, page, employee):
        """
        Extract project data from the projects table with improved parsing logic.
        
        Args:
            page: Playwright page object
            employee: EmployeeData object to store project information
        """
        self.logger.info(f"Extracting projects from table for {employee.real_name}")
        
        # First, let's debug the table structure
        await self._debug_table_structure(page, employee.real_name)
        
        # Try multiple approaches to find project data
        project_extraction_methods = [
            self._extract_projects_method_table_rows,  # Proper table row parsing
            self._extract_projects_method_1,  # Grid view approach
            self._extract_projects_method_2,  # Table row approach
            self._extract_projects_method_3,  # Direct link approach
        ]
        
        for method in project_extraction_methods:
            try:
                projects_found = await method(page, employee)
                if projects_found > 0:
                    self.logger.info(f"Found {projects_found} projects using method {method.__name__}")
                    return
            except Exception as e:
                self.logger.warning(f"Method {method.__name__} failed: {e}")
                continue
        
        self.logger.warning(f"No projects found for {employee.real_name} using any method")
    
    async def _debug_table_structure(self, page, employee_name):
        """
        Debug the table structure to understand how project data is organized.
        
        Args:
            page: Playwright page object
            employee_name: Name of the employee for logging
        """
        self.logger.info(f"Debugging table structure for {employee_name}")
        
        # Get all possible table elements
        table_elements = await page.query_selector_all('table, div[class*="table"], div[class*="grid"], div[class*="row"]')
        self.logger.info(f"Found {len(table_elements)} potential table elements")
        
        # Look for grid view cells
        grid_cells = await page.query_selector_all('div[class*="gridViewStyles__HorizontalCell"]')
        self.logger.info(f"Found {len(grid_cells)} grid view cells")
        
        # Debug first few cells
        for i, cell in enumerate(grid_cells[:5]):  # Only debug first 5 cells
            try:
                cell_text = await cell.text_content()
                cell_html = await cell.inner_html()
                self.logger.info(f"Cell {i}: Text='{cell_text}', HTML='{cell_html[:200]}...'")
            except Exception as e:
                self.logger.warning(f"Error debugging cell {i}: {e}")
        
        # Look for project links
        project_links = await page.query_selector_all('a[href*="/project/"]')
        self.logger.info(f"Found {len(project_links)} project links")
        
        # Debug first few project links
        for i, link in enumerate(project_links[:3]):  # Only debug first 3 links
            try:
                link_text = await link.text_content()
                link_href = await link.get_attribute('href')
                self.logger.info(f"Project link {i}: Text='{link_text}', URL='{link_href}'")
            except Exception as e:
                self.logger.warning(f"Error debugging project link {i}: {e}")
    
    async def _extract_projects_method_table_rows(self, page, employee):
        """Method 0: Extract from proper table rows (most accurate)"""
        projects_found = 0
        seen_urls = set()
        
        # Look for table rows that contain project data
        # Try different selectors for table rows
        table_row_selectors = [
            'tr',  # Standard table rows
            'div[class*="row"]',  # Div-based rows
            'div[class*="Row"]',  # Div-based rows with capital R
            'div[class*="gridViewStyles__HorizontalCell"]',  # Grid view cells
        ]
        
        for selector in table_row_selectors:
            rows = await page.query_selector_all(selector)
            self.logger.info(f"Found {len(rows)} rows with selector: {selector}")
            
            for row in rows:
                try:
                    # Check if this row contains a project link
                    project_links = await row.query_selector_all('a[href*="/project/"]')
                    if not project_links:
                        continue
                    
                    # Find the project link that has actual text content (project name)
                    project_link = None
                    href = None
                    project_name = ''
                    project_number = ''
                    
                    for link in project_links:
                        link_href = await link.get_attribute('href')
                        if link_href.startswith('/'):
                            link_href = f"https://ei.ennead.com{link_href}"
                        
                        # Skip if we've already seen this URL
                        if link_href in seen_urls:
                            continue
                            
                        # Check if this link has text content
                        link_text = await link.text_content()
                        if link_text and link_text.strip():
                            # If this looks like a project name (longer text), use it as the project name
                            if len(link_text.strip()) > 10 and not link_text.strip().isdigit():
                                project_link = link
                                href = link_href
                                project_name = link_text.strip()
                                seen_urls.add(href)
                            # If this looks like a project number (short, numeric), use it as project number
                            elif link_text.strip().isdigit() or len(link_text.strip()) <= 10:
                                project_number = link_text.strip()
                    
                    if not project_link:
                        continue
                    
                    # Try to extract other fields from the row
                    # Look for cells or divs within the row
                    cells = await row.query_selector_all('td, div[class*="cell"], div[class*="Cell"]')
                    
                    client = ''
                    project_role = ''
                    
                    if len(cells) >= 3:
                        # Try to get client from third cell
                        cell_text = await cells[2].text_content()
                        if cell_text and cell_text.strip():
                            client = cell_text.strip()
                    
                    if len(cells) >= 4:
                        # Try to get role from fourth cell
                        cell_text = await cells[3].text_content()
                        if cell_text and cell_text.strip():
                            project_role = cell_text.strip()
                    
                    # If we didn't find cells, try to parse from row text
                    if not client and not project_role:
                        row_text = await row.text_content()
                        if row_text:
                            lines = [line.strip() for line in row_text.split('\n') if line.strip()]
                            # Skip the project name and project number, try to extract other fields
                            for i, line in enumerate(lines[2:], 2):  # Start from third line
                                if i == 2 and not client:
                                    client = line
                                elif i == 3 and not project_role:
                                    project_role = line
                    
                    employee.projects.append({
                        'name': project_name,
                        'number': project_number,
                        'client': client,
                        'role': project_role,
                        'url': href
                    })
                    projects_found += 1
                    
                except Exception as e:
                    continue
            
            # If we found projects with this selector, we're done
            if projects_found > 0:
                self.logger.info(f"Successfully extracted {projects_found} projects using table row method")
                return projects_found
        
        return projects_found
    
    async def _extract_projects_method_1(self, page, employee):
        """Method 1: Extract from grid view cells with improved deduplication"""
        project_rows = await page.query_selector_all('div[class*="gridViewStyles__HorizontalCell"]')
        projects_found = 0
        seen_urls = set()  # Track URLs to avoid duplicates
        
        for row in project_rows:
            try:
                # Look for project links to identify project rows
                project_link = await row.query_selector('a[href*="/project/"]')
                if project_link:
                    # Get the project URL
                    href = await project_link.get_attribute('href')
                    if href.startswith('/'):
                        href = f"https://ei.ennead.com{href}"
                    
                    # Skip if we've already seen this URL
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)
                    
                    # Get project name from the link text
                    project_name = await project_link.text_content()
                    project_name = project_name.strip() if project_name else ''
                    
                    # Try to find additional details in the same row or nearby elements
                    project_number = ''
                    client = ''
                    project_role = ''
                    
                    # Look for additional data in the row
                    row_text = await row.text_content()
                    if row_text:
                        lines = [line.strip() for line in row_text.split('\n') if line.strip()]
                        
                        # Try to intelligently parse the lines
                        # Look for patterns that might indicate project number, client, role
                        for line in lines:
                            if line != project_name:  # Skip the project name itself
                                # Check if it looks like a project number (short, mostly numeric)
                                if len(line) <= 10 and any(c.isdigit() for c in line) and not project_number:
                                    project_number = line
                                # Check if it looks like a client name (longer text, not just numbers)
                                elif len(line) > 10 and not any(c.isdigit() for c in line) and not client:
                                    client = line
                                # Check if it looks like a role (contains role keywords)
                                elif any(keyword in line.lower() for keyword in ['architect', 'designer', 'manager', 'lead', 'director', 'associate', 'principal', 'senior', 'junior']) and not project_role:
                                    project_role = line
                    
                    employee.projects.append({
                        'name': project_name,
                        'number': project_number,
                        'client': client,
                        'role': project_role,
                        'url': href
                    })
                    projects_found += 1
                    
            except Exception as e:
                continue
        
        return projects_found
    
    async def _extract_projects_method_2(self, page, employee):
        """Method 2: Extract from table rows"""
        # Look for table rows containing project data
        table_rows = await page.query_selector_all('tr, div[class*="row"], div[class*="Row"]')
        projects_found = 0
        
        for row in table_rows:
            try:
                # Check if this row contains a project link
                project_link = await row.query_selector('a[href*="/project/"]')
                if project_link:
                    # Get the project URL
                    href = await project_link.get_attribute('href')
                    if href.startswith('/'):
                        href = f"https://ei.ennead.com{href}"
                    
                    # Get project name from the link text
                    project_name = await project_link.text_content()
                    project_name = project_name.strip() if project_name else ''
                    
                    # Try to extract other fields from the row
                    cells = await row.query_selector_all('td, div[class*="cell"], div[class*="Cell"]')
                    project_number = ''
                    client = ''
                    project_role = ''
                    
                    if len(cells) >= 2:
                        project_number = await cells[1].text_content()
                        project_number = project_number.strip() if project_number else ''
                    if len(cells) >= 3:
                        client = await cells[2].text_content()
                        client = client.strip() if client else ''
                    if len(cells) >= 4:
                        project_role = await cells[3].text_content()
                        project_role = project_role.strip() if project_role else ''
                    
                    employee.projects.append({
                        'name': project_name,
                        'number': project_number,
                        'client': client,
                        'role': project_role,
                        'url': href
                    })
                    projects_found += 1
                    
            except Exception as e:
                continue
        
        return projects_found
    
    async def _extract_projects_method_3(self, page, employee):
        """Method 3: Extract directly from project links"""
        # Find all project links on the page
        project_links = await page.query_selector_all('a[href*="/project/"]')
        projects_found = 0
        
        for link in project_links:
            try:
                # Get the project URL
                href = await link.get_attribute('href')
                if href.startswith('/'):
                    href = f"https://ei.ennead.com{href}"
                
                # Get project name from the link text
                project_name = await link.text_content()
                project_name = project_name.strip() if project_name else ''
                
                # For this method, we'll just extract the name and URL
                # Other details might not be easily accessible
                employee.projects.append({
                    'name': project_name,
                    'number': '',
                    'client': '',
                    'role': '',
                    'url': href
                })
                projects_found += 1
                
            except Exception as e:
                continue
        
        return projects_found
    
    async def _extract_projects_from_side_panel(self, page, employee):
        """
        Extract project data from the side panel with improved parsing logic.
        
        Args:
            page: Playwright page object
            employee: EmployeeData object to store project information
        """
        self.logger.info(f"Extracting projects from side panel for {employee.real_name}")
        
        # Try multiple selectors for project links in the side panel
        project_selectors = [
            'div[class*="gridViewStyles__HorizontalCell"] a[href*="/project/"]',
            'a[href*="/project/"]',
            'div[class*="project"] a[href*="/project/"]',
            'div[class*="Project"] a[href*="/project/"]'
        ]
        
        project_links = []
        for selector in project_selectors:
            project_links = await page.query_selector_all(selector)
            if project_links:
                self.logger.info(f"Found {len(project_links)} project links using selector: {selector}")
                break
        
        # Group links by URL to handle multiple links per project
        project_groups = {}
        for link in project_links:
            try:
                href = await link.get_attribute('href')
                text = await link.text_content()
                if href:
                    if href.startswith('/'):
                        href = f"https://ei.ennead.com{href}"
                    
                    if href not in project_groups:
                        project_groups[href] = []
                    
                    if text and text.strip():
                        project_groups[href].append(text.strip())
                        
            except Exception as e:
                continue
        
        # Process each project group
        for href, texts in project_groups.items():
            # Find the project name (longest text that's not just a number)
            project_name = ''
            project_number = ''
            client = ''
            role = ''
            
            for text in texts:
                if len(text) > 10 and not text.isdigit():
                    project_name = text
                elif text.isdigit() or len(text) <= 10:
                    if not project_number:
                        project_number = text
                    elif not client:
                        client = text
                    elif not role:
                        role = text
            
            if project_name:  # Only add if we found a project name
                employee.projects.append({
                    'name': project_name,
                    'number': project_number,
                    'client': client,
                    'role': role,
                    'url': href
                })
    
    async def _scroll_to_load_all_projects(self, page):
        """
        Scroll down the projects page to load all project rows (for lazy loading scenarios).
        
        Args:
            page: Playwright page object
        """
        self.logger.info("Scrolling to load all project rows...")
        
        # First, try to find the specific table container
        table_container = await page.query_selector('.gridViewStyles__GridView, .projects-table, .data-grid, [class*="table"], [class*="grid"]')
        
        # Get initial count of project rows
        initial_rows = await page.query_selector_all('div[class*="gridViewStyles__HorizontalCell"]')
        initial_count = len(initial_rows)
        self.logger.info(f"Initial project rows found: {initial_count}")
        
        # Scroll down multiple times to trigger lazy loading
        scroll_attempts = 0
        max_scroll_attempts = 5
        last_count = initial_count
        
        while scroll_attempts < max_scroll_attempts:
            if table_container:
                # Scroll within the specific table container
                await page.evaluate("""
                    (container) => {
                        if (container) {
                            container.scrollTop = container.scrollHeight;
                        } else {
                            window.scrollTo(0, document.body.scrollHeight);
                        }
                    }
                """, table_container)
            else:
                # Fallback: scroll the main page
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            await asyncio.sleep(2)  # Wait for content to load
            
            # Check if new content was loaded
            current_rows = await page.query_selector_all('div[class*="gridViewStyles__HorizontalCell"]')
            current_count = len(current_rows)
            
            self.logger.info(f"Project scroll attempt {scroll_attempts + 1}: Found {current_count} project rows")
            
            # If no new rows were loaded, we've reached the end
            if current_count == last_count:
                self.logger.info("No new project rows loaded, stopping scroll")
                break
            
            last_count = current_count
            scroll_attempts += 1
        
        # Final scroll to top to ensure we can see all content
        if table_container:
            await page.evaluate("(container) => container.scrollTop = 0", table_container)
        else:
            await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        
        final_rows = await page.query_selector_all('div[class*="gridViewStyles__HorizontalCell"]')
        final_count = len(final_rows)
        self.logger.info(f"Final project rows found after scrolling: {final_count}")
        
        return final_count
    
    async def scrape_employee_profile(self, page, profile_url: str, employee_name: str, office_location: str = "") -> Optional[EmployeeData]:
        """
        Scrape detailed information from an individual employee profile page.
        
        Args:
            page: Playwright page object
            profile_url: URL of the employee profile
            employee_name: Name of the employee
            
        Returns:
            EmployeeData object or None if failed
        """
        try:
            self.logger.info(f"  Scraping profile: {employee_name}")
            
            # Convert relative URL to absolute URL if needed
            if profile_url.startswith('/'):
                profile_url = f"https://ei.ennead.com{profile_url}"
            elif not profile_url.startswith('http'):
                profile_url = f"https://ei.ennead.com/{profile_url}"
            
            self.logger.info(f"    Navigating to: {profile_url}")
            
            # Navigate to the profile page
            try:
                await page.goto(profile_url, wait_until='networkidle')
                await asyncio.sleep(2)
            except Exception as nav_error:
                self.logger.error(f"    [ERROR] Navigation failed: {nav_error}")
                return None
            
            # Check if we're actually on a profile page or redirected back
            current_url = page.url
            self.logger.info(f"    Current URL after navigation: {current_url}")
            
            if 'employee/' not in current_url:
                self.logger.warning(f"    [WARNING] Redirected to: {current_url}")
                return None
            
            # Capture DOM for debugging if enabled
            safe_name = employee_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            await self._capture_dom_for_debug(page, f"profile_{safe_name}", f"Employee profile: {employee_name}")
            
            # Get page content
            content = await page.content()
            text_content = await page.evaluate("document.body.innerText")
            
            # Create employee object
            employee = EmployeeData()
            employee.real_name = employee_name
            employee.profile_url = profile_url
            employee.profile_id = profile_url.split('/')[-1] if '/' in profile_url else f"employee_{employee_name.replace(' ', '_')}"
            employee.office_location = office_location
            
            # Extract profile image
            try:
                profile_img = await page.query_selector('img.EntityHeader__HeaderPhoto-sc-1yar8fm-1')
                if profile_img:
                    src = await profile_img.get_attribute('src')
                    if src:
                        if src.startswith('/'):
                            src = f"https://ei.ennead.com{src}"
                        employee.image_url = src
                        
                        # Download the image if enabled
                        if self.config.DOWNLOAD_IMAGES:
                            try:
                                local_path = await self.image_downloader.download_image(src, employee_name, page)
                                if local_path:
                                    employee.image_local_path = local_path
                                    self.logger.info(f"Downloaded image for {employee_name}: {local_path}")
                                else:
                                    self.logger.warning(f"Failed to download image for {employee_name}")
                            except Exception as e:
                                self.logger.error(f"Error downloading image for {employee_name}: {e}")
            except:
                pass
            
            # Extract position/title from header - try multiple selectors
            try:
                # Try the original selector first
                title_element = await page.query_selector('span[data-kafieldname="title"]')
                if title_element:
                    employee.position = await title_element.text_content()
                else:
                    # Try to find "Project Coordinator" or similar job titles directly in the page text
                    page_text = await page.text_content('body')
                    if page_text:
                        # Look for common job title patterns
                        job_title_patterns = [
                            r'Project Coordinator',
                            r'Project Manager',
                            r'Architect',
                            r'Designer',
                            r'Engineer',
                            r'Director',
                            r'Manager',
                            r'Coordinator',
                            r'Specialist',
                            r'Analyst',
                            r'Consultant',
                            r'Associate',
                            r'Senior',
                            r'Principal',
                            r'Lead',
                            r'Head of',
                            r'VP',
                            r'Vice President'
                        ]
                        
                        for pattern in job_title_patterns:
                            matches = re.findall(pattern, page_text, re.IGNORECASE)
                            if matches:
                                # Take the first match that looks like a job title
                                for match in matches:
                                    if len(match) > 3 and len(match) < 50:
                                        employee.position = match
                                        self.logger.info(f"    Found position from text pattern '{pattern}': {employee.position}")
                                        break
                                if employee.position:
                                    break
                    
                    # If we still don't have a position, try alternative selectors
                    if not employee.position:
                        position_selectors = [
                            'h2', 'h3', 'h4',  # Common heading tags
                            '.position', '.title', '.job-title', '.employee-title',
                            'span[class*="title"]', 'div[class*="title"]',
                            'span[class*="position"]', 'div[class*="position"]',
                            'span[class*="job"]', 'div[class*="job"]',
                            # Look for text that appears after the name
                            'div:has(h1, h2, h3) + div', 'span:has(h1, h2, h3) + span',
                            # Generic text selectors near the name
                            'div[class*="header"] div:not(:has(img))',
                            'div[class*="profile"] div:not(:has(img))',
                            'div[class*="employee"] div:not(:has(img))'
                        ]
                        
                        for selector in position_selectors:
                            try:
                                elements = await page.query_selector_all(selector)
                                for element in elements:
                                    text = await element.text_content()
                                    if text and text.strip() and len(text.strip()) > 2 and len(text.strip()) < 100:
                                        # Check if this looks like a job title (not a name, not too long)
                                        if not text.strip().lower().startswith(('mr.', 'ms.', 'dr.', 'prof.')):
                                            # Filter out common non-job-title text patterns
                                            text_lower = text.strip().lower()
                                            if any(pattern in text_lower for pattern in [
                                                'the basics', 'years with firm', 'education', 'institution', 
                                                'degree', 'specialty', 'contact info', 'email', 'phone',
                                                'teams', 'recent posts', 'projects', 'personal bio',
                                                'i was born', 'i still live', 'i foster', 'i do'
                                            ]):
                                                continue
                                            
                                            # Prioritize shorter, more likely job titles
                                            if len(text.strip()) < 50 and not text.strip().startswith("I'm"):
                                                employee.position = text.strip()
                                                self.logger.info(f"    Found position with selector '{selector}': {employee.position}")
                                                break
                                            # If we haven't found anything yet, take this as fallback
                                            elif not employee.position:
                                                employee.position = text.strip()
                                                self.logger.info(f"    Found position (fallback) with selector '{selector}': {employee.position}")
                                if employee.position:
                                    break
                            except:
                                continue
            except Exception as e:
                self.logger.warning(f"    Error extracting position: {e}")
                pass
            
            # Extract years with firm
            try:
                years_element = await page.query_selector('div[data-kafieldname="hireDateForTenure"] .EntityFields__InfoFieldValue-sc-129sxys-5')
                if years_element:
                    years_text = await years_element.text_content()
                    if years_text and years_text.isdigit():
                        employee.years_with_firm = int(years_text)
            except:
                pass
            
            # Extract memberships
            try:
                membership_pills = await page.query_selector_all('div[data-kagridname="grid_3"] .EntityFields__GridPillContent-sc-129sxys-3')
                for pill in membership_pills:
                    membership_text = await pill.text_content()
                    if membership_text and membership_text.strip():
                        employee.memberships.append(membership_text.strip())
            except:
                pass
            
            # Extract education
            try:
                education_rows = await page.query_selector_all('div[data-kagridname="employeeDegrees"] .EntityFields__InfoFieldValue-sc-129sxys-5')
                if education_rows:
                    # Group by rows of 3 (institution, degree, specialty)
                    for i in range(0, len(education_rows), 3):
                        if i + 2 < len(education_rows):
                            institution = await education_rows[i].text_content()
                            degree = await education_rows[i + 1].text_content()
                            specialty = await education_rows[i + 2].text_content()
                            
                            if institution and institution.strip():
                                employee.education.append({
                                    'institution': institution.strip(),
                                    'degree': degree.strip() if degree else '',
                                    'specialty': specialty.strip() if specialty else ''
                                })
            except:
                pass
            
            # Extract licenses
            try:
                license_rows = await page.query_selector_all('div[data-kagridname="employeeRegistrations"] .EntityFields__InfoFieldValue-sc-129sxys-5')
                if license_rows:
                    # Group by rows of 4 (license, state, number, earned)
                    for i in range(0, len(license_rows), 4):
                        if i + 3 < len(license_rows):
                            license_name = await license_rows[i].text_content()
                            state = await license_rows[i + 1].text_content()
                            number = await license_rows[i + 2].text_content()
                            earned = await license_rows[i + 3].text_content()
                            
                            if license_name and license_name.strip():
                                employee.licenses.append({
                                    'license': license_name.strip(),
                                    'state': state.strip() if state else '',
                                    'number': number.strip() if number else '',
                                    'earned': earned.strip() if earned else ''
                                })
            except:
                pass
            
            # Extract contact information
            try:
                # Email
                email_link = await page.query_selector('a[href^="mailto:"]')
                if email_link:
                    href = await email_link.get_attribute('href')
                    if href:
                        employee.email = href.replace('mailto:', '')
                
                # Work phone
                work_phone_link = await page.query_selector('a[href^="tel:"]')
                if work_phone_link:
                    href = await work_phone_link.get_attribute('href')
                    if href:
                        employee.phone = href.replace('tel:', '')
                
                # Mobile phone (second tel link)
                mobile_phone_links = await page.query_selector_all('a[href^="tel:"]')
                if len(mobile_phone_links) > 1:
                    href = await mobile_phone_links[1].get_attribute('href')
                    if href:
                        employee.mobile = href.replace('tel:', '')
                
                # Teams URL
                teams_link = await page.query_selector('a[href*="teams.microsoft.com"]')
                if teams_link:
                    employee.teams_url = await teams_link.get_attribute('href')
            except:
                pass
            
            # Extract projects - handle both "Show All" and side panel cases
            try:
                # First, try to find the "Show All" link in the Projects section
                show_all_link = await page.query_selector('a[href*="/employee-projects/"]')
                
                if show_all_link:
                    # Case 1: Employee has "Show All" link - navigate to dedicated projects page
                    self.logger.info(f"Found 'Show All' link for {employee_name}, navigating to projects page")
                    projects_url = await show_all_link.get_attribute('href')
                    if projects_url:
                        if projects_url.startswith('/'):
                            projects_url = f"https://ei.ennead.com{projects_url}"
                        
                        # Navigate to the projects page
                        await page.goto(projects_url, wait_until='networkidle')
                        await asyncio.sleep(2)
                        
                        # Scroll down to load all project rows (in case of lazy loading)
                        await self._scroll_to_load_all_projects(page)
                        
                        # Extract project data from the table with improved parsing
                        await self._extract_projects_from_table(page, employee)
                        
                        # Navigate back to the profile page
                        await page.goto(profile_url, wait_until='networkidle')
                        await asyncio.sleep(2)
                else:
                    # Case 2: No "Show All" link - try to expand projects section and extract from side panel
                    self.logger.info(f"No 'Show All' link for {employee_name}, trying to expand projects section")
                    
                    # Try to find and click on the projects section to expand it
                    await self._try_expand_projects_section(page, employee_name)
                    
                    # Use improved project extraction for side panel
                    await self._extract_projects_from_side_panel(page, employee)
                    
                    if not employee.projects:
                        self.logger.warning(f"No projects found for {employee_name} in side panel")
                        
            except Exception as e:
                self.logger.error(f"Error extracting projects for {employee_name}: {e}")
                pass
            
            # Extract recent posts
            try:
                post_links = await page.query_selector_all('a[href*="/post/"] .ListPost__Title-sc-1vvfvm-1')
                for link in post_links:
                    text = await link.text_content()
                    if text and text.strip():
                        employee.recent_posts.append({
                            'title': text.strip(),
                            'url': ''  # Could extract URL if needed
                        })
            except:
                pass
            
            
            self.logger.info(f"    [SUCCESS] Found: {employee.email or 'No email'} | {employee.phone or 'No phone'} | {employee.position or 'No position'}")
            
            return employee
            
        except Exception as e:
            self.logger.error(f"    [ERROR] Error scraping profile: {e}")
            return None
    
    async def scrape_all_employees(self) -> List[EmployeeData]:
        """
        Scrape all employees from the directory.
        
        Returns:
            List of EmployeeData objects
        """
        
        try:
            # Initialize Playwright without timeout protection
            self.logger.info("[START] Initializing Playwright browser...")
            playwright = await async_playwright().start()
            
            self.logger.info("[START] Launching browser...")
            browser = await playwright.chromium.launch(
                headless=self.config.HEADLESS,
                channel='msedge',
                args=self.config.BROWSER_ARGS
            )
            self.logger.info("[START] Creating browser context...")
            context = await browser.new_context(
                viewport={'width': self.config.VIEWPORT_WIDTH, 'height': self.config.VIEWPORT_HEIGHT},
                user_agent=self.config.USER_AGENT
            )
            
            self.logger.info("[START] Creating new page...")
            page = await context.new_page()
            page.set_default_timeout(self.config.TIMEOUT)
            
            # Login and get to main page without timeout
            self.logger.info("[START] Attempting login...")
            login_success = await self.auto_login.login(page, self.config.BASE_URL)
            if not login_success:
                self.logger.error("❌ Failed to login")
                await browser.close()
                return []
            
            # Wait for page to load completely
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Capture DOM for debugging if enabled
            await self._capture_dom_for_debug(page, "main_directory", "Main employee directory page")
            
            # Find employee profile links
            employee_links = await self.find_employee_profile_links(page)
            
            if not employee_links:
                self.logger.warning("No employee profile links found!")
                return []
            
            self.logger.info(f"Scraping {len(employee_links)} employee profiles...")
            
            # Scrape each employee profile
            employees = []
            for i, (profile_url, employee_name, office_location) in enumerate(employee_links, 1):
                self.logger.info(f"[{i}/{len(employee_links)}] Processing: {employee_name}")
                
                employee = await self.scrape_employee_profile(page, profile_url, employee_name, office_location)
                if employee:
                    employees.append(employee)
                
                # Add small delay to be respectful
                await asyncio.sleep(1)
            
            # Scrape seating chart data and merge with employee data BEFORE closing browser
            print("DEBUG: Starting seating chart scraping section")
            try:
                self.logger.info("Scraping seating chart data...")
                print(f"DEBUG: About to call seating chart scraper with {len(employees)} existing employees")
                # Pass the authenticated page to the seating chart scraper
                seating_data = await self.seating_scraper.scrape_all_employees(page)
                print(f"DEBUG: Seating chart scraper returned {len(seating_data) if seating_data else 0} employees")
                
                if seating_data:
                    self.logger.info(f"Found {len(seating_data)} employees in seating chart")
                    print(f"DEBUG: Sample seating data: {[f'{emp.name}: {emp.seat}' for emp in seating_data[:3]]}")
                    print(f"DEBUG: Main employee names: {[emp.real_name for emp in employees]}")
                    print(f"DEBUG: Sample seating names: {[emp.name for emp in seating_data[:5]]}")
                    # Merge seating data with employee data
                    employees = self.data_merger.merge_employee_data(employees, seating_data)
                    print(f"DEBUG: After merging, {len([e for e in employees if e.seat_assignment])} employees have seat assignments")
                    self.logger.info("Successfully merged seating chart data")
                else:
                    self.logger.warning("No seating chart data found")
                    print("DEBUG: No seating chart data found")
                    
            except Exception as e:
                self.logger.error(f"Error scraping seating chart data: {e}")
                print(f"DEBUG: Error in seating chart scraping: {e}")
                # Continue without seating data rather than failing completely
            
            # Clean up browser resources
            self.logger.info("[CLEANUP] Cleaning up browser resources...")
            await browser.close()
            await playwright.stop()
            
            self.logger.info(f"✅ Successfully scraped {len(employees)} employees")
            
            return employees
            
        except Exception as e:
            self.logger.error(f"❌ Error during scraping: {e}")
            # Try to clean up browser if it exists
            try:
                if 'browser' in locals():
                    await browser.close()
                if 'playwright' in locals():
                    await playwright.stop()
            except:
                pass
            return []
    
    def save_to_json(self, employees: List[EmployeeData], filename: Optional[str] = None) -> str:
        """
        Save employee data to JSON file.
        
        Args:
            employees: List of EmployeeData objects
            filename: Output filename (optional)
            
        Returns:
            Path to the saved file
        """
        if not filename:
            filename = self.config.JSON_FILENAME
            # Add debug suffix if in debug mode
            if self.config.DEBUG_MODE and filename:
                name_parts = filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    filename = f"{name_parts[0]}_debug.{name_parts[1]}"
                else:
                    filename = f"{filename}_debug"
        
        output_path = self.config.get_output_path(filename)
        output_path.parent.mkdir(exist_ok=True)
        
        # Convert to dictionaries
        employees_data = [emp.to_dict() for emp in employees]
        
        # Create output data structure
        output_data = {
            "metadata": {
                "total_employees": len(employees),
                "scraped_at": employees[0].scraped_at if employees else None,
                "source_url": self.config.BASE_URL,
                "download_images": self.config.DOWNLOAD_IMAGES,
                "scraping_method": "complete_profile_extraction",
                "debug_mode": self.config.DEBUG_MODE,
                "debug_max_employees": self.config.DEBUG_MAX_EMPLOYEES if self.config.DEBUG_MODE else None
            },
            "employees": employees_data,
            "extraction_stats": {
                "employees_with_emails": len([e for e in employees if e.email]),
                "employees_with_phones": len([e for e in employees if e.phone]),
                "employees_with_bios": len([e for e in employees if e.bio]),
                "employees_with_positions": len([e for e in employees if e.position]),
                "employees_with_departments": len([e for e in employees if e.department]),
                "employees_with_images": len([e for e in employees if e.image_url]),
                "employees_with_office_locations": len([e for e in employees if e.office_location]),
                "office_location_breakdown": self._get_office_location_breakdown(employees)
            }
        }
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Data saved to: {output_path}")
        
        # Also save individual employee files
        if self.config.INDIVIDUAL_FILES:
            individual_dir = output_path.parent / "individual_employees"
            individual_dir.mkdir(exist_ok=True)
            
            for employee in employees:
                if employee.real_name:
                    safe_name = employee.real_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                    individual_file = individual_dir / f"{safe_name}.json"
                    with open(individual_file, 'w', encoding='utf-8') as f:
                        json.dump(employee.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Individual employee files saved to: {individual_dir}")
        
        return str(output_path)
    
    def _get_office_location_breakdown(self, employees: List[EmployeeData]) -> Dict[str, int]:
        """
        Get a breakdown of employees by office location.
        
        Args:
            employees: List of EmployeeData objects
            
        Returns:
            Dictionary mapping office locations to employee counts
        """
        location_counts = {}
        for employee in employees:
            if employee.office_location:
                location = employee.office_location.strip()
                if location:
                    location_counts[location] = location_counts.get(location, 0) + 1
        return location_counts
    
    async def _capture_dom_for_debug(self, page, filename_prefix: str, description: str = ""):
        """
        Capture DOM and screenshot for debugging purposes.
        
        Args:
            page: Playwright page object
            filename_prefix: Prefix for the saved files
            description: Description of what is being captured
        """
        if not self.config.DEBUG_MODE or not self.config.DEBUG_DOM_CAPTURE:
            return
        
        try:
            debug_dir = self.config.get_debug_output_path()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Capture DOM
            dom_content = await page.content()
            dom_filename = f"{filename_prefix}_{timestamp}.html"
            dom_path = debug_dir / "dom_captures" / dom_filename
            
            with open(dom_path, 'w', encoding='utf-8') as f:
                f.write(dom_content)
            
            # Capture screenshot
            screenshot_filename = f"{filename_prefix}_{timestamp}.png"
            screenshot_path = debug_dir / "screenshots" / screenshot_filename
            
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            self.logger.info(f"DEBUG: Captured DOM and screenshot for {description}")
            self.logger.info(f"  DOM: {dom_path}")
            self.logger.info(f"  Screenshot: {screenshot_path}")
            
        except Exception as e:
            self.logger.error(f"Error capturing debug data: {e}")
    
    def generate_html_report(self, json_file_path: Optional[str] = None) -> str:
        """
        Generate a beautiful HTML report from the scraped employee data.
        
        Args:
            json_file_path: Path to the JSON file (optional, will use default if not provided)
            
        Returns:
            Path to the generated HTML file
        """
        if json_file_path is None:
            json_file_path = str(self.config.get_output_path())
        
        self.logger.info("Generating HTML report...")
        
        try:
            html_file_path = self.html_generator.generate_from_json_file(json_file_path)
            self.logger.info(f"HTML report generated successfully: {html_file_path}")
            return html_file_path
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            raise
