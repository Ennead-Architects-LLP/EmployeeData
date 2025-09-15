# Orchestrator Structure

## 🎯 Overview

The scraper system uses **2 orchestrators** to handle different use cases. Each orchestrator is designed for a specific purpose and environment.

## 📋 Orchestrators

### 1. **`DevelopmentOrchestrator`** (Development/Analysis)
- **File**: `src/core/orchestrator.py`
- **Used by**: `main.py` (local development)
- **Purpose**: Full development pipeline with comprehensive analysis
- **Features**:
  - ✅ Scrapes employee data using unified scraper
  - ✅ Saves to JSON file
  - ✅ Generates HTML report
  - ✅ Voice announcements
  - ✅ Task verification
  - ✅ DOM capturing for debugging
  - ✅ Incremental saving

### 2. **`ProductionOrchestrator`** (GitHub Actions/Production)
- **File**: `src/core/individual_data_orchestrator.py`
- **Used by**: `weekly_scraper.py` (GitHub Actions)
- **Purpose**: Production pipeline for automated weekly updates
- **Features**:
  - ✅ Scrapes employee data using unified scraper
  - ✅ Saves each employee as individual JSON file
  - ✅ Downloads images to `docs/assets/images/`
  - ✅ Merges with existing data (preserves computer info)
  - ✅ Path validation for GitHub Pages
  - ✅ Optimized for CI/CD environment

## 🔄 Usage Patterns

### Development Workflow
```python
# main.py
from .core.orchestrator import DevelopmentOrchestrator

orchestrator = DevelopmentOrchestrator(config)
html_path = await orchestrator.run()
# Generates: JSON + HTML + Voice announcements
```

### Production Workflow
```python
# weekly_scraper.py
from src.core.individual_data_orchestrator import ProductionOrchestrator

orchestrator = ProductionOrchestrator(config)
success = await orchestrator.run()
# Generates: Individual JSON files + Images for GitHub Pages
```

## 📁 Output Structure

### Development Output
```
docs/
├── employee_data.json          # Combined employee data
├── employee_report.html        # HTML report
└── debug/                      # Debug files
    ├── dom_captures/
    └── screenshots/
```

### Production Output
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
└── employee_files_list.json    # Index of all employees
```

## 🎯 Why Two Orchestrators?

1. **Different Output Formats**:
   - Development needs HTML reports for analysis
   - Production needs individual files for GitHub Pages

2. **Different Environments**:
   - Development has GUI, voice, debugging features
   - Production is headless, automated, CI/CD optimized

3. **Different Data Handling**:
   - Development works with combined data
   - Production works with individual files for web hosting

4. **Different Features**:
   - Development has analysis and debugging tools
   - Production focuses on data collection and web publishing

## 🔧 Naming Convention

- **`DevelopmentOrchestrator`**: For local development and analysis
- **`ProductionOrchestrator`**: For automated production runs
- **`UnifiedEmployeeScraper`**: The core scraper used by both orchestrators

## ✅ Benefits

- **Clear Separation**: Each orchestrator has a specific purpose
- **Optimized**: Each is optimized for its use case
- **Maintainable**: Easy to understand and modify
- **Flexible**: Can add features to one without affecting the other
- **Consistent**: Both use the same unified scraper for data extraction

## 🚀 Future Enhancements

- Add configuration options to switch between output formats
- Add more specialized orchestrators if needed
- Consider making orchestrators configurable rather than separate classes
