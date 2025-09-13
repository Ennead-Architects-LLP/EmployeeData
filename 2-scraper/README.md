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
pip install -r requirements.txt
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
5. **Save Data** - Writes to individual files in `1-website/assets/individual_employees/`

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
- **Employee Data**: Individual JSON files in `1-website/assets/individual_employees/`
- **Images**: `1-website/assets/images/`
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
