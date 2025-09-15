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
    from .simple_scraper import SimpleEmployeeScraper as EmployeeScraper
    return EmployeeScraper

def get_orchestrator():
    from .orchestrator import Orchestrator
    return Orchestrator

def get_data_merger():
    from .data_merger import DataMerger
    return DataMerger

def get_complete_scraper():
    from .complete_scraper import CompleteScraper
    return CompleteScraper
