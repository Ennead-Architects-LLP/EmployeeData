"""
Seating Chart Scraper for ennead SeatingChart website.

This module scrapes department and seat information from the ennead SeatingChart
website (https://eacheckin.azurewebsites.net/) to enhance employee data.
"""

import asyncio
import logging
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import time
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page, BrowserContext


@dataclass
class SeatingChartData:
    """Data class for seating chart information."""
    name: str
    seat: Optional[str] = None
    department: Optional[str] = None
    office_location: Optional[str] = None
    profile_image_url: Optional[str] = None
    scraped_at: Optional[str] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class SeatingChartScraper:
    """Scraper for ennead SeatingChart website."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000, debug_mode: bool = False):
        """
        Initialize the seating chart scraper.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Page load timeout in milliseconds
            debug_mode: Whether to enable debug mode with DOM capture
        """
        self.headless = headless
        self.timeout = timeout
        self.base_url = "https://eacheckin.azurewebsites.net/"
        self.logger = logging.getLogger(__name__)
        self.debug_mode = debug_mode
        self.working_selectors = {
            'employee_elements': [],
            'name_selectors': [],
            'seat_selectors': [],
            'department_selectors': []
        }
        
        # Setup debug directories if in debug mode
        if self.debug_mode:
            self._setup_debug_directories()
    
    def _setup_debug_directories(self):
        """Setup debug directories for DOM capture and screenshots."""
        from .config import ScraperConfig
        cfg = ScraperConfig.from_env()
        self.debug_dir = Path(cfg.OUTPUT_DIR) / "debug" / "seating_chart"
        self.dom_dir = self.debug_dir / "dom_captures"
        self.screenshot_dir = self.debug_dir / "screenshots"
        
        self.dom_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    async def _capture_dom_for_debug(self, page: Page, filename: str, description: str = ""):
        """Capture DOM and screenshot for debugging."""
        if not self.debug_mode:
            return
        
        try:
            # Capture DOM
            dom_content = await page.content()
            dom_file = self.dom_dir / f"{filename}.html"
            with open(dom_file, 'w', encoding='utf-8') as f:
                f.write(f"<!-- {description} -->\n")
                f.write(dom_content)
            
            # Capture screenshot
            screenshot_file = self.screenshot_dir / f"{filename}.png"
            await page.screenshot(path=str(screenshot_file))
            
            self.logger.info(f"Debug capture saved: {dom_file} and {screenshot_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to capture debug info: {str(e)}")
    
    def _track_working_selector(self, selector_type: str, selector: str, count: int):
        """Track working selectors for future improvements."""
        if count > 0:
            self.working_selectors[selector_type].append({
                'selector': selector,
                'count': count,
                'timestamp': datetime.now().isoformat()
            })
            self.logger.info(f"Working selector [{selector_type}]: {selector} found {count} elements")
        else:
            self.logger.debug(f"Failed selector [{selector_type}]: {selector}")
    
    def _save_selector_report(self):
        """Save a report of working selectors."""
        if not self.debug_mode:
            return
        
        report_file = self.debug_dir / "selector_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.working_selectors, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Selector report saved: {report_file}")
        
    async def scrape_all_employees(self, page: Optional[Page] = None) -> List[SeatingChartData]:
        """
        Scrape all employee data from the seating chart.
        
        Args:
            page: Optional existing page to use (for authenticated sessions)
        
        Returns:
            List of SeatingChartData objects
        """
        if page:
            # Use existing authenticated page
            self.logger.info("Using existing authenticated page for seating chart")
            try:
                # Navigate to the seating chart using existing page
                self.logger.info(f"Navigating to {self.base_url}")
                await page.goto(self.base_url, wait_until='networkidle')
                
                # Capture initial page load
                await self._capture_dom_for_debug(page, "initial_load", "Initial page load after navigation")
                
                # Wait for the page to load (check for any text containing "ennead")
                try:
                    await page.wait_for_selector('text=ennead', timeout=10000)
                except:
                    # If specific selector fails, just wait a bit for page to load
                    await asyncio.sleep(2)
                
                # Capture after waiting for content
                await self._capture_dom_for_debug(page, "after_wait", "Page after waiting for ennead text")
                
                # Get all employee data
                employees = await self._extract_employee_data(page)
                
                # Save selector report
                self._save_selector_report()
                
                self.logger.info(f"Successfully scraped {len(employees)} employees from seating chart")
                return employees
                
            except Exception as e:
                self.logger.error(f"Error scraping seating chart with existing page: {str(e)}")
                return []
        else:
            # Create new browser session (fallback)
            try:
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(
                    headless=self.headless,
                    channel='msedge'
                )
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                try:
                    page = await context.new_page()
                    page.set_default_timeout(self.timeout)
                    
                    # Navigate to the seating chart
                    self.logger.info(f"Navigating to {self.base_url}")
                    await page.goto(self.base_url, wait_until='networkidle')
                    
                    # Capture initial page load
                    await self._capture_dom_for_debug(page, "initial_load", "Initial page load after navigation")
                    
                    # Wait for the page to load (check for any text containing "ennead")
                    try:
                        await page.wait_for_selector('text=ennead', timeout=10000)
                    except:
                        # If specific selector fails, just wait a bit for page to load
                        await asyncio.sleep(2)
                    
                    # Capture after waiting for content
                    await self._capture_dom_for_debug(page, "after_wait", "Page after waiting for ennead text")
                    
                    # Get all employee data
                    employees = await self._extract_employee_data(page)
                    
                    # Save selector report
                    self._save_selector_report()
                    
                    self.logger.info(f"Successfully scraped {len(employees)} employees from seating chart")
                    return employees
                    
                except Exception as e:
                    self.logger.error(f"Error scraping seating chart: {str(e)}")
                    raise
                finally:
                    await browser.close()
                    await playwright.stop()
            except Exception as e:
                self.logger.error(f"Failed to initialize playwright: {str(e)}")
                return []
    
    async def _extract_employee_data(self, page: Page) -> List[SeatingChartData]:
        """
        Extract employee data from the current page.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of SeatingChartData objects
        """
        employees = []
        
        try:
            # Wait a bit for the page to fully load
            await asyncio.sleep(3)
            
            # Capture DOM before extraction
            await self._capture_dom_for_debug(page, "before_extraction", "Page before employee data extraction")
            
            # Test various selectors to find employee elements
            employee_selectors = [
                # SVG circle elements (primary seating chart data)
                'circle.seatCircle',
                'circle[firstName]',
                'circle[lastName]',
                'circle[seat]',
                # Common table/list selectors (fallback)
                'tr',
                '.row',
                '[class*="row"]',
                '[role="row"]',
                # Employee-specific selectors
                '[data-testid*="employee"]',
                '[class*="employee"]',
                '[class*="person"]',
                '[class*="staff"]',
                '[class*="member"]',
                # Generic container selectors
                'div[class*="item"]',
                'div[class*="card"]',
                'div[class*="entry"]',
                'li',
                'div[class*="list"] > div',
                # More specific patterns
                'div:has(> div:has-text("EA"))',
                'div:has(> div:has-text("EF"))',
                'div:has(> div:has-text("Technical"))',
                'div:has(> div:has-text("Marketing"))'
            ]
            
            best_selector = None
            best_count = 0
            
            # Test each selector and track results
            for selector in employee_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    count = len(elements)
                    self._track_working_selector('employee_elements', selector, count)
                    
                    if count > best_count and count > 5:  # Reasonable number of employees
                        best_selector = selector
                        best_count = count
                        
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {str(e)}")
                    continue
            
            self.logger.info(f"Best employee selector: {best_selector} (found {best_count} elements)")
            
            # Try to extract data using the best selector
            if best_selector:
                employees = await self._extract_from_best_selector(page, best_selector)
            
            # If we didn't find many employees, try regex extraction
            if len(employees) < 10:
                self.logger.info("Trying regex extraction method")
                employees = await self._extract_with_regex(page)
            
            # If still not enough, try table structure extraction
            if len(employees) < 10:
                self.logger.info("Trying table structure extraction method")
                employees = await self._extract_from_table_structure(page)
            
            # Capture final DOM
            await self._capture_dom_for_debug(page, "after_extraction", f"Page after extraction - found {len(employees)} employees")
            
            self.logger.info(f"Successfully extracted {len(employees)} employees")
            
        except Exception as e:
            self.logger.error(f"Error in _extract_employee_data: {str(e)}")
            # Try fallback extraction
            return await self._fallback_extraction(page)
        
        return employees
    
    async def _extract_from_best_selector(self, page: Page, selector: str) -> List[SeatingChartData]:
        """
        Extract employee data using the best working selector.
        
        Args:
            page: Playwright page object
            selector: The best selector found
            
        Returns:
            List of SeatingChartData objects
        """
        employees = []
        
        try:
            elements = await page.query_selector_all(selector)
            self.logger.info(f"Extracting from {len(elements)} elements using selector: {selector}")
            
            for i, element in enumerate(elements):
                try:
                    employee_data = await self._extract_single_employee_advanced(element, page)
                    if employee_data and employee_data.name:
                        employees.append(employee_data)
                        
                    # Add small delay to avoid overwhelming the page
                    if i % 10 == 0:
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    self.logger.debug(f"Error extracting employee {i}: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error in _extract_from_best_selector: {str(e)}")
        
        return employees
    
    async def _extract_with_regex(self, page: Page) -> List[SeatingChartData]:
        """
        Extract employee data using regex patterns on page content.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of SeatingChartData objects
        """
        employees = []
        
        try:
            # Get page content
            content = await page.content()
            
            # Look for patterns in the HTML that might indicate employee data
            import re
            
            # Extract names (look for patterns that look like names)
            name_patterns = re.findall(r'<[^>]*>([A-Z][a-z]+ [A-Z][a-z]+)</[^>]*>', content)
            
            # Extract seat codes (alphanumeric codes like EA02, EF01, etc.)
            seat_patterns = re.findall(r'(EA\d+|EF\d+|EG\d+|SE\d+|ED\d+|WB\d+|WA\d+|SD\d+|WD\d+|SF\d+|SC\d+)', content)
            
            # Extract departments
            dept_patterns = re.findall(r'(Technical|Marketing|Design|Management|Administration|Resource)', content)
            
            self.logger.info(f"Regex found {len(name_patterns)} name patterns, {len(seat_patterns)} seat patterns, {len(dept_patterns)} department patterns")
            
            # Track regex results
            self._track_working_selector('name_selectors', 'regex_name_pattern', len(name_patterns))
            self._track_working_selector('seat_selectors', 'regex_seat_pattern', len(seat_patterns))
            self._track_working_selector('department_selectors', 'regex_dept_pattern', len(dept_patterns))
            
            # Try to match names with seats and departments
            for i, name in enumerate(name_patterns[:100]):  # Limit to reasonable number
                seat = seat_patterns[i] if i < len(seat_patterns) else None
                department = dept_patterns[i] if i < len(dept_patterns) else None
                
                # Skip if name is too short or looks like a common word
                if len(name) < 5 or name.lower() in ['new york', 'los angeles', 'shanghai', 'check in']:
                    continue
                
                employees.append(SeatingChartData(
                    name=name,
                    seat=seat,
                    department=department
                ))
            
        except Exception as e:
            self.logger.error(f"Error in _extract_with_regex: {str(e)}")
        
        return employees
    
    async def _extract_single_employee_advanced(self, element, page: Page) -> Optional[SeatingChartData]:
        """
        Advanced extraction from a single employee element with comprehensive selector testing.
        
        Args:
            element: Playwright element handle
            page: Playwright page object
            
        Returns:
            SeatingChartData object or None
        """
        try:
            # Check if this is an SVG circle element (primary seating chart data)
            tag_name = await element.evaluate('el => el.tagName')
            if tag_name.lower() == 'circle':
                # Extract data from SVG circle attributes
                first_name = await element.get_attribute('firstName')
                last_name = await element.get_attribute('lastName')
                seat = await element.get_attribute('seat')
                ext = await element.get_attribute('ext')
                
                if first_name and last_name:
                    name = f"{first_name} {last_name}"
                    self._track_working_selector('name_selectors', 'svg_circle_attributes', 1)
                    
                    # Try to determine department from seat code
                    department = None
                    if seat:
                        # Map seat codes to departments (this might need adjustment based on actual data)
                        if seat.startswith(('EA', 'EF', 'EG')):
                            department = 'Technical'
                        elif seat.startswith(('WB', 'WA')):
                            department = 'Marketing'
                        elif seat.startswith(('SE', 'SD', 'SF', 'SC')):
                            department = 'Design'
                        elif seat.startswith('ED'):
                            department = 'Management'
                        
                        self._track_working_selector('seat_selectors', f'svg_seat_{seat[:2]}', 1)
                        self._track_working_selector('department_selectors', f'svg_dept_{department}', 1)
                    
                    return SeatingChartData(
                        name=name,
                        seat=seat,
                        department=department
                    )
            
            # Fallback to text-based extraction for other element types
            text_content = await element.inner_text()
            if not text_content or len(text_content.strip()) < 3:
                return None
            
            # Test various selectors for names within this element
            name_selectors = [
                'a[href*="employee"]',
                '.name',
                '[class*="name"]',
                'strong',
                'b',
                'h3',
                'h4',
                'span[class*="title"]',
                'div[class*="title"]'
            ]
            
            name = None
            for selector in name_selectors:
                try:
                    name_element = await element.query_selector(selector)
                    if name_element:
                        name_text = await name_element.inner_text()
                        if name_text and len(name_text.strip()) > 2:
                            name = name_text.strip()
                            self._track_working_selector('name_selectors', selector, 1)
                            break
                except:
                    continue
            
            # If no name found in specific elements, try to parse from text content
            if not name:
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                for line in lines:
                    # Look for lines that look like names (contain letters, not just numbers/symbols)
                    if any(c.isalpha() for c in line) and len(line) > 2 and not line.startswith(('EA', 'EF', 'EG', 'SE', 'ED', 'WB', 'WA', 'SD', 'WD', 'SF', 'SC')):
                        name = line
                        break
            
            # Look for seat information (alphanumeric codes like EA02, EF01, etc.)
            seat_patterns = ['EA', 'EF', 'EG', 'SE', 'ED', 'WB', 'WA', 'SD', 'WD', 'SF', 'SC']
            seat = None
            for pattern in seat_patterns:
                if pattern in text_content:
                    # Extract the full seat code
                    import re
                    seat_match = re.search(rf'{pattern}\d+', text_content)
                    if seat_match:
                        seat = seat_match.group()
                        self._track_working_selector('seat_selectors', f'regex_{pattern}', 1)
                        break
            
            # Look for department information
            department_keywords = ['Technical', 'Marketing', 'Design', 'Management', 'Administration', 'Resource']
            department = None
            for keyword in department_keywords:
                if keyword in text_content:
                    department = keyword
                    self._track_working_selector('department_selectors', f'text_{keyword}', 1)
                    break
            
            if name:
                return SeatingChartData(
                    name=name,
                    seat=seat,
                    department=department
                )
            
        except Exception as e:
            self.logger.debug(f"Error extracting single employee: {str(e)}")
        
        return None
    
    async def _extract_from_table_structure(self, page: Page) -> List[SeatingChartData]:
        """
        Extract employee data from table-like structure.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of SeatingChartData objects
        """
        employees = []
        
        try:
            # Try to find table rows or similar structures
            table_selectors = [
                'tr',
                '.row',
                '[class*="row"]',
                '[role="row"]',
                'div[class*="employee"]',
                'div[class*="person"]'
            ]
            
            for selector in table_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 5:
                        self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        
                        for element in elements:
                            try:
                                text_content = await element.inner_text()
                                if text_content and len(text_content.strip()) > 10:
                                    # Try to parse the text content
                                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                                    
                                    # Look for patterns that might be employee data
                                    name = None
                                    seat = None
                                    department = None
                                    
                                    for line in lines:
                                        # Look for names (capitalized words)
                                        if not name and any(c.isalpha() for c in line) and len(line) > 5 and line[0].isupper():
                                            name = line
                                        
                                        # Look for seat codes
                                        if not seat and any(pattern in line for pattern in ['EA', 'EF', 'EG', 'SE', 'ED', 'WB', 'WA', 'SD', 'WD', 'SF', 'SC']):
                                            import re
                                            seat_match = re.search(r'(EA\d+|EF\d+|EG\d+|SE\d+|ED\d+|WB\d+|WA\d+|SD\d+|WD\d+|SF\d+|SC\d+)', line)
                                            if seat_match:
                                                seat = seat_match.group()
                                        
                                        # Look for departments
                                        if not department and any(dept in line for dept in ['Technical', 'Marketing', 'Design', 'Management', 'Administration', 'Resource']):
                                            department = line
                                    
                                    if name and len(name) > 5:
                                        employees.append(SeatingChartData(
                                            name=name,
                                            seat=seat,
                                            department=department
                                        ))
                            except Exception as e:
                                self.logger.debug(f"Error processing element: {str(e)}")
                                continue
                                        
                        if employees:
                            break
                            
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error in _extract_from_table_structure: {str(e)}")
        
        return employees
    
    async def _fallback_extraction(self, page: Page) -> List[SeatingChartData]:
        """
        Fallback extraction method when standard selectors fail.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of SeatingChartData objects
        """
        employees = []
        
        try:
            # Get all text content from the page
            content = await page.content()
            
            # Try to find employee data in the HTML
            import re
            
            # Look for patterns that might indicate employee data
            # This is a more aggressive approach for when the page structure is unclear
            
            # Look for names (sequences of words that could be names)
            name_patterns = re.findall(r'<[^>]*>([A-Z][a-z]+ [A-Z][a-z]+)</[^>]*>', content)
            
            # Look for seat codes
            seat_patterns = re.findall(r'(EA\d+|EF\d+|EG\d+|SE\d+|ED\d+|WB\d+|WA\d+|SD\d+|WD\d+|SF\d+|SC\d+)', content)
            
            # Look for departments
            dept_patterns = re.findall(r'(Technical|Marketing|Design|Management|Administration|Resource)', content)
            
            # Try to match names with seats and departments
            for i, name in enumerate(name_patterns[:100]):  # Limit to reasonable number
                seat = seat_patterns[i] if i < len(seat_patterns) else None
                department = dept_patterns[i] if i < len(dept_patterns) else None
                
                employees.append(SeatingChartData(
                    name=name,
                    seat=seat,
                    department=department
                ))
            
            self.logger.info(f"Fallback extraction found {len(employees)} employees")
            
        except Exception as e:
            self.logger.error(f"Fallback extraction failed: {str(e)}")
        
        return employees
    
    def save_to_json(self, employees: List[SeatingChartData], filename: str = "seating_chart_data.json") -> Path:
        """
        Save employee data to JSON file.
        
        Args:
            employees: List of SeatingChartData objects
            filename: Output filename
            
        Returns:
            Path to the saved file
        """
        from .config import ScraperConfig
        cfg = ScraperConfig.from_env()
        output_dir = Path(cfg.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        
        data = {
            "metadata": {
                "total_employees": len(employees),
                "scraped_at": datetime.now().isoformat(),
                "source_url": self.base_url,
                "scraping_method": "seating_chart_extraction"
            },
            "employees": [emp.to_dict() for emp in employees]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(employees)} employees to {output_path}")
        return output_path


async def main():
    """Main function for testing the scraper."""
    logging.basicConfig(level=logging.INFO)
    
    scraper = SeatingChartScraper(headless=False, debug_mode=True)  # Set to False for debugging
    
    try:
        employees = await scraper.scrape_all_employees()
        output_path = scraper.save_to_json(employees)
        
        print(f"\nScraping completed!")
        print(f"Total employees: {len(employees)}")
        print(f"Employees with seats: {len([e for e in employees if e.seat])}")
        print(f"Employees with departments: {len([e for e in employees if e.department])}")
        print(f"Output file: {output_path}")
        
        # Show some examples
        print("\nSample employees:")
        for emp in employees[:5]:
            print(f"  {emp.name} - Seat: {emp.seat} - Dept: {emp.department}")
            
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
