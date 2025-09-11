# EmployeeData (GitHub Pages Ready)

## Quick Start

- Run the scraper and site generator:
```bash
python run.py --headless=true --no-images
```
Common flags:
- `--debug` `--debug-employees N` `--debug-no-dom`
- `--setup-credentials`

## Repo Layout

- `run.py`               → App entry (runs orchestrator)
- `app/`                 → Public app API (thin facade)
- `GetEmployeeData/`     → Internal modules (scraper, config, orchestrator, etc.)
- `assets/`              → Site output and data
  - `index.html` (at repo root)
  - `assets/styles.css`, `assets/app.js`
  - `assets/employees_data.json`, `assets/individual_employees/`
  - `assets/images/` (downloaded profile images)
- `DEBUG/`               → Debug artifacts (gitignored)
- `credentials.json`     → Local credentials (not committed)

## Separation of Concerns
- Entry: `run.py`, `app/`
- Logic: `GetEmployeeData/modules/*`
- Data: `assets/employees_data.json`, `assets/individual_employees/`
- Debug: `DEBUG/` (DOM captures, screenshots, selector reports)
- Credentials: `credentials.json` (local only)
- Output Page: `index.html` + `assets/`

## GitHub Pages
Commit at least:
- `index.html`
- `assets/` (include images if desired)
- `run.py` and code
- Exclude `DEBUG/` and `credentials.json`