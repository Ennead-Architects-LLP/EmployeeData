"""
Configuration settings for the employee scraper.
"""
import os
import time
from pathlib import Path
from datetime import datetime, timedelta


class ScraperConfig:
    """Configuration class for the employee scraper."""
    
    # Base configuration
    BASE_URL = "https://ei.ennead.com/employees/1/all-employees"
    
    # Browser settings
    HEADLESS = True
    TIMEOUT = 30000  # milliseconds
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080
    
    # Download settings
    DOWNLOAD_IMAGES = True
    IMAGE_DOWNLOAD_DIR = "docs/assets/images"  # Keep in docs/assets for GitHub Pages
    MAX_CONCURRENT_DOWNLOADS = 5
    
    # Output settings - use absolute paths relative to project root
    # HTML (index.html) remains at OUTPUT_DIR (repo root)
    OUTPUT_DIR = "."
    # JSON and individual JSON live under docs/assets/ for GitHub Pages
    ASSETS_DIR = "docs/assets"
    # Debug and logs live under debug/ (can be gitignored)
    DEBUG_DIR = "debug"
    # No longer using compiled JSON file - individual files only
    INDIVIDUAL_FILES = True
    
    # Scraping settings
    DELAY_BETWEEN_REQUESTS = 1  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    # Debug settings
    DEBUG_MODE = False
    DEBUG_MAX_EMPLOYEES = 10  # Limit number of employees when in debug mode
    DEBUG_DOM_CAPTURE = True  # Capture DOM for debugging when in debug mode
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FILE = "debug/scraper.log"
    LOG_FORMAT = "[%(levelname)s] %(message)s"
    
    # User agent (Edge)
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    
    # Browser arguments
    BROWSER_ARGS = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-features=VizDisplayCompositor'
    ]
    
    def get_debug_output_path(self) -> Path:
        """Get the debug output directory path."""
        debug_dir = Path(self.DEBUG_DIR)
        debug_dir.mkdir(parents=True, exist_ok=True)
        return debug_dir
    
    def setup_debug_directories(self):
        """Setup debug-specific directories."""
        if self.DEBUG_MODE:
            debug_dir = self.get_debug_output_path()
            debug_dir.mkdir(parents=True, exist_ok=True)
            (debug_dir / "dom_captures").mkdir(exist_ok=True)
            (debug_dir / "screenshots").mkdir(exist_ok=True)
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables if they exist
        config.BASE_URL = os.getenv('SCRAPER_BASE_URL', config.BASE_URL)
        config.HEADLESS = os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true'
        config.DOWNLOAD_IMAGES = os.getenv('SCRAPER_DOWNLOAD_IMAGES', 'true').lower() == 'true'
        config.OUTPUT_DIR = os.getenv('SCRAPER_OUTPUT_DIR', config.OUTPUT_DIR)
        config.ASSETS_DIR = os.getenv('SCRAPER_ASSETS_DIR', config.ASSETS_DIR)
        config.DEBUG_DIR = os.getenv('SCRAPER_DEBUG_DIR', config.DEBUG_DIR)
        config.LOG_LEVEL = os.getenv('SCRAPER_LOG_LEVEL', config.LOG_LEVEL)
        
        return config
    
    def setup_directories(self):
        """Create necessary directories."""
        # Root for index.html
        Path(self.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        # Assets directories for JSON and images
        Path(self.ASSETS_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.ASSETS_DIR, "individual_employees").mkdir(parents=True, exist_ok=True)
        if self.DOWNLOAD_IMAGES:
            Path(self.IMAGE_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
        # Debug directory
        Path(self.DEBUG_DIR).mkdir(parents=True, exist_ok=True)
    
    def get_output_path(self, filename: str = None) -> Path:
        """Get full output path for a file."""
        if filename is None:
            filename = self.JSON_FILENAME
        return Path(self.ASSETS_DIR) / filename
    
    def cleanup_debug_files(self, max_files_per_folder: int = 30):
        """
        Clean up debug files by keeping only the most recent files per folder.
        
        Args:
            max_files_per_folder: Maximum number of files to keep per folder (default: 30)
        """
        debug_dir = self.get_debug_output_path()
        if not debug_dir.exists():
            return
        
        deleted_count = 0
        total_size_freed = 0
        
        # Clean up dom_captures folder
        dom_captures_dir = debug_dir / "dom_captures"
        if dom_captures_dir.exists():
            deleted, size = self._cleanup_folder_by_count(dom_captures_dir, max_files_per_folder)
            deleted_count += deleted
            total_size_freed += size
        
        # Clean up screenshots folder
        screenshots_dir = debug_dir / "screenshots"
        if screenshots_dir.exists():
            deleted, size = self._cleanup_folder_by_count(screenshots_dir, max_files_per_folder)
            deleted_count += deleted
            total_size_freed += size
        
        # Clean up any other files in debug directory (keep only the most recent)
        other_files = [f for f in debug_dir.iterdir() if f.is_file()]
        if len(other_files) > max_files_per_folder:
            # Sort by modification time (newest first)
            other_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            # Delete the oldest files
            for file_path in other_files[max_files_per_folder:]:
                file_size = file_path.stat().st_size
                file_path.unlink()
                deleted_count += 1
                total_size_freed += file_size
        
        if deleted_count > 0:
            size_mb = round(total_size_freed / (1024 * 1024), 2)
            print(f"Debug cleanup: Removed {deleted_count} files ({size_mb} MB), keeping max {max_files_per_folder} files per folder")
        else:
            print(f"Debug cleanup: No files removed, all folders within {max_files_per_folder} file limit")
    
    def _cleanup_folder_by_count(self, folder_path: Path, max_files: int) -> tuple[int, int]:
        """
        Clean up a folder by keeping only the most recent files.
        
        Args:
            folder_path: Path to the folder to clean up
            max_files: Maximum number of files to keep
            
        Returns:
            Tuple of (deleted_count, total_size_freed)
        """
        files = [f for f in folder_path.iterdir() if f.is_file()]
        
        if len(files) <= max_files:
            return 0, 0
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        deleted_count = 0
        total_size_freed = 0
        
        # Delete the oldest files
        for file_path in files[max_files:]:
            file_size = file_path.stat().st_size
            file_path.unlink()
            deleted_count += 1
            total_size_freed += file_size
        
        return deleted_count, total_size_freed
    
    def auto_cleanup_debug_files(self):
        """Automatically clean up debug files keeping max 30 files per folder."""
        self.cleanup_debug_files(max_files_per_folder=30)
