#!/usr/bin/env python3
"""
Debug utilities for enhanced troubleshooting and content analysis.

This module provides comprehensive debugging tools for the employee scraper,
including performance monitoring, content analysis, and error diagnostics.
"""

import asyncio
import json
import logging
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import re


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DebugContext:
    """Debug context for tracking operations."""
    operation_id: str
    start_time: float
    context_data: Dict[str, Any]
    performance_metrics: List[PerformanceMetric]
    
    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = []


class PerformanceMonitor:
    """Enhanced performance monitoring with detailed metrics."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.metrics: List[PerformanceMetric] = []
        self.active_operations: Dict[str, float] = {}
        self.contexts: Dict[str, DebugContext] = {}
    
    def start_operation(self, operation: str, context_id: Optional[str] = None) -> str:
        """Start tracking an operation."""
        operation_id = f"{operation}_{int(time.time() * 1000)}"
        start_time = time.time()
        
        self.active_operations[operation_id] = start_time
        
        if context_id and context_id in self.contexts:
            self.contexts[context_id].performance_metrics.append(
                PerformanceMetric(
                    operation=operation,
                    start_time=start_time,
                    end_time=0,
                    duration=0,
                    success=False
                )
            )
        
        self.logger.debug(f"Started operation: {operation} (ID: {operation_id})")
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, 
                     error_message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """End tracking an operation."""
        if operation_id not in self.active_operations:
            self.logger.warning(f"Operation {operation_id} not found in active operations")
            return
        
        start_time = self.active_operations.pop(operation_id)
        end_time = time.time()
        duration = end_time - start_time
        
        metric = PerformanceMetric(
            operation=operation_id.split('_')[0],
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        self.metrics.append(metric)
        
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Operation {metric.operation}: {status} in {duration:.3f}s")
        
        if not success and error_message:
            self.logger.error(f"Operation {metric.operation} failed: {error_message}")
    
    @asynccontextmanager
    async def track_operation(self, operation: str, context_id: Optional[str] = None):
        """Context manager for tracking operations."""
        operation_id = self.start_operation(operation, context_id)
        success = True
        error_message = None
        
        try:
            yield operation_id
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            self.end_operation(operation_id, success, error_message)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.metrics:
            return {"message": "No performance data available"}
        
        successful_metrics = [m for m in self.metrics if m.success]
        failed_metrics = [m for m in self.metrics if not m.success]
        
        total_duration = sum(m.duration for m in self.metrics)
        avg_duration = total_duration / len(self.metrics) if self.metrics else 0
        
        return {
            "total_operations": len(self.metrics),
            "successful_operations": len(successful_metrics),
            "failed_operations": len(failed_metrics),
            "success_rate": (len(successful_metrics) / len(self.metrics)) * 100,
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "fastest_operation": min(self.metrics, key=lambda x: x.duration).operation if self.metrics else None,
            "slowest_operation": max(self.metrics, key=lambda x: x.duration).operation if self.metrics else None,
            "recent_errors": [m.error_message for m in failed_metrics[-5:] if m.error_message]
        }
    
    def export_metrics(self, file_path: Path):
        """Export performance metrics to JSON file."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "performance_summary": self.get_performance_summary(),
            "detailed_metrics": [asdict(metric) for metric in self.metrics]
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Performance metrics exported to {file_path}")


class ContentAnalyzer:
    """Analyzes scraped content for debugging and validation."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze_employee_data(self, employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze employee data for completeness and quality."""
        if not employees:
            return {"error": "No employee data to analyze"}
        
        analysis = {
            "total_employees": len(employees),
            "field_completeness": {},
            "data_quality_issues": [],
            "statistics": {}
        }
        
        # Define expected fields
        expected_fields = [
            "name", "email", "title", "office_location", "bio", 
            "profile_image_url", "profile_url"
        ]
        
        # Analyze field completeness
        field_counts = {}
        for field in expected_fields:
            field_counts[field] = sum(1 for emp in employees if emp.get(field))
        
        analysis["field_completeness"] = {
            field: {
                "count": count,
                "percentage": (count / len(employees)) * 100
            }
            for field, count in field_counts.items()
        }
        
        # Check for data quality issues
        for i, employee in enumerate(employees):
            issues = []
            
            # Check for empty required fields
            if not employee.get("name"):
                issues.append("Missing name")
            if not employee.get("email"):
                issues.append("Missing email")
            
            # Check email format
            email = employee.get("email", "")
            if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                issues.append("Invalid email format")
            
            # Check for very short bio (might indicate scraping issues)
            bio = employee.get("bio", "")
            if bio and len(bio.strip()) < 10:
                issues.append("Very short bio (possible scraping issue)")
            
            if issues:
                analysis["data_quality_issues"].append({
                    "employee_index": i,
                    "employee_name": employee.get("name", "Unknown"),
                    "issues": issues
                })
        
        # Calculate statistics
        analysis["statistics"] = {
            "employees_with_complete_data": sum(
                1 for emp in employees 
                if all(emp.get(field) for field in ["name", "email", "title"])
            ),
            "employees_with_images": sum(1 for emp in employees if emp.get("profile_image_url")),
            "employees_with_bio": sum(1 for emp in employees if emp.get("bio")),
            "average_bio_length": sum(len(emp.get("bio", "")) for emp in employees) / len(employees)
        }
        
        return analysis
    
    def analyze_dom_content(self, dom_content: str, page_url: str) -> Dict[str, Any]:
        """Analyze DOM content for debugging scraping issues."""
        analysis = {
            "page_url": page_url,
            "dom_size": len(dom_content),
            "element_counts": {},
            "potential_issues": [],
            "selectors_found": {}
        }
        
        # Count common elements
        element_patterns = {
            "links": r"<a[^>]*>",
            "images": r"<img[^>]*>",
            "divs": r"<div[^>]*>",
            "spans": r"<span[^>]*>",
            "buttons": r"<button[^>]*>",
            "forms": r"<form[^>]*>",
            "inputs": r"<input[^>]*>"
        }
        
        for element_type, pattern in element_patterns.items():
            matches = re.findall(pattern, dom_content, re.IGNORECASE)
            analysis["element_counts"][element_type] = len(matches)
        
        # Look for potential issues
        if "error" in dom_content.lower():
            analysis["potential_issues"].append("Error text found in DOM")
        
        if "loading" in dom_content.lower():
            analysis["potential_issues"].append("Loading indicators found (possible dynamic content)")
        
        if "javascript" in dom_content.lower():
            analysis["potential_issues"].append("JavaScript content detected")
        
        # Look for common selector patterns
        selector_patterns = {
            "employee_links": r'href="[^"]*employee[^"]*"',
            "profile_images": r'src="[^"]*\.(jpg|jpeg|png|gif)[^"]*"',
            "email_links": r'href="mailto:[^"]*"',
            "office_locations": r'(New York|Shanghai|California)',
        }
        
        for selector_name, pattern in selector_patterns.items():
            matches = re.findall(pattern, dom_content, re.IGNORECASE)
            analysis["selectors_found"][selector_name] = len(matches)
        
        return analysis


class ErrorDiagnostics:
    """Enhanced error diagnostics and recovery suggestions."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_patterns = {
            "timeout": r"(timeout|timed out)",
            "network": r"(network|connection|dns)",
            "authentication": r"(auth|login|credential)",
            "parsing": r"(parse|json|xml|html)",
            "browser": r"(browser|selenium|playwright)",
            "rate_limit": r"(rate limit|throttle|429)",
            "not_found": r"(404|not found|missing)"
        }
    
    def diagnose_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Diagnose an error and provide recovery suggestions."""
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        diagnosis = {
            "error_type": error_type,
            "error_message": str(error),
            "context": context or {},
            "categorized_issues": [],
            "recovery_suggestions": [],
            "debugging_steps": []
        }
        
        # Categorize the error
        for category, pattern in self.error_patterns.items():
            if re.search(pattern, error_message):
                diagnosis["categorized_issues"].append(category)
        
        # Generate recovery suggestions based on error type
        if "timeout" in diagnosis["categorized_issues"]:
            diagnosis["recovery_suggestions"].extend([
                "Increase timeout values in configuration",
                "Check network connectivity",
                "Verify target website is accessible",
                "Consider using retry logic with exponential backoff"
            ])
            diagnosis["debugging_steps"].extend([
                "Check if the website is responding normally",
                "Monitor network requests in browser dev tools",
                "Test with different timeout values"
            ])
        
        if "network" in diagnosis["categorized_issues"]:
            diagnosis["recovery_suggestions"].extend([
                "Check internet connection",
                "Verify DNS resolution",
                "Check firewall/proxy settings",
                "Try accessing the website manually"
            ])
        
        if "authentication" in diagnosis["categorized_issues"]:
            diagnosis["recovery_suggestions"].extend([
                "Verify credentials are correct",
                "Check if credentials have expired",
                "Ensure proper authentication flow",
                "Test login manually"
            ])
        
        if "parsing" in diagnosis["categorized_issues"]:
            diagnosis["recovery_suggestions"].extend([
                "Check if page structure has changed",
                "Verify selectors are still valid",
                "Enable DOM capture for analysis",
                "Test with different parsing strategies"
            ])
            diagnosis["debugging_steps"].extend([
                "Capture DOM content for analysis",
                "Compare current page structure with expected",
                "Test selectors individually"
            ])
        
        if "browser" in diagnosis["categorized_issues"]:
            diagnosis["recovery_suggestions"].extend([
                "Update browser driver",
                "Check browser compatibility",
                "Try different browser options",
                "Verify browser installation"
            ])
        
        if "rate_limit" in diagnosis["categorized_issues"]:
            diagnosis["recovery_suggestions"].extend([
                "Implement rate limiting",
                "Add delays between requests",
                "Use different IP addresses",
                "Contact website administrator"
            ])
        
        if "not_found" in diagnosis["categorized_issues"]:
            diagnosis["recovery_suggestions"].extend([
                "Verify URL is correct",
                "Check if content has moved",
                "Update URL patterns",
                "Test with different URLs"
            ])
        
        # Add general debugging steps
        diagnosis["debugging_steps"].extend([
            "Enable debug mode for detailed logging",
            "Check log files for additional context",
            "Test with a smaller dataset",
            "Verify configuration settings"
        ])
        
        return diagnosis
    
    def generate_error_report(self, errors: List[Exception], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive error report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_errors": len(errors),
            "error_summary": {},
            "detailed_diagnoses": [],
            "common_issues": [],
            "recommended_actions": []
        }
        
        # Analyze each error
        error_types = {}
        for error in errors:
            diagnosis = self.diagnose_error(error, context)
            report["detailed_diagnoses"].append(diagnosis)
            
            error_type = diagnosis["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        report["error_summary"] = error_types
        
        # Find common issues
        all_issues = []
        for diagnosis in report["detailed_diagnoses"]:
            all_issues.extend(diagnosis["categorized_issues"])
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        report["common_issues"] = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Generate recommended actions
        all_suggestions = []
        for diagnosis in report["detailed_diagnoses"]:
            all_suggestions.extend(diagnosis["recovery_suggestions"])
        
        # Get unique suggestions
        unique_suggestions = list(set(all_suggestions))
        report["recommended_actions"] = unique_suggestions
        
        return report


class DebugReportGenerator:
    """Generates comprehensive debug reports."""
    
    def __init__(self, output_dir: Path, logger: Optional[logging.Logger] = None):
        self.output_dir = output_dir
        self.logger = logger or logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor(logger)
        self.content_analyzer = ContentAnalyzer(logger)
        self.error_diagnostics = ErrorDiagnostics(logger)
    
    async def generate_comprehensive_report(self, 
                                          employees: List[Dict[str, Any]] = None,
                                          errors: List[Exception] = None,
                                          dom_samples: List[Tuple[str, str]] = None) -> Path:
        """Generate a comprehensive debug report."""
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "report_type": "comprehensive_debug",
            "performance_analysis": {},
            "content_analysis": {},
            "error_analysis": {},
            "dom_analysis": {},
            "recommendations": []
        }
        
        # Performance analysis
        if self.performance_monitor.metrics:
            report_data["performance_analysis"] = self.performance_monitor.get_performance_summary()
        
        # Content analysis
        if employees:
            report_data["content_analysis"] = self.content_analyzer.analyze_employee_data(employees)
        
        # Error analysis
        if errors:
            report_data["error_analysis"] = self.error_diagnostics.generate_error_report(errors)
        
        # DOM analysis
        if dom_samples:
            dom_analyses = []
            for dom_content, page_url in dom_samples:
                analysis = self.content_analyzer.analyze_dom_content(dom_content, page_url)
                dom_analyses.append(analysis)
            report_data["dom_analysis"] = {
                "total_pages_analyzed": len(dom_analyses),
                "page_analyses": dom_analyses
            }
        
        # Generate recommendations
        recommendations = []
        
        if report_data["content_analysis"].get("data_quality_issues"):
            recommendations.append({
                "category": "data_quality",
                "priority": "high",
                "description": "Data quality issues detected",
                "action": "Review and fix data extraction logic"
            })
        
        if report_data["error_analysis"].get("common_issues"):
            recommendations.append({
                "category": "error_handling",
                "priority": "medium",
                "description": "Common errors identified",
                "action": "Implement better error handling and recovery"
            })
        
        if report_data["performance_analysis"].get("success_rate", 100) < 90:
            recommendations.append({
                "category": "reliability",
                "priority": "high",
                "description": "Low success rate detected",
                "action": "Investigate and fix failing operations"
            })
        
        report_data["recommendations"] = recommendations
        
        # Save report
        report_path = self.output_dir / f"debug_report_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"Comprehensive debug report generated: {report_path}")
        return report_path


# Utility functions for easy integration
def create_debug_context(operation_id: str, context_data: Dict[str, Any] = None) -> DebugContext:
    """Create a new debug context."""
    return DebugContext(
        operation_id=operation_id,
        start_time=time.time(),
        context_data=context_data or {},
        performance_metrics=[]
    )


def log_operation_start(logger: logging.Logger, operation: str, **kwargs):
    """Log the start of an operation."""
    logger.info(f"🚀 Starting {operation}" + (f" - {kwargs}" if kwargs else ""))


def log_operation_end(logger: logging.Logger, operation: str, success: bool, duration: float, **kwargs):
    """Log the end of an operation."""
    status = "✅" if success else "❌"
    logger.info(f"{status} {operation} completed in {duration:.2f}s" + (f" - {kwargs}" if kwargs else ""))


def log_error_with_context(logger: logging.Logger, error: Exception, context: str, **kwargs):
    """Log an error with context information."""
    logger.error(f"❌ Error in {context}: {error}")
    if kwargs:
        logger.error(f"   Context: {kwargs}")
    logger.debug(f"   Traceback: {traceback.format_exc()}")
