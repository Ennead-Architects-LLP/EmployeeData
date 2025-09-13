# EmployeeData - Multi-Component Architecture

A comprehensive employee data management system with 5 distinct components for data collection, processing, and display.

## 🏗️ Repository Structure

```
EmployeeData/
├── 1-website/           # 🌐 Main website (GitHub Pages)
├── 2-scraper/           # 🕛 Daily data collection
├── 3-aboutme/           # 💻 User computer data collection
├── 4-server/            # 🖥️ POST data handler
├── 5-workfiles/         # 📁 Reference materials
└── .github/             # ⚙️ GitHub Actions workflows
```

## 🚀 Quick Start

### 1. Website (Static Hosting)
```bash
cd 1-website
# Deploy to GitHub Pages - website loads data dynamically from JSON
```

### 2. Weekly Scraper
```bash
cd 2-scraper
pip install -r requirements.txt
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
pip install -r requirements.txt
python server.py
```

## 📋 Component Overview

### 1. Website Component (`1-website/`)
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

## 📖 Documentation

See `README_ARCHITECTURE.md` for detailed component documentation and setup instructions.