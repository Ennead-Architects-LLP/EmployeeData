# Daily Employee Data Scraper

This component handles daily data collection from the Ennead employee directory website.

## 🎯 Purpose

- **Daily Data Collection**: Scrapes employee data from EI website
- **Image Download**: Downloads and updates profile images
- **Data Merging**: Preserves existing computer data while updating employee info
- **JSON Updates**: Saves data directly to website assets folder

## 🚀 Features

- ✅ **No HTML Generation** - Focuses only on data collection
- ✅ **Preserves Computer Data** - Keeps existing computer info intact
- ✅ **Image Management** - Downloads and updates profile images
- ✅ **Incremental Updates** - Only updates changed data
- ✅ **Automated Scheduling** - Runs daily via GitHub Actions

## 📁 Structure

```
2-scraper/
├── daily_scraper.py          # Main daily scraper script
├── test_scraper.py           # Test script
├── requirements.txt          # Dependencies
├── src/                      # Source code
│   ├── core/
│   │   ├── data_orchestrator.py  # Data-only orchestrator
│   │   ├── scraper.py            # Employee scraper
│   │   └── models.py             # Data models
│   ├── services/
│   │   └── image_downloader.py   # Image download service
│   └── config/
│       └── settings.py           # Configuration
└── README.md                # This file
```

## 🔧 Usage

### Manual Run
```bash
cd 2-scraper
pip install -r requirements.txt
python daily_scraper.py
```

### Test Run
```bash
cd 2-scraper
python test_scraper.py
```

### GitHub Actions
The scraper runs automatically daily at midnight UTC via GitHub Actions.

## 📊 Data Flow

1. **Load Existing Data** - Reads current `employees_data.json`
2. **Scrape New Data** - Collects employee info from EI website
3. **Merge Data** - Updates existing records, preserves computer info
4. **Download Images** - Updates profile images
5. **Save Data** - Writes to `1-website/assets/employees_data.json`

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
- **Employee Data**: `1-website/assets/employees_data.json`
- **Images**: `1-website/assets/images/`
- **Logs**: `daily_scraper.log`

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
- **Log File**: `daily_scraper.log`
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
