"""
Auto-login module for handling Microsoft authentication.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import Page


class AutoLogin:
    """
    Handles automatic login to Microsoft authentication systems.
    """
    
    def __init__(self, credentials_file: str = "credentials.json"):
        """
        Initialize the auto-login handler.
        
        Args:
            credentials_file: Path to the credentials JSON file
        """
        self.credentials_file = Path(__file__).parent.parent / credentials_file
        self.logger = logging.getLogger(__name__)
        self.credentials: Optional[Dict[str, str]] = None
    
    def create_credentials_file(self, email: str, password: str) -> bool:
        """
        Create a credentials file with the provided email and password.
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            True if file was created successfully, False otherwise
        """
        try:
            credentials_data = {
                "email": email,
                "password": password
            }
            
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(credentials_data, f, indent=2)
            
            self.logger.info(f"Credentials file created: {self.credentials_file}")
            self.logger.info("Note: This file is NOT tracked in git for security reasons")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create credentials file: {e}")
            return False
    
    def load_credentials(self) -> bool:
        """
        Load credentials with three-tier fallback system:
        1. GitHub secrets (environment variables)
        2. Local credentials.json file
        3. If neither exists, prompt for credentials setup
        
        Returns:
            True if credentials loaded successfully, False otherwise
        """
        # Tier 1: Try to load from GitHub secrets (environment variables)
        email_env = os.getenv('SCRAPER_EMAIL')
        password_env = os.getenv('SCRAPER_PASSWORD')
        
        if email_env and password_env:
            self.credentials = {
                'email': email_env,
                'password': password_env
            }
            self.logger.info(f"Credentials loaded from GitHub secrets for: {self.credentials['email']}")
            return True
        
        # Tier 2: Try to load from local credentials file
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'r') as f:
                    self.credentials = json.load(f)
                
                if self.credentials.get('email') and self.credentials.get('password'):
                    self.logger.info(f"Credentials loaded from local file for: {self.credentials['email']}")
                    return True
                else:
                    self.logger.warning("Local credentials file is missing email or password")
            except Exception as e:
                self.logger.error(f"Error loading local credentials file: {e}")
        
        # Tier 3: Neither GitHub secrets nor local file available
        self.logger.warning("No credentials found. GitHub secrets and local credentials.json not available.")
        self.logger.info("Launching credentials GUI to create local credentials.json...")
        self.logger.info("Note: This file will be stored locally and NOT tracked in git for security.")
        
        # Import and show the credentials GUI
        try:
            from ..config.credentials import show_credentials_gui
            if show_credentials_gui():
                self.logger.info("Credentials GUI completed successfully!")
                # Try to load the newly created credentials
                return self.load_credentials()
            else:
                self.logger.error("Credentials GUI was cancelled or failed")
                return False
        except Exception as e:
            self.logger.error(f"Failed to launch credentials GUI: {e}")
            self.logger.info("Please set up credentials manually:")
            self.logger.info("1. Set GitHub secrets: SCRAPER_EMAIL and SCRAPER_PASSWORD")
            self.logger.info("2. Run: python -m src.config.credentials")
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
            if not self.setup_credentials_if_needed():
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
    
    def setup_credentials_if_needed(self) -> bool:
        """
        Set up credentials if none are available.
        This will show the GUI for credential setup.
        
        Returns:
            True if credentials are now available, False otherwise
        """
        if self.credentials:
            return True
        
        if not self.load_credentials():
            self.logger.info("No credentials found. Starting credentials setup...")
            try:
                from ..config.credentials import show_credentials_gui
                if show_credentials_gui():
                    return self.load_credentials()
                else:
                    self.logger.error("Credentials setup was cancelled or failed")
                    return False
            except ImportError:
                self.logger.error("Cannot import credentials GUI. Please set up credentials manually.")
                return False
        
        return True
