"""
Service layer for the Employee Data Scraper.
"""

# Lazy imports to avoid dependency issues
__all__ = [
    "AutoLogin",
    "ImageDownloader",
    "HTMLReportGenerator",
    "generate_employee_directory_html",
    "SeatingChartScraper",
    "SeatingChartData"
]

def get_auth():
    from .auth import AutoLogin
    return AutoLogin

def get_image_downloader():
    from .image_downloader import ImageDownloader
    return ImageDownloader

def get_html_generator():
    from .html_generator import HTMLReportGenerator, generate_employee_directory_html
    return HTMLReportGenerator, generate_employee_directory_html

def get_seating_scraper():
    from .seating_scraper import SeatingChartScraper, SeatingChartData
    return SeatingChartScraper, SeatingChartData
