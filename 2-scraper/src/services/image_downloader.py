"""
Image downloader utility for employee profile images.
"""
import os
import aiohttp
import asyncio
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse, unquote
import logging
from playwright.async_api import Page


class ImageDownloader:
    """
    Handles downloading and saving employee profile images.
    """
    
    def __init__(self, download_dir: str = "assets/images"):
        """
        Initialize the image downloader.
        
        Args:
            download_dir: Directory to save downloaded images
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Use the download_dir directly for images
        self.images_dir = self.download_dir
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_filename_from_url(self, url: str, employee_name: str = None) -> str:
        """
        Generate a filename from URL and employee name.
        
        Args:
            url: Image URL
            employee_name: Employee name for fallback filename
            
        Returns:
            Generated filename
        """
        if not url:
            return f"unknown_{employee_name or 'employee'}.jpg"
        
        # Parse URL to get filename
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # If no filename in URL, create one
        if not filename or '.' not in filename:
            # Try to get extension from content type or use default
            extension = self._get_extension_from_url(url)
            safe_name = self._sanitize_filename(employee_name or "employee")
            filename = f"{safe_name}_profile{extension}"
        
        # Decode URL encoding
        filename = unquote(filename)
        
        # Sanitize filename
        filename = self._sanitize_filename(filename)
        
        return filename
    
    def _get_extension_from_url(self, url: str) -> str:
        """Get file extension from URL or content type."""
        # Common image extensions
        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                if ext in url.lower():
                    return ext
        
        # Default to jpg
        return '.jpg'
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unknown"
        
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove extra spaces and dots
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        return filename
    
    async def capture_preview_image(self, page: Page, employee_name: str, image_selector: str = None) -> Optional[str]:
        """
        Capture the preview image directly from the page using screenshot.
        This avoids authentication issues with downloading full-resolution images.
        
        Args:
            page: Playwright page object
            employee_name: Employee name for filename
            image_selector: CSS selector for the image element
            
        Returns:
            Path to saved image file, or None if failed
        """
        try:
            # Default selector for employee profile images
            if not image_selector:
                image_selector = 'img[src*="/api/image/"], .profile-image img, .employee-image img, .avatar img'
            
            # Find the image element
            image_element = await page.query_selector(image_selector)
            if not image_element:
                self.logger.warning(f"No image found for {employee_name}")
                return None
            
            # Generate filename
            filename = f"{employee_name.replace(' ', '_')}_profile.jpg"
            file_path = self.images_dir / filename
            
            # Take screenshot of the image element
            await image_element.screenshot(path=str(file_path))
            
            self.logger.info(f"Captured preview image for {employee_name}: {file_path}")
            # Return relative web path from docs root for GitHub Pages
            return f"assets/images/{filename}"
            
        except Exception as e:
            self.logger.error(f"Failed to capture preview image for {employee_name}: {e}")
            return None
    
    async def download_image(self, url: str, employee_name: str = None, page=None) -> Optional[str]:
        """
        Download an image from URL and save it locally.
        
        Args:
            url: Image URL to download
            employee_name: Employee name for filename generation
            page: Playwright page object for authenticated requests (optional)
            
        Returns:
            Local file path if successful, None otherwise
        """
        if not url:
            self.logger.warning("No URL provided for image download")
            return None
        
        try:
            filename = self._get_filename_from_url(url, employee_name)
            file_path = self.images_dir / filename
            
            # Skip if file already exists
            if file_path.exists():
                self.logger.info(f"Image already exists: {file_path}")
                # Return relative web path from docs root for GitHub Pages
                return f"assets/images/{filename}"
            
            # Use authenticated browser session if available
            if page:
                try:
                    # Use Playwright's request context which includes authentication
                    response = await page.request.get(url)
                    if response.status == 200:
                        # Get content type to determine extension
                        content_type = response.headers.get('content-type', '')
                        if 'image' not in content_type:
                            self.logger.warning(f"URL does not point to an image: {url}")
                            return None
                        
                        # Read image data
                        image_data = await response.body()
                        
                        # Save image
                        with open(file_path, 'wb') as f:
                            f.write(image_data)
                        
                        self.logger.info(f"Downloaded image: {file_path}")
                        # Return relative web path from docs root for GitHub Pages
                        return f"assets/images/{filename}"
                    else:
                        self.logger.error(f"Failed to download image: {url} (Status: {response.status})")
                        return None
                except Exception as e:
                    self.logger.error(f"Error downloading image with browser session {url}: {str(e)}")
                    return None
            else:
                # Fallback to aiohttp (will likely fail for authenticated URLs)
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            # Get content type to determine extension
                            content_type = response.headers.get('content-type', '')
                            if 'image' not in content_type:
                                self.logger.warning(f"URL does not point to an image: {url}")
                                return None
                            
                            # Read image data
                            image_data = await response.read()
                            
                            # Save image
                            with open(file_path, 'wb') as f:
                                f.write(image_data)
                            
                            self.logger.info(f"Downloaded image: {file_path}")
                            # Return relative web path from docs root for GitHub Pages
                            return f"assets/images/{filename}"
                        else:
                            self.logger.error(f"Failed to download image: {url} (Status: {response.status})")
                            return None
                        
        except Exception as e:
            self.logger.error(f"Error downloading image {url}: {str(e)}")
            return None
    
    def get_image_info(self, file_path: str) -> dict:
        """
        Get information about a downloaded image.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with image information
        """
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        file_stat = os.stat(file_path)
        return {
            "file_path": file_path,
            "file_size": file_stat.st_size,
            "file_size_mb": round(file_stat.st_size / (1024 * 1024), 2),
            "created": file_stat.st_ctime,
            "modified": file_stat.st_mtime
        }
    
    def cleanup_failed_downloads(self):
        """Remove any empty or corrupted image files."""
        for file_path in self.images_dir.glob("*"):
            if file_path.is_file() and file_path.stat().st_size == 0:
                file_path.unlink()
                self.logger.info(f"Removed empty file: {file_path}")
    
    def get_download_stats(self) -> dict:
        """Get statistics about downloaded images."""
        total_files = 0
        total_size = 0
        
        for file_path in self.images_dir.glob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        return {
            "total_images": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "download_directory": str(self.images_dir)
        }
