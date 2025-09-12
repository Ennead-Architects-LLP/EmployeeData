#!/usr/bin/env python3
"""
Real-time Debug Monitor for Employee Data Scraper.

This script provides real-time monitoring of the scraper's debug output,
including performance metrics, error tracking, and content analysis.

Usage:
    python debug_monitor.py [options]
    
Options:
    --watch-dir DIR          Directory to watch for debug files (default: output/debug)
    --refresh-interval SEC   Refresh interval in seconds (default: 5)
    --log-level LEVEL        Log level (default: INFO)
    --export-metrics         Export metrics to JSON file
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.debug_utilities import PerformanceMonitor, ContentAnalyzer, ErrorDiagnostics


class DebugFileHandler(FileSystemEventHandler):
    """Handles file system events for debug monitoring."""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
    
    def on_created(self, event):
        if not event.is_directory:
            self.monitor.on_file_created(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.monitor.on_file_modified(event.src_path)


class DebugMonitor:
    """Real-time debug monitor for the scraper."""
    
    def __init__(self, watch_dir: Path, refresh_interval: int = 5):
        self.watch_dir = Path(watch_dir)
        self.refresh_interval = refresh_interval
        self.logger = logging.getLogger(__name__)
        
        # Initialize analyzers
        self.performance_monitor = PerformanceMonitor(self.logger)
        self.content_analyzer = ContentAnalyzer(self.logger)
        self.error_diagnostics = ErrorDiagnostics(self.logger)
        
        # Monitoring state
        self.start_time = time.time()
        self.file_counts = {}
        self.last_analysis = {}
        self.error_count = 0
        self.success_count = 0
        
        # Setup file watcher
        self.observer = Observer()
        self.event_handler = DebugFileHandler(self)
        self.observer.schedule(self.event_handler, str(self.watch_dir), recursive=True)
    
    def on_file_created(self, file_path: str):
        """Handle new file creation."""
        file_path = Path(file_path)
        file_type = file_path.suffix.lower()
        
        if file_type not in self.file_counts:
            self.file_counts[file_type] = 0
        self.file_counts[file_type] += 1
        
        self.logger.info(f"📁 New file created: {file_path.name} ({file_type})")
        
        # Analyze based on file type
        if file_type == '.json' and 'employee' in file_path.name.lower():
            self.analyze_employee_data(file_path)
        elif file_type == '.log':
            self.analyze_log_file(file_path)
        elif file_type in ['.png', '.jpg']:
            self.logger.info(f"📸 Screenshot captured: {file_path.name}")
    
    def on_file_modified(self, file_path: str):
        """Handle file modification."""
        file_path = Path(file_path)
        self.logger.debug(f"📝 File modified: {file_path.name}")
    
    def analyze_employee_data(self, file_path: Path):
        """Analyze employee data file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                employees_data = json.load(f)
            
            if isinstance(employees_data, list):
                analysis = self.content_analyzer.analyze_employee_data(employees_data)
                self.last_analysis['employee_data'] = analysis
                
                self.logger.info(f"📊 Employee data analysis: {len(employees_data)} employees")
                self.logger.info(f"   Complete records: {analysis.get('statistics', {}).get('employees_with_complete_data', 0)}")
                self.logger.info(f"   Quality issues: {len(analysis.get('data_quality_issues', []))}")
                
                self.success_count += 1
            else:
                self.logger.warning(f"⚠️ Invalid employee data format in {file_path.name}")
                
        except Exception as e:
            self.logger.error(f"❌ Error analyzing employee data {file_path.name}: {e}")
            self.error_count += 1
    
    def analyze_log_file(self, file_path: Path):
        """Analyze log file for errors and performance."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count errors
            error_count = content.count('ERROR')
            warning_count = content.count('WARNING')
            
            if error_count > 0:
                self.error_count += error_count
                self.logger.warning(f"⚠️ Found {error_count} errors in {file_path.name}")
            
            if warning_count > 0:
                self.logger.info(f"⚠️ Found {warning_count} warnings in {file_path.name}")
            
            # Extract performance metrics
            import re
            timing_patterns = {
                'page_load': r'page.*load.*?(\d+\.?\d*)\s*ms',
                'scraping_time': r'scraping.*?(\d+\.?\d*)\s*s',
                'browser_startup': r'browser.*start.*?(\d+\.?\d*)\s*s'
            }
            
            for pattern_name, pattern in timing_patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    times = [float(match) for match in matches]
                    avg_time = sum(times) / len(times)
                    self.logger.info(f"⏱️ {pattern_name}: {avg_time:.2f}s average")
                    
        except Exception as e:
            self.logger.error(f"❌ Error analyzing log file {file_path.name}: {e}")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current status summary."""
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': f"{int(uptime // 60)}m {int(uptime % 60)}s",
            'file_counts': self.file_counts,
            'total_files': sum(self.file_counts.values()),
            'error_count': self.error_count,
            'success_count': self.success_count,
            'success_rate': (self.success_count / (self.success_count + self.error_count) * 100) if (self.success_count + self.error_count) > 0 else 0,
            'last_analysis': self.last_analysis
        }
    
    def print_status(self):
        """Print current status to console."""
        status = self.get_status_summary()
        
        print("\n" + "="*60)
        print("🔍 DEBUG MONITOR STATUS")
        print("="*60)
        print(f"⏱️  Uptime: {status['uptime_formatted']}")
        print(f"📁 Total Files: {status['total_files']}")
        print(f"✅ Success Count: {status['success_count']}")
        print(f"❌ Error Count: {status['error_count']}")
        print(f"📊 Success Rate: {status['success_rate']:.1f}%")
        
        if status['file_counts']:
            print("\n📁 Files by Type:")
            for file_type, count in status['file_counts'].items():
                print(f"   {file_type}: {count}")
        
        if status['last_analysis'].get('employee_data'):
            analysis = status['last_analysis']['employee_data']
            print(f"\n📊 Latest Employee Data Analysis:")
            print(f"   Total Employees: {analysis.get('total_employees', 0)}")
            print(f"   Complete Records: {analysis.get('statistics', {}).get('employees_with_complete_data', 0)}")
            print(f"   Quality Issues: {len(analysis.get('data_quality_issues', []))}")
        
        print("="*60)
    
    def export_metrics(self, output_file: Path):
        """Export current metrics to JSON file."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'monitor_status': self.get_status_summary(),
            'performance_summary': self.performance_monitor.get_performance_summary()
        }
        
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        self.logger.info(f"📊 Metrics exported to {output_file}")
    
    def start_monitoring(self):
        """Start the debug monitoring."""
        self.logger.info(f"🚀 Starting debug monitor for {self.watch_dir}")
        self.logger.info(f"⏱️  Refresh interval: {self.refresh_interval} seconds")
        
        # Start file watcher
        self.observer.start()
        
        try:
            while True:
                self.print_status()
                time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            self.logger.info("🛑 Debug monitor stopped by user")
        finally:
            self.observer.stop()
            self.observer.join()
    
    def run_once(self):
        """Run analysis once without continuous monitoring."""
        self.logger.info(f"🔍 Running one-time analysis of {self.watch_dir}")
        
        if not self.watch_dir.exists():
            self.logger.error(f"❌ Watch directory does not exist: {self.watch_dir}")
            return
        
        # Analyze existing files
        for file_path in self.watch_dir.rglob("*"):
            if file_path.is_file():
                self.on_file_created(str(file_path))
        
        self.print_status()


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Real-time Debug Monitor for Employee Data Scraper")
    parser.add_argument("--watch-dir", type=str, default="output/debug",
                       help="Directory to watch for debug files")
    parser.add_argument("--refresh-interval", type=int, default=5,
                       help="Refresh interval in seconds")
    parser.add_argument("--log-level", type=str, default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Log level")
    parser.add_argument("--export-metrics", type=str,
                       help="Export metrics to JSON file")
    parser.add_argument("--once", action="store_true",
                       help="Run analysis once instead of continuous monitoring")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create monitor
    monitor = DebugMonitor(
        watch_dir=Path(args.watch_dir),
        refresh_interval=args.refresh_interval
    )
    
    try:
        if args.once:
            monitor.run_once()
        else:
            monitor.start_monitoring()
        
        if args.export_metrics:
            monitor.export_metrics(Path(args.export_metrics))
            
    except Exception as e:
        logging.error(f"❌ Monitor error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
