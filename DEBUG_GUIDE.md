# 🔍 Debug Guide for Employee Data Scraper

This guide provides comprehensive information about debugging the Employee Data Scraper, including tools, techniques, and troubleshooting strategies.

## 📋 Table of Contents

- [Debug Features Overview](#debug-features-overview)
- [Debug Mode Usage](#debug-mode-usage)
- [Debug Tools](#debug-tools)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)
- [Performance Monitoring](#performance-monitoring)
- [Error Analysis](#error-analysis)
- [Content Quality Analysis](#content-quality-analysis)
- [Debug Report Generation](#debug-report-generation)
- [Best Practices](#best-practices)

## 🚀 Debug Features Overview

The Employee Data Scraper includes comprehensive debugging capabilities:

- **Enhanced Logging**: Detailed operation tracking with performance metrics
- **Error Diagnostics**: Automatic error categorization and recovery suggestions
- **Content Analysis**: Data quality assessment and completeness checking
- **Performance Monitoring**: Real-time performance tracking and bottleneck identification
- **Debug Artifacts**: DOM captures, screenshots, and detailed logs
- **Report Generation**: Comprehensive HTML/JSON/Markdown reports

## 🛠️ Debug Mode Usage

### Basic Debug Mode

```bash
# Enable debug mode with default settings (10 employees, DOM capture enabled)
python -m src.main --debug

# Debug with custom employee limit
python -m src.main --debug --debug-employees 5

# Debug without DOM capturing (faster)
python -m src.main --debug --debug-no-dom

# Debug with explicit DOM capturing
python -m src.main --debug --debug-dom
```

### Advanced Debug Options

```bash
# Debug with parallel processing
python -m src.main --debug --parallel --max-workers 2

# Debug with custom timeout
python -m src.main --debug --timeout 30000

# Debug with cleanup of old debug files
python -m src.main --debug --cleanup-debug 20
```

### Debug Help

```bash
# Show detailed debug mode help
python -m src.main --debug-help
```

## 🔧 Debug Tools

### 1. Enhanced Test Script

The improved `test_parallel.py` provides comprehensive testing:

```bash
# Run enhanced parallel testing
python test_parallel.py
```

**Features:**
- Performance comparison between sequential and parallel processing
- Comprehensive error reporting
- Content quality analysis
- Detailed performance metrics
- JSON report generation

### 2. Debug Report Generator

Generate comprehensive debug reports:

```bash
# Generate HTML report
python debug_report_generator.py --input-dir output/debug --output-file debug_report.html

# Generate JSON report
python debug_report_generator.py --format json --output-file debug_report.json

# Include screenshots and DOM captures
python debug_report_generator.py --include-screenshots --include-dom
```

**Report Features:**
- Directory analysis and file counts
- Performance timing analysis
- Content quality assessment
- Error pattern analysis
- Screenshot and DOM capture integration

### 3. Real-time Debug Monitor

Monitor debug output in real-time:

```bash
# Start continuous monitoring
python debug_monitor.py --watch-dir output/debug --refresh-interval 5

# Run one-time analysis
python debug_monitor.py --once

# Export metrics
python debug_monitor.py --once --export-metrics metrics.json
```

**Monitoring Features:**
- Real-time file system watching
- Performance metrics tracking
- Error count monitoring
- Content analysis updates
- Success rate calculation

## 🐛 Troubleshooting Common Issues

### 1. Authentication Issues

**Symptoms:**
- Login failures
- "Authentication" errors in logs
- Empty employee data

**Debug Steps:**
1. Check credentials configuration:
   ```bash
   python -m src.main --setup-credentials
   ```

2. Enable debug mode to capture login process:
   ```bash
   python -m src.main --debug --debug-employees 1
   ```

3. Check debug screenshots in `output/debug/screenshots/`

**Recovery Suggestions:**
- Verify username/password are correct
- Check if credentials have expired
- Test login manually in browser
- Update credentials if needed

### 2. Timeout Issues

**Symptoms:**
- "Timeout" errors in logs
- Slow page loading
- Incomplete data scraping

**Debug Steps:**
1. Increase timeout values:
   ```bash
   python -m src.main --debug --timeout 30000
   ```

2. Check network connectivity
3. Monitor performance metrics:
   ```bash
   python debug_monitor.py --watch-dir output/debug
   ```

**Recovery Suggestions:**
- Increase timeout in configuration
- Check network stability
- Verify target website accessibility
- Consider using retry logic

### 3. Parsing Issues

**Symptoms:**
- "Parse" errors in logs
- Missing employee data
- Incomplete field extraction

**Debug Steps:**
1. Enable DOM capture:
   ```bash
   python -m src.main --debug --debug-dom
   ```

2. Analyze DOM captures in `output/debug/dom_captures/`
3. Check selector validity
4. Compare with expected page structure

**Recovery Suggestions:**
- Update selectors if page structure changed
- Test selectors individually
- Use different parsing strategies
- Enable debug DOM capture for analysis

### 4. Performance Issues

**Symptoms:**
- Slow scraping speed
- High memory usage
- Browser crashes

**Debug Steps:**
1. Monitor performance metrics:
   ```bash
   python debug_monitor.py --watch-dir output/debug
   ```

2. Generate performance report:
   ```bash
   python debug_report_generator.py --format json
   ```

3. Test with different worker counts:
   ```bash
   python test_parallel.py
   ```

**Recovery Suggestions:**
- Reduce parallel workers
- Increase memory limits
- Use sequential processing
- Optimize browser settings

## 📊 Performance Monitoring

### Real-time Metrics

The debug monitor provides real-time performance tracking:

- **Uptime**: How long the monitor has been running
- **File Counts**: Number of files created by type
- **Success Rate**: Percentage of successful operations
- **Error Count**: Total number of errors encountered
- **Performance Timing**: Average times for operations

### Performance Analysis

The debug report generator analyzes:

- **Timing Patterns**: Page load, scraping, browser startup times
- **Bottlenecks**: Operations taking longer than expected
- **Resource Usage**: File sizes and counts
- **Success Rates**: Operation success percentages

### Optimization Recommendations

Based on performance analysis, the system provides:

- **Bottleneck Identification**: Operations that need optimization
- **Resource Recommendations**: Memory and CPU usage suggestions
- **Configuration Tuning**: Optimal settings for your environment
- **Scaling Advice**: When to use parallel vs sequential processing

## ❌ Error Analysis

### Error Categorization

The system automatically categorizes errors:

- **Timeout**: Network or operation timeouts
- **Network**: Connection and DNS issues
- **Authentication**: Login and credential problems
- **Parsing**: Data extraction and parsing errors
- **Browser**: Browser and driver issues
- **Rate Limit**: Throttling and rate limiting
- **Not Found**: Missing content or URLs

### Error Recovery

Each error category includes:

- **Recovery Suggestions**: Specific actions to resolve the issue
- **Debugging Steps**: How to investigate further
- **Prevention Tips**: How to avoid the error in the future

### Error Reporting

Comprehensive error reports include:

- **Error Timeline**: When errors occurred
- **Common Patterns**: Most frequent error types
- **Context Information**: What was happening when errors occurred
- **Recovery Actions**: Suggested next steps

## 📈 Content Quality Analysis

### Data Completeness

The system analyzes:

- **Field Completeness**: Which fields are missing data
- **Record Completeness**: How many complete records exist
- **Data Quality Issues**: Specific problems with data extraction

### Quality Metrics

Key quality indicators:

- **Completeness Score**: Percentage of complete records
- **Field Coverage**: Percentage of fields with data
- **Data Validation**: Email format, required fields, etc.
- **Consistency Checks**: Data format consistency

### Quality Issues

Common quality issues identified:

- **Missing Names**: Employees without names
- **Invalid Emails**: Malformed email addresses
- **Short Bios**: Very brief bio text (possible scraping issues)
- **Missing Images**: Profile images not downloaded
- **Incomplete Data**: Records missing critical information

## 📋 Debug Report Generation

### HTML Reports

Comprehensive visual reports with:

- **Executive Summary**: High-level overview
- **Performance Metrics**: Timing and resource usage
- **Content Analysis**: Data quality assessment
- **Error Analysis**: Error patterns and suggestions
- **Screenshots**: Visual debugging aids
- **DOM Captures**: Page structure analysis

### JSON Reports

Machine-readable reports for:

- **API Integration**: Programmatic access to debug data
- **Automated Analysis**: Script-based debugging
- **Data Export**: Integration with other tools
- **Metrics Tracking**: Performance monitoring

### Markdown Reports

Documentation-friendly reports for:

- **Issue Tracking**: GitHub/GitLab integration
- **Documentation**: Team communication
- **Version Control**: Track changes over time
- **Collaboration**: Share with team members

## 🎯 Best Practices

### Debug Mode Usage

1. **Start Small**: Begin with 1-5 employees for initial debugging
2. **Enable DOM Capture**: Use `--debug-dom` for parsing issues
3. **Monitor Performance**: Use debug monitor for real-time insights
4. **Generate Reports**: Create reports for comprehensive analysis

### Error Handling

1. **Check Logs First**: Always review log files for error details
2. **Use Error Diagnostics**: Leverage automatic error categorization
3. **Follow Recovery Suggestions**: Implement suggested fixes
4. **Test Incrementally**: Fix one issue at a time

### Performance Optimization

1. **Monitor Metrics**: Use debug monitor for performance tracking
2. **Test Different Configurations**: Try various worker counts
3. **Analyze Bottlenecks**: Focus on slowest operations
4. **Optimize Selectively**: Don't optimize everything at once

### Content Quality

1. **Regular Analysis**: Check content quality regularly
2. **Validate Data**: Ensure extracted data is correct
3. **Monitor Completeness**: Track data completeness over time
4. **Fix Issues Promptly**: Address quality issues as they arise

## 🔗 Quick Reference

### Debug Commands

```bash
# Basic debug
python -m src.main --debug

# Advanced debug
python -m src.main --debug --debug-employees 5 --debug-dom --parallel

# Test performance
python test_parallel.py

# Generate report
python debug_report_generator.py --include-screenshots

# Monitor real-time
python debug_monitor.py --watch-dir output/debug
```

### Debug Directories

- `output/debug/dom_captures/` - HTML captures for analysis
- `output/debug/screenshots/` - Visual debugging aids
- `output/debug/logs/` - Detailed operation logs
- `output/debug/reports/` - Generated debug reports

### Key Files

- `test_parallel.py` - Enhanced testing script
- `debug_report_generator.py` - Report generation tool
- `debug_monitor.py` - Real-time monitoring
- `src/services/debug_utilities.py` - Debug utilities library

## 📞 Support

For additional debugging support:

1. **Check Logs**: Review log files for detailed error information
2. **Generate Reports**: Create comprehensive debug reports
3. **Use Monitor**: Monitor real-time performance and errors
4. **Follow Recovery**: Implement suggested recovery actions
5. **Test Incrementally**: Debug one issue at a time

Remember: Debug mode is designed to help you identify and resolve issues quickly. Use the tools provided to get detailed insights into what's happening during the scraping process.
