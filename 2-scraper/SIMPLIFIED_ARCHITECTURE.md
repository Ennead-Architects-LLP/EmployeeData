# Simplified Scraper Architecture

## 🎯 **Single Flow Design**

The scraper now follows a **single, unified flow** that works for both local development and GitHub Actions.

## 📋 **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   main.py       │    │ ScraperOrchestrator │    │ UnifiedScraper  │
│ (Entry Point)   │───▶│   (Single Flow)   │───▶│ (Data Extraction)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ weekly_scraper.py│    │   JSON Files     │    │   Images        │
│ (GitHub Actions)│    │   (Individual)   │    │   (Profile)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔧 **Components**

### 1. **`main.py`** - Single Entry Point
- **Purpose**: Main entry point for both local and GitHub Actions
- **Features**: 
  - Command-line argument parsing
  - Configuration management
  - Debug mode support
  - Credential setup

### 2. **`ScraperOrchestrator`** - Single Orchestrator
- **Purpose**: Orchestrates the entire scraping process
- **Features**:
  - Scrapes employee data using UnifiedScraper
  - Saves individual JSON files to `docs/assets/individual_employees/`
  - Saves combined JSON file to `docs/assets/employee_files_list.json`
  - Downloads images to `docs/assets/images/`

### 3. **`UnifiedScraper`** - Core Scraper
- **Purpose**: Extracts comprehensive employee data
- **Features**:
  - Browser automation with Playwright
  - Authentication handling
  - Comprehensive data extraction
  - Image downloading

### 4. **`weekly_scraper.py`** - GitHub Actions Wrapper
- **Purpose**: Simple wrapper that calls `main.py`
- **Features**:
  - Calls `python -m src.main --headless=true`
  - Handles logging and error reporting
  - No duplicate logic

## 🚀 **Usage**

### Local Development
```bash
cd 2-scraper
python -m src.main
```

### GitHub Actions
```bash
cd 2-scraper
python weekly_scraper.py
# Which internally calls: python -m src.main --headless=true
```

## 📁 **Output Structure**

```
docs/assets/
├── individual_employees/       # Individual JSON files
│   ├── John_Doe.json
│   ├── Jane_Smith.json
│   └── ...
├── images/                     # Profile images
│   ├── John_Doe_profile.jpg
│   ├── Jane_Smith_profile.jpg
│   └── ...
└── employee_files_list.json    # Combined employee data
```

## ✅ **Benefits**

1. **Single Source of Truth**: One scraper, one orchestrator, one flow
2. **No Duplication**: Same logic for local and GitHub Actions
3. **Clear Separation**: Scraper only scrapes, no HTML generation
4. **Simple Maintenance**: Changes in one place affect everything
5. **Consistent Output**: Same JSON structure everywhere
6. **Easy Testing**: Single entry point for all testing

## 🎯 **What Was Removed**

- ❌ **HTML Generation**: Moved to static framework in docs folder
- ❌ **Voice Announcements**: Not needed for automated scraping
- ❌ **Multiple Orchestrators**: Consolidated to single ScraperOrchestrator
- ❌ **Development vs Production**: Single flow for all use cases
- ❌ **Complex Mode Logic**: Simplified to single comprehensive scraper

## 🔄 **Migration**

### Before (Complex)
- `DevelopmentOrchestrator` + `ProductionOrchestrator`
- HTML generation + voice announcements
- Different flows for local vs GitHub Actions

### After (Simple)
- `ScraperOrchestrator` (single orchestrator)
- JSON files only (no HTML generation)
- `weekly_scraper.py` just calls `main.py`

## 🚀 **Future Enhancements**

- Add configuration options for different output formats
- Add more specialized scrapers if needed
- Consider making the orchestrator more configurable
- Add more comprehensive error handling and retry logic

This simplified architecture makes the scraper much easier to understand, maintain, and extend!
