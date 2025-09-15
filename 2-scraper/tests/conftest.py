"""
Test configuration and fixtures for the Employee Data Scraper test suite.

This module provides common test utilities, fixtures, and configuration
that can be shared across all test scenarios.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Setup test logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestConfig:
    """Configuration class for tests."""
    
    # Base directories
    BASE_DIR = Path(__file__).parent.parent
    TESTS_DIR = Path(__file__).parent
    
    # Test output directories
    TEST_OUTPUT_DIR = TESTS_DIR / "test_outputs"
    TEST_DEBUG_DIR = TESTS_DIR / "test_debug"
    
    # Default test parameters
    DEFAULT_DEBUG_EMPLOYEES = 3
    DEFAULT_TIMEOUT = 10000
    DEFAULT_BASE_URL = "https://ei.ennead.com/employees/1/all-employees"
    
    # Test categories
    PRODUCTION_TESTS = ["production_full", "production_headless"]
    DEBUG_TESTS = ["debug_limited", "quick_debug"]
    SETUP_TESTS = ["credentials"]


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return TestConfig()


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix="scraper_test_")
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_output_dir():
    """Create and cleanup test output directory."""
    output_dir = TestConfig.TEST_OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    yield output_dir
    # Cleanup test outputs
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)


@pytest.fixture
def test_debug_dir():
    """Create and cleanup test debug directory."""
    debug_dir = TestConfig.TEST_DEBUG_DIR
    debug_dir.mkdir(exist_ok=True)
    yield debug_dir
    # Cleanup test debug files
    if debug_dir.exists():
        shutil.rmtree(debug_dir, ignore_errors=True)


class TestRunner:
    """Utility class for running test scenarios."""
    
    @staticmethod
    async def run_scraper_command(
        cmd: list,
        cwd: Optional[Path] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run a scraper command and return results.
        
        Args:
            cmd: Command to run
            cwd: Working directory
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with success, stdout, stderr, return_code, duration
        """
        import time
        import subprocess
        
        start_time = time.time()
        cwd = cwd or TestConfig.BASE_DIR
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            if timeout:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            else:
                stdout, stderr = await process.communicate()
            
            return_code = process.returncode
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "success": return_code == 0,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip(),
                "return_code": return_code,
                "duration": duration
            }
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "return_code": -1,
                "duration": duration
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "duration": duration
            }
    
    @staticmethod
    def check_output_files(expected_files: list, base_dir: Path = None) -> Dict[Path, bool]:
        """
        Check if expected output files exist.
        
        Args:
            expected_files: List of expected file paths
            base_dir: Base directory to resolve relative paths
            
        Returns:
            Dictionary mapping file paths to existence status
        """
        base_dir = base_dir or Path.cwd()
        results = {}
        
        for file_path in expected_files:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            if not file_path.is_absolute():
                file_path = base_dir / file_path
            
            results[file_path] = file_path.exists()
        
        return results
    
    @staticmethod
    def analyze_file_contents(file_path: Path) -> Dict[str, Any]:
        """
        Analyze file contents for test validation.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if not file_path.exists():
            return {"exists": False}
        
        analysis = {"exists": True}
        
        try:
            if file_path.is_file():
                stat = file_path.stat()
                analysis.update({
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "is_file": True,
                    "is_dir": False
                })
                
                # Try to read file contents based on extension
                if file_path.suffix == '.json':
                    try:
                        import json
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        analysis["json_valid"] = True
                        analysis["json_keys"] = list(data.keys()) if isinstance(data, dict) else None
                    except Exception as e:
                        analysis["json_valid"] = False
                        analysis["json_error"] = str(e)
                
                elif file_path.suffix == '.log':
                    try:
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                        analysis["log_lines"] = len(lines)
                        analysis["log_last_line"] = lines[-1].strip() if lines else None
                    except Exception as e:
                        analysis["log_error"] = str(e)
            
            elif file_path.is_dir():
                files = list(file_path.rglob('*'))
                analysis.update({
                    "is_file": False,
                    "is_dir": True,
                    "file_count": len(files),
                    "files": [str(f.relative_to(file_path)) for f in files]
                })
        
        except Exception as e:
            analysis["analysis_error"] = str(e)
        
        return analysis


@pytest.fixture
def test_runner():
    """Provide test runner utility."""
    return TestRunner()


class TestValidator:
    """Utility class for validating test results."""
    
    @staticmethod
    def validate_scraper_output(result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate scraper execution results.
        
        Args:
            result: Result dictionary from TestRunner.run_scraper_command
            
        Returns:
            Validation results
        """
        validation = {
            "execution_success": result["success"],
            "return_code_valid": result["return_code"] in [0, 1],  # 0=success, 1=expected failure
            "has_output": bool(result["stdout"].strip()),
            "error_analysis": None
        }
        
        # Analyze stderr for common issues
        stderr = result["stderr"]
        if stderr:
            validation["error_analysis"] = {
                "has_errors": bool(stderr.strip()),
                "contains_timeout": "timeout" in stderr.lower(),
                "contains_network": any(word in stderr.lower() for word in ["network", "connection", "url"]),
                "contains_browser": any(word in stderr.lower() for word in ["browser", "chrome", "driver"]),
                "contains_credentials": "credential" in stderr.lower()
            }
        
        # Overall validation
        validation["overall_valid"] = (
            validation["execution_success"] and
            validation["return_code_valid"]
        )
        
        return validation
    
    @staticmethod
    def validate_output_files(file_results: Dict[Path, bool], expected_min_files: int = 1) -> Dict[str, Any]:
        """
        Validate output file results.
        
        Args:
            file_results: Results from TestRunner.check_output_files
            expected_min_files: Minimum number of files expected
            
        Returns:
            Validation results
        """
        existing_files = sum(1 for exists in file_results.values() if exists)
        
        validation = {
            "files_exist": existing_files >= expected_min_files,
            "total_expected": len(file_results),
            "total_found": existing_files,
            "missing_files": [str(path) for path, exists in file_results.items() if not exists],
            "existing_files": [str(path) for path, exists in file_results.items() if exists]
        }
        
        validation["overall_valid"] = validation["files_exist"]
        
        return validation


@pytest.fixture
def test_validator():
    """Provide test validator utility."""
    return TestValidator()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with test-specific settings."""
    # Add custom markers
    config.addinivalue_line("markers", "production: Production test scenarios")
    config.addinivalue_line("markers", "debug: Debug test scenarios")
    config.addinivalue_line("markers", "setup: Setup test scenarios")
    config.addinivalue_line("markers", "slow: Tests that take a long time to run")
    config.addinivalue_line("markers", "browser: Tests that require browser interaction")


def pytest_collection_modifyitems(config, items):
    """Modify test items based on configuration."""
    # Add markers based on test names
    for item in items:
        if "production" in item.name:
            item.add_marker(pytest.mark.production)
        if "debug" in item.name:
            item.add_marker(pytest.mark.debug)
        if "credentials" in item.name:
            item.add_marker(pytest.mark.setup)
        if "full" in item.name or "production" in item.name:
            item.add_marker(pytest.mark.slow)
        if "browser" in item.name or "DOM" in item.name:
            item.add_marker(pytest.mark.browser)


# Async test support
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
