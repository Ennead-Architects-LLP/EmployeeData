"""
Base scraper with shared core functionality for employee data extraction.
This eliminates duplication between SimpleEmployeeScraper and CompleteScraper.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from playwright.async_api import Page

from .models import EmployeeData
from ..services.auth import AutoLogin
from ..services.image_downloader import ImageDownloader


class BaseEmployeeScraper:
    """
    Base scraper with shared core functionality for extracting basic employee data.
    Both SimpleEmployeeScraper and CompleteScraper can inherit from this.
    """
    
    def __init__(self, download_images: bool = True, timeout: int = 30000):
        """
        Initialize the base scraper.
        
        Args:
            download_images: Whether to download profile images
            timeout: Page load timeout in milliseconds
        """
        self.download_images = download_images
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Initialize shared components
        self.image_downloader = ImageDownloader() if download_images else None
        self.auto_login = AutoLogin()
        
        # Common selectors for basic employee data
        self.base_selectors = {
            'employee_name': '.employee-name, .profile-name, h3, h4',
            'employee_title': '.employee-title, .profile-title, .position',
            'profile_image': 'img.profile-image, .employee-photo img, .avatar img',
            'email_link': 'a[href^="mailto:"]',
            'phone_link': 'a[href^="tel:"]',
            'bio_text': '.bio, .about, .description, .employee-bio',
            'department': '.department, .team, .division'
        }
    
    async def extract_basic_employee_data(self, page: Page, profile_url: str, 
                                        employee_name: str = None, 
                                        image_url: str = None) -> EmployeeData:
        """
        Extract basic employee data that both scrapers need.
        This ensures consistency between SimpleEmployeeScraper and CompleteScraper.
        
        Args:
            page: Playwright page object
            profile_url: URL of the employee profile
            employee_name: Name of the employee (if known)
            image_url: Image URL (if known)
            
        Returns:
            EmployeeData object with basic information
        """
        try:
            # Create employee object
            employee = EmployeeData()
            employee.human_name = employee_name or ""
            employee.profile_url = profile_url
            employee.profile_id = profile_url.split('/')[-1] if '/' in profile_url else f"employee_{employee_name.replace(' ', '_') if employee_name else 'unknown'}"
            
            # Extract basic information using consistent selectors
            employee_data = await page.evaluate(f"""
                () => {{
                    const data = {{}};
                    
                    // Basic information
                    data.human_name = document.querySelector('{self.base_selectors['employee_name']}')?.textContent?.trim() || '';
                    data.email = document.querySelector('{self.base_selectors['email_link']}')?.href?.replace('mailto:', '') || '';
                    data.phone = document.querySelector('{self.base_selectors['phone_link']}')?.href?.replace('tel:', '') || '';
                    
                    // Position and department
                    data.position = document.querySelector('{self.base_selectors['employee_title']}')?.textContent?.trim() || '';
                    data.department = document.querySelector('{self.base_selectors['department']}')?.textContent?.trim() || '';
                    
                    // Bio
                    data.bio = document.querySelector('{self.base_selectors['bio_text']}')?.textContent?.trim() || '';
                    
                    // Office location
                    data.office_location = document.querySelector('.location, .office, .address')?.textContent?.trim() || '';
                    
                    // Profile image
                    const img = document.querySelector('{self.base_selectors['profile_image']}');
                    data.image_url = img ? img.src : '';
                    
                    return data;
                }}
            """)
            
            # Update employee object with extracted data
            if employee_data.get('human_name'):
                employee.human_name = employee_data['human_name']
            if employee_data.get('email'):
                employee.email = employee_data['email']
            if employee_data.get('phone'):
                employee.phone = employee_data['phone']
            if employee_data.get('position'):
                employee.position = employee_data['position']
            if employee_data.get('department'):
                employee.department = employee_data['department']
            if employee_data.get('bio'):
                employee.bio = employee_data['bio']
            if employee_data.get('office_location'):
                employee.office_location = employee_data['office_location']
            if employee_data.get('image_url'):
                employee.image_url = employee_data['image_url']
            
            # Handle image URL from parameter if provided
            if image_url and not employee.image_url:
                employee.image_url = image_url
            
            # Download image if enabled
            if self.download_images and employee.image_url and self.image_downloader:
                try:
                    name = employee.human_name or employee_name or 'unknown'
                    local_path = await self.image_downloader.download_image(
                        employee.image_url, 
                        name.replace(' ', '_')
                    )
                    if local_path:
                        employee.image_local_path = local_path
                        self.logger.info(f"Downloaded image for {employee.human_name}")
                except Exception as e:
                    self.logger.warning(f"Failed to download image for {employee.human_name}: {e}")
            
            return employee
            
        except Exception as e:
            self.logger.error(f"Error extracting basic employee data: {e}")
            # Return minimal employee data
            employee = EmployeeData()
            employee.human_name = employee_name or "Unknown"
            employee.profile_url = profile_url
            return employee
    
    def normalize_office_location(self, location: str) -> str:
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
    
    def validate_employee_data(self, employee: EmployeeData) -> bool:
        """
        Validate that employee data has required fields.
        
        Args:
            employee: EmployeeData object to validate
            
        Returns:
            True if valid, False otherwise
        """
        return bool(employee.human_name or employee.email)
    
    def get_employee_summary(self, employee: EmployeeData) -> str:
        """
        Get a summary of employee data for logging.
        
        Args:
            employee: EmployeeData object
            
        Returns:
            Summary string
        """
        return f"Employee(name='{employee.human_name}', email='{employee.email}', position='{employee.position}')"
