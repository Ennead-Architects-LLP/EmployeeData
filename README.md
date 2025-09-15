# EmployeeData - Multi-Component Architecture

Live site: https://ennead-architects-llp.github.io/EmployeeData/

A comprehensive employee data management system with 5 distinct components for data collection, processing, and display.

## 🏗️ Repository Structure

```
EmployeeData/
├── docs/           # 🌐 Main website (GitHub Pages)
├── 2-scraper/           # 🕛 Daily data collection
├── 3-aboutme/           # 💻 User computer data collection
├── 4-server/            # 🖥️ POST data handler
├── 5-workfiles/         # 📁 Reference materials
└── .github/             # ⚙️ GitHub Actions workflows
```

## 🚀 Quick Start

### 1. Website (Static Hosting)
```bash
cd docs
# Deploy to GitHub Pages - website loads data dynamically from JSON
```

### 2. Weekly Scraper
```bash
cd 2-scraper
pip install -r requirements_scraper.txt
python weekly_scraper.py
```

### 3. AboutMe App (User Computer)
```bash
cd 3-aboutme
pip install requests psutil wmi
python about_me.py --send-to-github --github-token YOUR_TOKEN
```

### 4. Server (Data Handler)
```bash
cd 4-server
pip install -r requirements_server.txt
python server.py
```

## 📋 Component Overview

### 1. Website Component (`docs/`)
- **Purpose**: Dynamic website hosted on GitHub Pages
- **Features**: Employee directory, search/filter, computer data display
- **Data Source**: Loads from `assets/employees_data.json`

### 2. Scraper Component (`2-scraper/`)
- **Purpose**: Daily employee data collection
- **Schedule**: Runs at midnight via GitHub Actions
- **Output**: Updates employee JSON and downloads images

### 3. AboutMe Component (`3-aboutme/`)
- **Purpose**: User computer data collection
- **Usage**: Users run locally to submit hardware info
- **Output**: Sends data via POST to server

### 4. Server Component (`4-server/`)
- **Purpose**: Handle POST data from AboutMe app
- **Function**: Merges computer data with employee records
- **API**: RESTful endpoints for data submission

### 5. Work Files Component (`5-workfiles/`)
- **Purpose**: Reference materials and documentation
- **Contents**: HR Excel files, reference scripts, docs

## 🔄 Data Flow

1. **Weekly Scraper** → Updates `employees_data.json`
2. **AboutMe App** → Sends computer data via POST
3. **Server** → Merges data into employee records
4. **Website** → Displays updated data dynamically

## 📊 Key Features

- ✅ **Dynamic Website** - No regeneration needed
- ✅ **Automated Data Collection** - Daily scraping
- ✅ **User Data Submission** - AboutMe app
- ✅ **Real-time Updates** - Website updates automatically
- ✅ **Modular Architecture** - Clear separation of concerns

---

# Weekly Employee Data Scraper

This component handles weekly data collection from the Ennead employee directory website.

## 🎯 Purpose

- **Weekly Data Collection**: Scrapes employee data from EI website
- **Image Download**: Downloads and updates profile images
- **Data Merging**: Preserves existing computer data while updating employee info
- **JSON Updates**: Saves data directly to website assets folder

## 🚀 Features

- ✅ **No HTML Generation** - Focuses only on data collection
- ✅ **Preserves Computer Data** - Keeps existing computer info intact
- ✅ **Image Management** - Downloads and updates profile images
- ✅ **Incremental Updates** - Only updates changed data
- ✅ **Automated Scheduling** - Runs weekly on Tuesday at 3:14 AM EST via GitHub Actions

## 📁 Structure

```
2-scraper/
├── weekly_scraper.py         # Main weekly scraper script
├── requirements.txt          # Dependencies
├── debug/                    # Debug output directory
│   ├── dom_captures/         # DOM capture files
│   ├── screenshots/          # Debug screenshots
│   └── seating_chart/        # Seating chart debug files
├── src/                      # Source code
│   ├── core/
│   │   ├── data_orchestrator.py      # Data-only orchestrator
│   │   ├── individual_data_orchestrator.py  # Individual employee processing
│   │   ├── complete_scraper.py       # Complete scraper implementation
│   │   ├── simple_scraper.py         # Simple scraper implementation
│   │   └── models.py                 # Data models
│   ├── services/
│   │   ├── dom_capture.py            # DOM capture and analysis
│   │   ├── advanced_selector_recorder.py  # Advanced selector recording
│   │   ├── debug_utilities.py        # Debug utilities
│   │   ├── image_downloader.py       # Image download service
│   │   ├── auth.py                   # Authentication service
│   │   └── html_generator.py         # HTML generation service
│   ├── tests/
│   │   └── test_scraper.py           # Test script
│   └── config/
│       ├── settings.py               # Configuration
│       └── credentials.py            # Credentials management
└── README.md                # This file
```

## 🔧 Usage

### Manual Run
```bash
cd 2-scraper
pip install -r requirements_scraper.txt
python weekly_scraper.py
```

### Test Run
```bash
cd 2-scraper
python -m src.tests.test_scraper
```

### DOM Capture and Debugging
```bash
cd 2-scraper
python -m src.services.dom_capture
python -m src.services.advanced_selector_recorder
```

### GitHub Actions
The scraper runs automatically weekly on Tuesday at 3:14 AM EST (8:14 AM UTC) via GitHub Actions.

## 📊 Data Flow

1. **Load Existing Data** - Reads current individual employee JSON files
2. **Scrape New Data** - Collects employee info from EI website
3. **Merge Data** - Updates existing records, preserves computer info
4. **Download Images** - Updates profile images
5. **Save Data** - Writes to individual files in `docs/assets/individual_employees/`

## 🔄 Data Merging Logic

The scraper intelligently merges data:

- **New Employees**: Added to the dataset
- **Existing Employees**: Updated with new info
- **Computer Data**: Preserved from existing records
- **Images**: Downloaded and updated

## ⚙️ Configuration

### Environment Variables
- `HEADLESS`: Run browser in headless mode (default: true)
- `DOWNLOAD_IMAGES`: Download profile images (default: true)
- `TIMEOUT`: Page load timeout in milliseconds (default: 15000)

### Output
- **Employee Data**: Individual JSON files in `docs/assets/individual_employees/`
- **Images**: `docs/assets/images/`
- **Logs**: `weekly_scraper.log`

## 🧪 Testing

Run the test script to verify functionality:

```bash
python test_scraper.py
```

This will:
- Test data loading
- Test employee scraping
- Test data merging
- Test data saving

## 📝 Logging

The scraper creates detailed logs:
- **Console Output**: Real-time progress
- **Log File**: `weekly_scraper.log`
- **GitHub Actions**: Workflow logs

## 🔍 Troubleshooting

### Common Issues

1. **No employees scraped**
   - Check network connection
   - Verify website accessibility
   - Check timeout settings

2. **Image download failures**
   - Verify image URLs
   - Check disk space
   - Review permissions

3. **Data merge issues**
   - Check JSON format
   - Verify email fields
   - Review log files

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance

- **Typical Runtime**: 5-10 minutes
- **Memory Usage**: ~200MB
- **Disk Usage**: ~50MB for images
- **Network**: Downloads ~100-200 images

## 🔒 Security

- **Credentials**: Stored securely in GitHub Secrets
- **Data**: No sensitive information logged
- **Access**: Read-only access to employee directory

---

# AboutMe Computer Information Collector

This application collects comprehensive computer information and can send it to the EmployeeData GitHub Pages website.

## Features

- **System Information Collection**: Gathers detailed computer specs including CPU, GPU, memory, OS, and more
- **GitHub Integration**: Sends data directly to the GitHub repository via repository dispatch API
- **Automatic Processing**: GitHub Actions automatically processes and displays the data on the website
- **Multiple Output Options**: Save locally, send to GitHub, or create GitHub issues

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install requests psutil wmi
   ```

2. **Run the application**:
   ```bash
   python about_me.py
   ```

## Usage

### Basic Usage (Collect and Save Locally)
```bash
python about_me.py
```

### Send Data to GitHub Repository (Recommended)
```bash
python about_me.py --send-to-github --github-token YOUR_GITHUB_TOKEN
```

### Send Data as GitHub Issue (Alternative)
```bash
python about_me.py --send-as-issue --github-token YOUR_GITHUB_TOKEN
```

### Advanced Options
```bash
python about_me.py --send-to-github \
  --github-token YOUR_TOKEN \
  --repo-owner szhang \
  --repo-name EmployeeData \
  --output my_computer_info.json
```

## Command Line Arguments

- `--send-to-github`: Send data to GitHub repository (recommended method)
- `--send-as-issue`: Send data as GitHub issue (alternative method)
- `--github-token`: Your GitHub personal access token (required for sending)
- `--repo-owner`: GitHub repository owner (default: szhang)
- `--repo-name`: GitHub repository name (default: EmployeeData)
- `--output`: Output JSON filename (default: computer_info.json)
- `--no-save`: Don't save to local JSON file

## Getting a GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (Full control of private repositories)
4. Copy the token and use it with `--github-token`

## How It Works

1. **Data Collection**: The script gathers comprehensive system information
2. **GitHub Dispatch**: Data is sent to GitHub via repository dispatch API
3. **GitHub Actions**: Automatically processes the incoming data
4. **Website Display**: Data appears on the EmployeeData website in real-time

## Data Collected

- Computer name and user information
- Operating system details
- Hardware manufacturer and model
- CPU specifications
- GPU information and driver version
- Memory (RAM) details
- System serial number
- Collection timestamp

## Privacy

- All data is sent to the specified GitHub repository
- Data is processed and stored in the `assets/computer_data/` folder
- Individual computer data files are created with timestamps
- A master file (`all_computers.json`) contains all submissions

## Troubleshooting

### "GitHub token required" error
- Make sure you've provided a valid GitHub token with `--github-token`
- Ensure the token has `repo` permissions

### "Failed to send data" error
- Check your internet connection
- Verify the GitHub token is valid and not expired
- Ensure the repository exists and you have access

### WMI errors on Windows
- Run as Administrator if you encounter WMI permission errors
- Install Windows Management Framework if WMI is not available

## Example Output

The script will display a summary like:
```
=== Computer Information Summary ===
Computer Name: DESKTOP-ABC123
User: John Doe (johndoe)
OS: Windows 10
Manufacturer: Dell Inc.
Model: OptiPlex 7090
CPU: Intel(R) Core(TM) i7-10700 CPU @ 2.90GHz
Memory: 17179869184 bytes
GPU: NVIDIA GeForce RTX 3060
Serial Number: ABC123456
========================================
```

---

# Excel to JSON Merger

This standalone script processes 3 Excel files and creates a composite JSON file with employee information linked by human names as keys.

## Files Required

1. `Employee List .xlsx` - Basic employee information (First Name, Last Name, Company, Office, etc.)
2. `GPU by User.xlsx` - Computer/GPU specifications per user
3. `Master Technology List.xlsx` - Employee roles, titles, and office locations

## Installation

```bash
pip install -r requirements_workfiles.txt
```

## Usage

```bash
python excel_to_json_merger.py
```

## Output

The script generates `composite_employees.json` with the following structure:

```json
{
  "summary": {
    "total_employees": 216,
    "employees_with_computers": 52,
    "total_computers": 53,
    "employees_with_roles": 109,
    "generation_timestamp": "2025-09-12T15:08:33.682535"
  },
  "employees": {
    "Employee Name": {
      "full_name": "Employee Name",
      "first_name": "First",
      "last_name": "Last",
      "preferred_name": "",
      "company": "Company Name",
      "office": "Office Location",
      "computers": [
        {
          "computername": "COMPUTER-NAME",
          "username": "username",
          "os": "Operating System",
          "manufacturer": "Manufacturer",
          "model": "Model",
          "total_physical_memory": 16777216.0,
          "cpu": "CPU Model",
          "serial_number": "Serial Number",
          "gpu_name": "GPU Name",
          "gpu_processor": "GPU Processor",
          "gpu_driver": "GPU Driver Version",
          "gpu_memory": 4193280.0,
          "date": "2025-06-27T15:26:00"
        }
      ],
      "role": "Job Role",
      "title": "Job Title",
      "office_location": "Office Location"
    }
  }
}
```

## Key Features

- **Human names as keys**: Each employee is identified by their full name
- **Multiple computers support**: Employees can have multiple computers stored as a list
- **Enhanced fuzzy name matching**: Advanced matching with multiple algorithms:
  - Handles spelling variations and typos
  - Supports common nicknames (Bob/Robert, Mike/Michael, etc.)
  - Token-based matching for different name orders
  - Configurable similarity thresholds
- **Comprehensive data linking**: Combines information from all 3 Excel files
- **Data quality monitoring**: Automatic alerts for data loss and missing information
- **Detailed reporting**: Shows unmatched records and data coverage statistics
- **Standalone operation**: No dependencies on the rest of the repository
- **Intelligent matching**: Uses best-match scoring to avoid duplicate entries

## Data Sources

- **Employee List**: Basic employee information and office assignments
- **GPU by User**: Detailed computer specifications including hardware, OS, and GPU details
- **Master Technology List**: Job roles, titles, and office locations

## Data Quality Monitoring

The script automatically monitors data quality and provides comprehensive alerts for:

### Coverage Alerts
- **Low coverage**: Warns when less than 30% of employees have computer data
- **Missing roles**: Alerts when less than 50% have role information  
- **Missing titles**: Warns when less than 40% have title information
- **Critical gaps**: Flags when less than 20% have complete data from all sources

### Data Loss Alerts
- **Invalid names**: Tracks records with empty, null, or invalid names
- **Data loss by source**: Reports exactly how many records were lost from each Excel file
- **Unmatched records**: Reports records that couldn't be matched between files

### Matching Quality Alerts
- **Low confidence matches**: Flags matches with <90% confidence that may be incorrect
- **Mismatch detection**: Shows potential name mismatches with confidence scores
- **Duplicate prevention**: Tracks when multiple records might match the same employee

## Notes

- **Enhanced matching**: The script uses multiple fuzzy matching algorithms to handle:
  - Spelling variations and typos
  - Common nicknames and shortened names
  - Different name orders (Last, First vs First Last)
  - Middle name variations
- **Smart scoring**: Uses best-match scoring to prevent duplicate entries
- **Fallback handling**: Employees without computer data will have an empty computers array
- **Data expansion**: Creates new entries for employees found in GPU or Tech lists but not in the Employee List
- **Data normalization**: All data is cleaned and normalized during processing
- **Threshold tuning**: Matching threshold can be adjusted (default: 75% similarity)
- **Quality reporting**: Detailed reports show exactly which data is missing and why

---

## 🏗️ Scraper Architecture

The scraper system uses a **simplified, unified architecture** that works for both local development and GitHub Actions.

### Architecture Overview

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

### Key Components

1. **`main.py`** - Single entry point for both local and GitHub Actions
2. **`ScraperOrchestrator`** - Orchestrates the entire scraping process
3. **`UnifiedScraper`** - Core scraper with comprehensive data extraction
4. **`weekly_scraper.py`** - GitHub Actions wrapper

### Benefits

- ✅ **Single Source of Truth**: One scraper, one orchestrator, one flow
- ✅ **No Duplication**: Same logic for local and GitHub Actions
- ✅ **Clear Separation**: Scraper only scrapes, no HTML generation
- ✅ **Simple Maintenance**: Changes in one place affect everything
- ✅ **Consistent Output**: Same JSON structure everywhere

## 🔄 Migration History

### Unified Scraper Migration

The scraper system was refactored to eliminate code duplication by consolidating `SimpleEmployeeScraper` and `CompleteScraper` into a single `UnifiedEmployeeScraper`.

**Benefits of Migration:**
- **Single codebase** - No more duplication
- **Comprehensive data** - All features enabled by default
- **No modes** - One scraper for all use cases
- **Easier maintenance** - Changes in one place
- **Consistent behavior** - Same comprehensive logic everywhere

**What Was Removed:**
- ❌ **HTML Generation**: Moved to static framework in docs folder
- ❌ **Voice Announcements**: Not needed for automated scraping
- ❌ **Multiple Orchestrators**: Consolidated to single ScraperOrchestrator
- ❌ **Development vs Production**: Single flow for all use cases
- ❌ **Complex Mode Logic**: Simplified to single comprehensive scraper

## 📖 Documentation

This comprehensive README covers all components of the EmployeeData system. Each component can be used independently or as part of the complete system.