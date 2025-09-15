# Scraper Path Structure

## Overview
The scraper is designed to save all output files to the `docs/assets/` directory, ensuring consistency whether run locally or from GitHub Actions.

## Path Resolution
The scraper uses absolute path resolution to ensure files are always saved to the correct location:

```
Project Root: /path/to/EmployeeData/
├── docs/                    # GitHub Pages source directory
│   └── assets/             # Scraper output directory
│       ├── individual_employees/  # JSON files for each employee
│       └── images/         # Profile images
└── 2-scraper/             # Scraper source code
    └── src/
        └── core/
            └── individual_data_orchestrator.py
```

## Path Calculation
The orchestrator calculates paths as follows:
```python
# From: 2-scraper/src/core/individual_data_orchestrator.py
project_root = Path(__file__).parent.parent.parent.parent  # Go up 4 levels
output_path = project_root / "docs" / "assets"            # Target directory
```

This ensures:
- **Local execution**: Files saved to `EmployeeData/docs/assets/`
- **GitHub Actions**: Files saved to `EmployeeData/docs/assets/` (same location)

## Directory Structure
```
docs/assets/
├── individual_employees/     # Individual employee JSON files
│   ├── John_Doe.json
│   ├── Jane_Smith.json
│   └── ...
├── images/                  # Profile images
│   ├── John_Doe_profile.jpg
│   ├── Jane_Smith_profile.jpg
│   └── ...
└── employee_files_list.json # Index of all employee files
```

## Verification
The scraper includes validation to ensure:
1. All required directories exist
2. Files are saved to the correct location
3. Both JSON and image artifacts are generated
4. Paths are accessible for GitHub Pages

## GitHub Pages Integration
Since GitHub Pages serves from the `docs/` folder, the scraper output is directly accessible at:
- JSON files: `https://your-site.github.io/assets/individual_employees/`
- Images: `https://your-site.github.io/assets/images/`
- Index: `https://your-site.github.io/assets/employee_files_list.json`
