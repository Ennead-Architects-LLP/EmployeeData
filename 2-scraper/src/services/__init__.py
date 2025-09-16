"""
Service layer for the Employee Data Scraper.
"""

# Lazy imports to avoid dependency issues
__all__ = [
    "AutoLogin",
    "ImageDownloader"
]

def get_auth():
    from .auth import AutoLogin
    return AutoLogin

def get_image_downloader():
    from .image_downloader import ImageDownloader
    return ImageDownloader

# HTML generation removed by policy

# Seating scraper removed by policy
