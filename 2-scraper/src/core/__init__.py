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

def get_development_orchestrator():
    from .orchestrator import DevelopmentOrchestrator
    return DevelopmentOrchestrator

def get_production_orchestrator():
    from .individual_data_orchestrator import ProductionOrchestrator
    return ProductionOrchestrator

def get_data_merger():
    from .data_merger import DataMerger
    return DataMerger

def get_complete_scraper():
    from .complete_scraper import CompleteScraper
    return CompleteScraper
