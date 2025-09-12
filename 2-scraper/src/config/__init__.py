"""
Configuration management for the Employee Data Scraper.
"""

# Lazy imports to avoid dependency issues
__all__ = [
    "ScraperConfig",
    "CredentialsGUI", 
    "show_credentials_gui"
]

def get_scraper_config():
    from .settings import ScraperConfig
    return ScraperConfig

def get_credentials_gui():
    from .credentials import CredentialsGUI, show_credentials_gui
    return CredentialsGUI, show_credentials_gui
