"""
Core business logic for the Employee Data Scraper.
"""

# Lazy imports to avoid dependency issues
__all__ = [
    "EmployeeData",
    "EmployeeScraper", 
    "Orchestrator",
    "DataMerger",
    "CompleteScraper"
]

def get_models():
    from .models import EmployeeData
    return EmployeeData

def get_scraper():
    from .unified_scraper import UnifiedEmployeeScraper as EmployeeScraper
    return EmployeeScraper

def get_orchestrator():
    from .orchestrator import ScraperOrchestrator
    return ScraperOrchestrator
 

def get_complete_scraper():
    from .complete_scraper import CompleteScraper
    return CompleteScraper
