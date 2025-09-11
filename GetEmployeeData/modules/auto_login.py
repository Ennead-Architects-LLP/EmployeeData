"""
Auto-login module for handling Microsoft authentication.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import Page


class AutoLogin:
    """
    Handles automatic login to Microsoft authentication systems.
    """
    
    def __init__(self, credentials_file: str = "credentials/credentials.json"):
        """
        Initialize the auto-login handler.
        
        Args:
            credentials_file: Path to the credentials JSON file
        """
        self.credentials_file = Path(__file__).parent.parent / credentials_file
        self.logger = logging.getLogger(__name__)
        self.credentials: Optional[Dict[str, str]] = None
    
    def load_credentials(self) -> bool:
        """
        Load credentials from the credentials file.
        
        Returns:
            True if credentials loaded successfully, False otherwise
        """
        if not self.credentials_file.exists():
            self.logger.error(f"Credentials file not found: {self.credentials_file}")
            return False
        
        try:
            with open(self.credentials_file, 'r') as f:
                self.credentials = json.load(f)
            
            if not self.credentials.get('email') or not self.credentials.get('password'):
                self.logger.error("Credentials file is missing email or password")
                return False
            
            self.logger.info(f"Credentials loaded for: {self.credentials['email']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading credentials: {e}")
            return False
    
    async def login(self, page: Page, target_url: str) -> bool:
        """
        Perform automatic login to the target URL.
        
        Args:
            page: Playwright page object
            target_url: URL to navigate to after login
            
        Returns:
            True if login successful, False otherwise
        """
        if not self.credentials:
            if not self.load_credentials():
                return False
        
        try:
            self.logger.info(f"Navigating to: {target_url}")
            await page.goto(target_url, wait_until='networkidle')
            
            current_url = page.url
            self.logger.info(f"Current URL: {current_url}")
            
            # Check if we need to log in
            if 'login' in current_url.lower() or 'microsoftonline' in current_url.lower():
                self.logger.info("Login required. Starting automatic login process...")
                
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Step 1: Enter email
                email_input = await page.wait_for_selector('input[type="email"]', timeout=15000)
                await email_input.fill(self.credentials['email'])
                self.logger.info("[SUCCESS] Email entered")
                
                # Step 2: Click next button
                next_button = await page.wait_for_selector('input[type="submit"]', timeout=15000)
                await next_button.click()
                self.logger.info("[SUCCESS] Clicked next button")
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Step 3: Enter password
                password_input = await page.wait_for_selector('input[type="password"]', timeout=15000)
                await password_input.fill(self.credentials['password'])
                self.logger.info("[SUCCESS] Password entered")
                
                # Step 4: Click sign in button
                signin_button = await page.wait_for_selector('input[type="submit"]', timeout=15000)
                await signin_button.click()
                self.logger.info("[SUCCESS] Clicked sign in button")
                
                # Wait for login to complete
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)
                
                # Check if login was successful
                current_url = page.url
                if 'login' in current_url.lower() or 'microsoftonline' in current_url.lower():
                    self.logger.error("Login failed - still on login page")
                    return False
                else:
                    self.logger.info("[SUCCESS] Login successful!")
                    return True
            else:
                self.logger.info("Already logged in or no login required")
                return True
                
        except Exception as e:
            self.logger.error(f"Error during login process: {e}")
            return False
    
    def create_credentials_file(self, email: str, password: str) -> bool:
        """
        Create a credentials file with the provided email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            True if credentials file created successfully, False otherwise
        """
        try:
            credentials = {
                "email": email,
                "password": password,
                "note": "Auto-generated credentials file"
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            self.logger.info(f"Credentials file created: {self.credentials_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating credentials file: {e}")
            return False
    
    def get_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get the loaded credentials.
        
        Returns:
            Dictionary with credentials or None if not loaded
        """
        return self.credentials
