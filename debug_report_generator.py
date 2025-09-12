#!/usr/bin/env python3
"""
Comprehensive Debug Report Generator for Employee Data Scraper.

This script generates detailed debug reports by analyzing:
- Performance metrics
- Content quality
- Error patterns
- System configuration
- Debug artifacts (DOM captures, screenshots)

Usage:
    python debug_report_generator.py [options]
    
Options:
    --input-dir DIR          Directory containing debug data (default: output/debug)
    --output-file FILE       Output file for the report (default: debug_report.html)
    --format FORMAT          Report format: html, json, markdown (default: html)
    --include-screenshots    Include screenshots in HTML report
    --include-dom            Include DOM captures in analysis
    --verbose                Enable verbose output
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import base64
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.debug_utilities import PerformanceMonitor, ContentAnalyzer, ErrorDiagnostics


class DebugReportGenerator:
    """Generates comprehensive debug reports from scraper data."""
    
    def __init__(self, input_dir: Path, output_file: Path, format_type: str = "html"):
        self.input_dir = Path(input_dir)
        self.output_file = Path(output_file)
        self.format_type = format_type.lower()
        self.logger = logging.getLogger(__name__)
        
        # Initialize analyzers
        self.performance_monitor = PerformanceMonitor(self.logger)
        self.content_analyzer = ContentAnalyzer(self.logger)
        self.error_diagnostics = ErrorDiagnostics(self.logger)
        
        # Report data
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "input_directory": str(self.input_dir),
            "generator_version": "1.0.0"
        }
    
    def analyze_debug_directory(self) -> Dict[str, Any]:
        """Analyze the debug directory structure and contents."""
        analysis = {
            "directory_exists": self.input_dir.exists(),
            "subdirectories": [],
            "file_counts": {},
            "total_size_mb": 0,
            "recent_files": [],
            "issues": []
        }
        
        if not self.input_dir.exists():
            analysis["issues"].append("Debug directory does not exist")
            return analysis
        
        # Analyze subdirectories
        for subdir in self.input_dir.iterdir():
            if subdir.is_dir():
                subdir_info = {
                    "name": subdir.name,
                    "file_count": len(list(subdir.glob("*"))),
                    "size_mb": sum(f.stat().st_size for f in subdir.rglob("*") if f.is_file()) / (1024 * 1024)
                }
                analysis["subdirectories"].append(subdir_info)
                analysis["total_size_mb"] += subdir_info["size_mb"]
        
        # Count files by type
        for pattern in ["*.json", "*.html", "*.png", "*.jpg", "*.log"]:
            files = list(self.input_dir.rglob(pattern))
            analysis["file_counts"][pattern] = len(files)
        
        # Find recent files
        all_files = list(self.input_dir.rglob("*"))
        recent_files = sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]
        analysis["recent_files"] = [
            {
                "path": str(f.relative_to(self.input_dir)),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "size_mb": f.stat().st_size / (1024 * 1024)
            }
            for f in recent_files if f.is_file()
        ]
        
        return analysis
    
    def analyze_performance_data(self) -> Dict[str, Any]:
        """Analyze performance data from log files and metrics."""
        performance_data = {
            "log_files_found": 0,
            "performance_metrics": {},
            "timing_analysis": {},
            "bottlenecks": []
        }
        
        # Look for log files
        log_files = list(self.input_dir.rglob("*.log"))
        performance_data["log_files_found"] = len(log_files)
        
        # Analyze log files for performance data
        timing_patterns = {
            "page_load": r"page.*load.*?(\d+\.?\d*)\s*ms",
            "scraping_time": r"scraping.*?(\d+\.?\d*)\s*s",
            "browser_startup": r"browser.*start.*?(\d+\.?\d*)\s*s",
            "login_time": r"login.*?(\d+\.?\d*)\s*s"
        }
        
        timing_data = {pattern: [] for pattern in timing_patterns.keys()}
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern_name, pattern in timing_patterns.items():
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    timing_data[pattern_name].extend([float(match) for match in matches])
            except Exception as e:
                self.logger.warning(f"Error reading log file {log_file}: {e}")
        
        # Calculate statistics
        for pattern_name, values in timing_data.items():
            if values:
                performance_data["timing_analysis"][pattern_name] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "median": sorted(values)[len(values) // 2]
                }
        
        # Identify bottlenecks
        for pattern_name, stats in performance_data["timing_analysis"].items():
            if stats["average"] > 10:  # More than 10 seconds
                performance_data["bottlenecks"].append({
                    "operation": pattern_name,
                    "average_time": stats["average"],
                    "suggestion": f"Consider optimizing {pattern_name} - average time is {stats['average']:.2f}s"
                })
        
        return performance_data
    
    def analyze_content_quality(self) -> Dict[str, Any]:
        """Analyze content quality from scraped data."""
        content_analysis = {
            "data_files_found": 0,
            "employee_data_analysis": {},
            "quality_issues": [],
            "completeness_score": 0
        }
        
        # Look for employee data files
        data_files = list(self.input_dir.rglob("*employees*.json"))
        content_analysis["data_files_found"] = len(data_files)
        
        if data_files:
            # Analyze the most recent data file
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    employees_data = json.load(f)
                
                if isinstance(employees_data, list) and employees_data:
                    analysis = self.content_analyzer.analyze_employee_data(employees_data)
                    content_analysis["employee_data_analysis"] = analysis
                    content_analysis["completeness_score"] = analysis.get("statistics", {}).get("employees_with_complete_data", 0)
                    
                    # Extract quality issues
                    quality_issues = analysis.get("data_quality_issues", [])
                    content_analysis["quality_issues"] = quality_issues[:10]  # Top 10 issues
                    
            except Exception as e:
                self.logger.warning(f"Error analyzing employee data: {e}")
                content_analysis["quality_issues"].append(f"Error reading employee data: {e}")
        
        return content_analysis
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns from log files."""
        error_analysis = {
            "error_files_found": 0,
            "error_patterns": {},
            "common_errors": [],
            "error_timeline": []
        }
        
        # Look for error files and log files
        error_files = list(self.input_dir.rglob("*error*.json")) + list(self.input_dir.rglob("*.log"))
        error_analysis["error_files_found"] = len(error_files)
        
        error_patterns = {
            "timeout": r"(timeout|timed out)",
            "network": r"(network|connection|dns)",
            "authentication": r"(auth|login|credential)",
            "parsing": r"(parse|json|xml|html)",
            "browser": r"(browser|selenium|playwright)",
            "rate_limit": r"(rate limit|throttle|429)",
            "not_found": r"(404|not found|missing)"
        }
        
        error_counts = {pattern: 0 for pattern in error_patterns.keys()}
        all_errors = []
        
        for error_file in error_files:
            try:
                with open(error_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Count error patterns
                for pattern_name, pattern in error_patterns.items():
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    error_counts[pattern_name] += len(matches)
                
                # Extract error messages
                error_messages = re.findall(r'ERROR.*?:(.*?)(?:\n|$)', content, re.IGNORECASE)
                all_errors.extend(error_messages)
                
            except Exception as e:
                self.logger.warning(f"Error reading error file {error_file}: {e}")
        
        error_analysis["error_patterns"] = error_counts
        error_analysis["common_errors"] = all_errors[:20]  # Top 20 errors
        
        return error_analysis
    
    def generate_html_report(self, include_screenshots: bool = False, include_dom: bool = False) -> str:
        """Generate HTML debug report."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Employee Scraper Debug Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #007bff; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .section h2 { color: #007bff; margin-top: 0; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .metric-label { font-size: 14px; color: #666; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        .code { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }
        .table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        .table th, .table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background-color: #f8f9fa; }
        .screenshot { max-width: 100%; height: auto; margin: 10px 0; border: 1px solid #ddd; }
        .dom-content { max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Employee Scraper Debug Report</h1>
            <p>Generated on: {timestamp}</p>
            <p>Input Directory: {input_directory}</p>
        </div>
        
        {content}
    </div>
</body>
</html>
        """
        
        # Generate report sections
        sections = []
        
        # Directory Analysis
        dir_analysis = self.analyze_debug_directory()
        sections.append(f"""
        <div class="section">
            <h2>📁 Directory Analysis</h2>
            <div class="metric">
                <div class="metric-value {'success' if dir_analysis['directory_exists'] else 'error'}">
                    {'✓' if dir_analysis['directory_exists'] else '✗'}
                </div>
                <div class="metric-label">Directory Exists</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dir_analysis['total_size_mb']:.1f}</div>
                <div class="metric-label">Total Size (MB)</div>
            </div>
            <div class="metric">
                <div class="metric-value">{sum(dir_analysis['file_counts'].values())}</div>
                <div class="metric-label">Total Files</div>
            </div>
            
            <h3>File Counts by Type</h3>
            <table class="table">
                <tr><th>File Type</th><th>Count</th></tr>
                {''.join(f'<tr><td>{file_type}</td><td>{count}</td></tr>' for file_type, count in dir_analysis['file_counts'].items())}
            </table>
            
            {f"<h3>Recent Files</h3><table class='table'><tr><th>File</th><th>Modified</th><th>Size (MB)</th></tr>{''.join(f'<tr><td>{f[\"path\"]}</td><td>{f[\"modified\"]}</td><td>{f[\"size_mb\"]:.2f}</td></tr>' for f in dir_analysis['recent_files'])}</table>" if dir_analysis['recent_files'] else ""}
        </div>
        """)
        
        # Performance Analysis
        perf_analysis = self.analyze_performance_data()
        sections.append(f"""
        <div class="section">
            <h2>⚡ Performance Analysis</h2>
            <div class="metric">
                <div class="metric-value">{perf_analysis['log_files_found']}</div>
                <div class="metric-label">Log Files Found</div>
            </div>
            
            <h3>Timing Analysis</h3>
            {f"<table class='table'><tr><th>Operation</th><th>Count</th><th>Average (s)</th><th>Min (s)</th><th>Max (s)</th></tr>{''.join(f'<tr><td>{op}</td><td>{stats[\"count\"]}</td><td>{stats[\"average\"]:.2f}</td><td>{stats[\"min\"]:.2f}</td><td>{stats[\"max\"]:.2f}</td></tr>' for op, stats in perf_analysis['timing_analysis'].items())}</table>" if perf_analysis['timing_analysis'] else "<p>No timing data found</p>"}
            
            {f"<h3>Performance Bottlenecks</h3><ul>{''.join(f'<li class=\"warning\">{bottleneck[\"suggestion\"]}</li>' for bottleneck in perf_analysis['bottlenecks'])}</ul>" if perf_analysis['bottlenecks'] else ""}
        </div>
        """)
        
        # Content Quality Analysis
        content_analysis = self.analyze_content_quality()
        sections.append(f"""
        <div class="section">
            <h2>📊 Content Quality Analysis</h2>
            <div class="metric">
                <div class="metric-value">{content_analysis['data_files_found']}</div>
                <div class="metric-label">Data Files Found</div>
            </div>
            <div class="metric">
                <div class="metric-value">{content_analysis['completeness_score']}</div>
                <div class="metric-label">Complete Records</div>
            </div>
            
            {f"<h3>Employee Data Statistics</h3><div class='code'>{json.dumps(content_analysis['employee_data_analysis'].get('statistics', {}), indent=2)}</div>" if content_analysis['employee_data_analysis'] else ""}
            
            {f"<h3>Quality Issues</h3><ul>{''.join(f'<li class=\"warning\">Employee {issue[\"employee_name\"]}: {', '.join(issue[\"issues\"])}</li>' for issue in content_analysis['quality_issues'][:5])}</ul>" if content_analysis['quality_issues'] else ""}
        </div>
        """)
        
        # Error Analysis
        error_analysis = self.analyze_error_patterns()
        sections.append(f"""
        <div class="section">
            <h2>❌ Error Analysis</h2>
            <div class="metric">
                <div class="metric-value">{error_analysis['error_files_found']}</div>
                <div class="metric-label">Error Files Found</div>
            </div>
            
            <h3>Error Patterns</h3>
            <table class="table">
                <tr><th>Error Type</th><th>Count</th></tr>
                {''.join(f'<tr><td>{error_type}</td><td>{count}</td></tr>' for error_type, count in error_analysis['error_patterns'].items() if count > 0)}
            </table>
            
            {f"<h3>Recent Errors</h3><div class='code'>{'<br>'.join(error_analysis['common_errors'][:10])}</div>" if error_analysis['common_errors'] else ""}
        </div>
        """)
        
        # Screenshots section
        if include_screenshots:
            screenshot_files = list(self.input_dir.rglob("*.png")) + list(self.input_dir.rglob("*.jpg"))
            if screenshot_files:
                sections.append(f"""
                <div class="section">
                    <h2>📸 Screenshots</h2>
                    {''.join(f'<div><h4>{screenshot.name}</h4><img src="data:image/png;base64,{base64.b64encode(screenshot.read_bytes()).decode()}" class="screenshot" alt="{screenshot.name}"></div>' for screenshot in screenshot_files[:10])}
                </div>
                """)
        
        # DOM Analysis
        if include_dom:
            dom_files = list(self.input_dir.rglob("*.html"))
            if dom_files:
                sections.append(f"""
                <div class="section">
                    <h2>🌐 DOM Analysis</h2>
                    {''.join(f'<div><h4>{dom_file.name}</h4><div class="dom-content">{dom_file.read_text(encoding="utf-8")[:1000]}...</div></div>' for dom_file in dom_files[:5])}
                </div>
                """)
        
        # Generate final HTML
        content = '\n'.join(sections)
        return html_template.format(
            timestamp=self.report_data["timestamp"],
            input_directory=self.report_data["input_directory"],
            content=content
        )
    
    def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON debug report."""
        return {
            **self.report_data,
            "directory_analysis": self.analyze_debug_directory(),
            "performance_analysis": self.analyze_performance_data(),
            "content_analysis": self.analyze_content_quality(),
            "error_analysis": self.analyze_error_patterns()
        }
    
    def generate_markdown_report(self) -> str:
        """Generate Markdown debug report."""
        md_content = f"""# Employee Scraper Debug Report

**Generated:** {self.report_data['timestamp']}  
**Input Directory:** {self.report_data['input_directory']}

## Directory Analysis

"""
        
        dir_analysis = self.analyze_debug_directory()
        md_content += f"- **Directory Exists:** {'✓' if dir_analysis['directory_exists'] else '✗'}\n"
        md_content += f"- **Total Size:** {dir_analysis['total_size_mb']:.1f} MB\n"
        md_content += f"- **Total Files:** {sum(dir_analysis['file_counts'].values())}\n\n"
        
        md_content += "### File Counts by Type\n"
        for file_type, count in dir_analysis['file_counts'].items():
            md_content += f"- **{file_type}:** {count}\n"
        
        # Add other sections...
        perf_analysis = self.analyze_performance_data()
        md_content += f"\n## Performance Analysis\n\n"
        md_content += f"- **Log Files Found:** {perf_analysis['log_files_found']}\n"
        
        if perf_analysis['timing_analysis']:
            md_content += "\n### Timing Analysis\n\n"
            md_content += "| Operation | Count | Average (s) | Min (s) | Max (s) |\n"
            md_content += "|-----------|-------|-------------|---------|----------|\n"
            for op, stats in perf_analysis['timing_analysis'].items():
                md_content += f"| {op} | {stats['count']} | {stats['average']:.2f} | {stats['min']:.2f} | {stats['max']:.2f} |\n"
        
        return md_content
    
    def generate_report(self, include_screenshots: bool = False, include_dom: bool = False) -> None:
        """Generate the debug report in the specified format."""
        self.logger.info(f"Generating {self.format_type} debug report...")
        
        if self.format_type == "html":
            content = self.generate_html_report(include_screenshots, include_dom)
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        elif self.format_type == "json":
            content = self.generate_json_report()
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2)
        
        elif self.format_type == "markdown":
            content = self.generate_markdown_report()
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")
        
        self.logger.info(f"Debug report generated: {self.output_file}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Generate comprehensive debug reports for Employee Data Scraper")
    parser.add_argument("--input-dir", type=str, default="output/debug", 
                       help="Directory containing debug data")
    parser.add_argument("--output-file", type=str, default="debug_report.html",
                       help="Output file for the report")
    parser.add_argument("--format", type=str, choices=["html", "json", "markdown"], 
                       default="html", help="Report format")
    parser.add_argument("--include-screenshots", action="store_true",
                       help="Include screenshots in HTML report")
    parser.add_argument("--include-dom", action="store_true",
                       help="Include DOM captures in analysis")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Generate report
    generator = DebugReportGenerator(
        input_dir=Path(args.input_dir),
        output_file=Path(args.output_file),
        format_type=args.format
    )
    
    try:
        generator.generate_report(
            include_screenshots=args.include_screenshots,
            include_dom=args.include_dom
        )
        print(f"✅ Debug report generated successfully: {args.output_file}")
    except Exception as e:
        print(f"❌ Error generating debug report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
