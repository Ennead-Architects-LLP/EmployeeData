# EmployeeData (Professional Structure)

## Quick Start

### Setup Virtual Environment
```bash
# Create virtual environment
py -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install playwright
playwright install
```

### Run the Application
```bash
# Using virtual environment
.venv\Scripts\python.exe run.py --debug --debug-employees 1 --debug-no-dom --no-images

# Or using system Python (if playwright is installed)
python run.py --headless=true --no-images
```

Common flags:
- `--debug` `--debug-employees N` `--debug-no-dom`
- `--setup-credentials`

## Professional Repo Structure

```
EmployeeData/
├── src/                    # Source code (professional structure)
│   ├── config/            # Configuration management
│   ├── core/              # Core business logic
│   ├── services/          # Service layer (auth, images, HTML)
│   ├── ui/                # User interface components
│   └── cli/               # Command line interface
├── static/                # Static web assets (templates)
│   ├── templates/         # HTML templates
│   ├── css/               # CSS styles
│   └── js/                # JavaScript files
├── assets/                # Generated output (committed for GitHub Pages)
│   ├── employees_data.json
│   ├── individual_employees/
│   ├── images/            # Profile images
│   ├── styles.css         # Generated CSS
│   └── app.js             # Generated JS
├── debug/                 # Debug artifacts (gitignored)
├── tests/                 # Test suite
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

## Separation of Concerns
- **Source Code**: `src/` - All business logic organized by layer
- **Static Assets**: `static/` - Templates and source assets
- **Generated Output**: `assets/` - Committed for GitHub Pages
- **Debug Files**: `debug/` - Temporary debugging artifacts (gitignored)
- **Credentials**: `credentials.json` - Local only (gitignored)
- **Main Entry**: `run.py` - Application entry point

## GitHub Pages
Commit at least:
- `index.html`
- `assets/` (include images if desired)
- `run.py` and code
- Exclude `DEBUG/` and `credentials.json`