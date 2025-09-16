"""
Employee Data Scraper - Professional Package Structure

A comprehensive tool for scraping employee data from the Ennead website,
including contact information, profile images, and organizational data.
"""

__version__ = "2.0.0"
__author__ = "EnneadTab Team"
__description__ = "Employee Data Scraper with Professional Structure"

# Import main components for easy access
# Note: Import only what's needed to avoid dependency issues

__all__ = [
    "Orchestrator",
    "ScraperConfig",
]

# Lazy imports to avoid dependency issues
def get_orchestrator():
    from .core.orchestrator import Orchestrator
    return Orchestrator

def get_scraper_config():
    from .config.settings import ScraperConfig
    return ScraperConfig
