# Employee Data Scraper Test Suite

This directory contains comprehensive test scenarios for the Employee Data Scraper. The tests cover different configurations and use cases to ensure the scraper works correctly in various environments.

## Test Scenarios

### 1. Production Tests

#### `test_production_full_scraping_without_browser.py`
- **Purpose**: Test full production scraping without browser GUI
- **Configuration**: Headless browser, all employees, images enabled, DOM capture disabled
- **Use Case**: Production deployment, automated runs
- **Command**: `python -m tests.test_production_full_scraping_without_browser`

#### `test_production_headless_with_images.py`
- **Purpose**: Test production scraping with headless browser and image downloading
- **Configuration**: Headless browser, all employees, images enabled
- **Use Case**: Production runs with image collection
- **Command**: `python -m tests.test_production_headless_with_images`

### 2. Debug Tests

#### `test_debugging_limited_employee_with_DOM_with_browser.py`
- **Purpose**: Test debugging with limited employees, DOM capture, and visible browser
- **Configuration**: Visible browser, limited employees (default 10), DOM capture enabled, screenshots enabled
- **Use Case**: Development debugging, selector analysis, visual debugging
- **Command**: `python -m tests.test_debugging_limited_employee_with_DOM_with_browser`

#### `test_quick_debug_no_images.py`
- **Purpose**: Quick debug test without images for fast testing
- **Configuration**: Headless browser, limited employees (default 3), no images, no DOM capture
- **Use Case**: Quick testing, CI/CD, fast validation
- **Command**: `python -m tests.test_quick_debug_no_images`

### 3. Setup Tests

#### `test_credentials_setup.py`
- **Purpose**: Test credentials setup and configuration
- **Configuration**: Tests credentials GUI and configuration access
- **Use Case**: Initial setup, configuration validation
- **Command**: `python -m tests.test_credentials_setup`

## Running Tests

### Run All Tests
```bash
# Run all test scenarios
python -m tests.run_all_tests

# List all available tests
python -m tests.run_all_tests --list
```

### Run Specific Tests
```bash
# Run specific test
python -m tests.run_all_tests --test production_full
python -m tests.run_all_tests --test debug_limited
python -m tests.run_all_tests --test quick_debug
python -m tests.run_all_tests --test production_headless
python -m tests.run_all_tests --test credentials
```

### Run Tests with Custom Parameters
```bash
# Debug tests with custom employee count
python -m tests.run_all_tests --test debug_limited --debug-employees 5

# Debug tests in headless mode
python -m tests.run_all_tests --test debug_limited --headless

# Tests without images
python -m tests.run_all_tests --no-images

# Custom timeout
python -m tests.run_all_tests --timeout 20000
```

### Run Individual Tests
```bash
# Run individual test files directly
python -m tests.test_production_full_scraping_without_browser
python -m tests.test_debugging_limited_employee_with_DOM_with_browser --debug-employees 5
python -m tests.test_quick_debug_no_images --debug-employees 3
python -m tests.test_production_headless_with_images
python -m tests.test_credentials_setup
```

## Test Parameters

### Common Parameters
- `--timeout`: Custom timeout in milliseconds
- `--base-url`: Custom base URL for scraping
- `--debug-employees`: Number of employees to scrape (debug tests only)
- `--headless`: Run browser in headless mode (debug tests only)
- `--no-images`: Skip downloading images

### Test-Specific Parameters
- **Debug tests**: Support `--debug-employees`, `--headless`, `--no-images`
- **Production tests**: Support `--timeout`, `--base-url`
- **Credentials test**: No additional parameters

## Test Output

Each test provides:
- Real-time logging of scraper execution
- Output file verification
- Performance metrics (duration, file counts, sizes)
- Success/failure status with error details
- Comprehensive test summary

## Expected Output Files

### Production Tests
- `assets/{test_name}_output/` - JSON employee data
- `assets/images/` - Downloaded profile images
- `debug/scraper.log` - Execution logs

### Debug Tests
- `assets/{test_name}_output/` - JSON employee data
- `debug/dom_captures/` - HTML files for DOM analysis
- `debug/screenshots/` - PNG screenshots for visual debugging
- `debug/seating_chart/` - Selector analysis files
- `debug/scraper.log` - Execution logs

### Credentials Test
- Verification of credentials module import
- Credentials file existence check
- Configuration validation

## Debugging Features

The test suite includes several debugging features:

1. **Real-time Output**: All tests capture and display scraper output in real-time
2. **File Verification**: Automatic checking of expected output files
3. **Performance Metrics**: Duration tracking and file size analysis
4. **Error Capture**: Detailed error logging and reporting
5. **DOM Analysis**: Debug tests provide DOM captures for selector analysis
6. **Visual Debugging**: Screenshots for visual verification

## Best Practices

1. **Start with Quick Tests**: Use `test_quick_debug_no_images` for initial validation
2. **Use Debug Tests for Development**: `test_debugging_limited_employee_with_DOM_with_browser` for debugging
3. **Validate with Production Tests**: Run production tests before deployment
4. **Check Credentials**: Ensure credentials are properly configured with `test_credentials_setup`
5. **Monitor Logs**: Check `debug/scraper.log` for detailed execution information

## Troubleshooting

### Common Issues
1. **Credentials Not Set**: Run `test_credentials_setup` first
2. **Browser Issues**: Check if browser dependencies are installed
3. **Network Issues**: Verify internet connection and target URL accessibility
4. **File Permissions**: Ensure write permissions for output directories

### Debug Steps
1. Run quick debug test first: `python -m tests.test_quick_debug_no_images`
2. Check logs in `debug/scraper.log`
3. Verify credentials with `python -m tests.test_credentials_setup`
4. Use debug test with visible browser for visual debugging
5. Check output files and their contents

## Integration with CI/CD

The test suite is designed to work with CI/CD pipelines:

```bash
# Quick validation for CI
python -m tests.run_all_tests --test quick_debug

# Full validation for deployment
python -m tests.run_all_tests --test production_full

# Development testing
python -m tests.run_all_tests --test debug_limited --debug-employees 3
```
