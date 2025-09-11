"""
Employee data scraper package.
"""

from .employee_data import EmployeeData
from .employee_scraper import EmployeeScraper
from .image_downloader import ImageDownloader
from .config import ScraperConfig
from .auto_login import AutoLogin
from .complete_scraper import CompleteScraper
from .credentials_gui import CredentialsGUI, show_credentials_gui
from .html_report_generator import HTMLReportGenerator, generate_employee_directory_html
# from .seating_chart_scraper import SeatingChartScraper, SeatingChartData  # Removed - not working
from .data_merger import DataMerger

__version__ = "1.0.0"
__author__ = "EnneadTab Team"

__all__ = [
    "EmployeeData",
    "EmployeeScraper",
    "ImageDownloader",
    "ScraperConfig",
    "AutoLogin",
    "CompleteScraper",
    "CredentialsGUI",
    "show_credentials_gui",
    "HTMLReportGenerator",
    "generate_employee_directory_html",
    "SeatingChartScraper"
    "SeatingChartData"
    "DataMerger"
]
