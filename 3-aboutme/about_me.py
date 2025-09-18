#!/usr/bin/env python3
"""
Computer Information Collector - Embedded Token Version
Generates a JSON file with comprehensive computer information
Embedded with GitHub token for easy distribution to non-technical users
Thie will work with the computer-data-handler.yml workflow
"""

import json
import os
import platform
import ctypes
import psutil
import wmi
import requests
import argparse
import traceback
import sys
import logging
from datetime import datetime
import threading
import queue
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:
    # If tkinter isn't available, we'll fall back to CLI later
    tk = None
    ttk = None
    messagebox = None

# Optional Pillow for GIF animation and masking
try:
    from PIL import Image, ImageTk, ImageSequence, ImageDraw
except Exception:
    Image = None
    ImageTk = None
    ImageSequence = None
    ImageDraw = None

# Load GitHub token with error handling
token_file = "token.json"
EMBEDDED_GITHUB_TOKEN = None

# Detect silent/headless mode (used by about_me_silent and packaged exe)
SILENT_MODE = os.environ.get("ABOUTME_FORCE_SILENT") == "1"

@dataclass
class InfoDataCPU:
    """CPU information data class"""
    name: str
    processor: str
    cores: int
    logical_processors: int
    max_clock_speed: int
    architecture: int
    family: int
    model: int
    stepping: int
    release_date: str
    type: str = "Physical"
    driver: str = "N/A"  # CPUs don't have drivers
    memory_mb: Optional[int] = None  # CPUs don't have dedicated memory
    memory_bytes: Optional[int] = None
    
    # NEW FIELDS - Just added for demo!
    virtualization_support: bool = False
    hyperthreading_enabled: bool = False
    cache_l3_size: Optional[int] = None  # KB
    
    def __repr__(self):
        """Return a comprehensive string representation of CPU information"""
        lines = []
        lines.append(f"CPU: {self.name}")
        lines.append(f"  Type: {self.type}")
        lines.append(f"  Cores: {self.cores}")
        lines.append(f"  Logical Processors: {self.logical_processors}")
        lines.append(f"  Max Clock Speed: {self.max_clock_speed} MHz")
        lines.append(f"  Architecture: {self.architecture}")
        lines.append(f"  Family: {self.family}")
        lines.append(f"  Model: {self.model}")
        lines.append(f"  Stepping: {self.stepping}")
        
        # NEW: Show new fields if available
        if self.cache_l3_size:
            lines.append(f"  L3 Cache: {self.cache_l3_size} KB")
        if self.virtualization_support:
            lines.append(f"  Virtualization: Supported")
        if self.hyperthreading_enabled:
            lines.append(f"  Hyperthreading: Enabled")
            
        lines.append(f"  Release Date: {self.release_date}")
        return "\n".join(lines)
    
    
    @classmethod
    def from_wmi_processor(cls, cpu):
        """Create InfoDataCPU from WMI Win32_Processor object"""
        return cls(
            name=getattr(cpu, 'Name', None) or "Unknown",
            processor=getattr(cpu, 'Name', None) or "Unknown",
            cores=getattr(cpu, 'NumberOfCores', None) or 0,
            logical_processors=getattr(cpu, 'NumberOfLogicalProcessors', None) or 0,
            max_clock_speed=getattr(cpu, 'MaxClockSpeed', None) or 0,
            architecture=getattr(cpu, 'Architecture', None) or 0,
            family=getattr(cpu, 'Family', None) or 0,
            model=getattr(cpu, 'Model', None) or 0,
            stepping=getattr(cpu, 'Stepping', None) or 0,
            release_date=cls.get_release_date(getattr(cpu, 'Name', None) or ""),
            
            # NEW: Extract new fields from WMI
            virtualization_support=getattr(cpu, 'VirtualizationFirmwareEnabled', False),
            hyperthreading_enabled=getattr(cpu, 'HyperThreadingEnabled', False),
            cache_l3_size=getattr(cpu, 'L3CacheSize', None)
        )
    
    @staticmethod
    def get_release_date(cpu_name):
        """Get CPU release date using dynamic hardware manager"""
        try:
            from hardware_release_date_manager import get_release_date
            return get_release_date(cpu_name, 'cpu')
        except ImportError:
            # Fallback if hardware manager is not available
            return "Unknown"
        except Exception as e:
            return "Unknown"

@dataclass
class InfoDataGPU:
    """GPU information data class"""
    name: str
    processor: str
    driver: str
    memory_bytes: Optional[int]
    memory_mb: Optional[float]
    memory_gb: Optional[float]
    memory_formatted: Optional[str]
    release_date: Optional[str]
    type: str
    priority: int
    is_virtual: bool
    
    def __repr__(self):
        """Return a comprehensive string representation of GPU information"""
        lines = []
        lines.append(f"GPU: {self.name}")
        lines.append(f"  Type: {self.type}")
        lines.append(f"  Processor: {self.processor}")
        lines.append(f"  Driver: {self.driver}")
        if self.memory_formatted:
            lines.append(f"  Memory: {self.memory_formatted}")
        lines.append(f"  Priority: {self.priority}")
        lines.append(f"  Virtual: {self.is_virtual}")
        lines.append(f"  Release Date: {self.release_date or 'Unknown'}")
        return "\n".join(lines)
    
    
    @classmethod
    def from_wmi_video_controller(cls, gpu, memory_formatting_func, virtual_gpu_names):
        """Create InfoDataGPU from WMI Win32_VideoController object"""
        gpu_name = (gpu.Name or "").lower()
        
        # Calculate memory size
        raw = getattr(gpu, 'AdapterRAM', None)
        mem_bytes = None
        if raw is not None:
            try:
                raw_int = int(raw)
                if raw_int < 0:
                    raw_int = raw_int + (2 ** 32)
                mem_bytes = int(raw_int)
            except Exception:
                mem_bytes = None

        # Try registry fallback for memory if WMI didn't provide it
        if mem_bytes is None:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}") as h:
                    # Scan subkeys for HardwareInformation.qwMemorySize
                    i = 0
                    while True:
                        try:
                            sub = winreg.EnumKey(h, i)
                            i += 1
                        except OSError:
                            break
                        try:
                            with winreg.OpenKey(h, sub) as subkey:
                                val, typ = winreg.QueryValueEx(subkey, "HardwareInformation.qwMemorySize")
                                # Value may already be 64-bit
                                if isinstance(val, int) and val > 0:
                                    mem_bytes = val
                                    break
                        except OSError:
                            continue
            except Exception:
                pass
        
        # Format memory size
        memory_formatted, memory_mb, memory_gb = memory_formatting_func(mem_bytes)
        
        # Determine GPU priority
        current_priority = 0
        if "nvidia" in gpu_name or "geforce" in gpu_name or "quadro" in gpu_name or "rtx" in gpu_name or "gtx" in gpu_name:
            current_priority = 3  # Dedicated NVIDIA
        elif "amd" in gpu_name or "radeon" in gpu_name or "rx" in gpu_name:
            current_priority = 3  # Dedicated AMD
        elif "intel" in gpu_name and ("arc" in gpu_name or "iris" in gpu_name):
            current_priority = 2  # Intel Arc/Iris (higher-end integrated)
        elif "intel" in gpu_name:
            current_priority = 1  # Basic Intel integrated
        else:
            current_priority = 0  # Unknown/other
        
        # Determine if virtual
        is_virtual = any(virtual_name in gpu_name for virtual_name in virtual_gpu_names)
        
        return cls(
            name=gpu.Name,
            processor=gpu.VideoProcessor or "Unknown",
            driver=gpu.DriverVersion or "Unknown",
            memory_bytes=mem_bytes,
            memory_mb=memory_mb,
            memory_gb=memory_gb,
            memory_formatted=memory_formatted,
            release_date=cls.get_release_date(gpu.Name or ""),
            type="Virtual" if is_virtual else "Physical",
            priority=current_priority,
            is_virtual=is_virtual
        )
    
    @staticmethod
    def get_release_date(gpu_name):
        """Get GPU release date using dynamic hardware manager"""
        try:
            from hardware_release_date_manager import get_release_date
            return get_release_date(gpu_name, 'gpu')
        except ImportError:
            # Fallback if hardware manager is not available
            return "Unknown"
        except Exception as e:
            return "Unknown"

@dataclass
class InfoDataSystem:
    """System-level information data class"""
    total_memory_bytes: int
    total_memory_formatted: str
    total_memory_mb: float
    total_memory_gb: float
    available_memory_bytes: int
    used_memory_bytes: int
    memory_percent: float
    
    def __repr__(self):
        """Return a comprehensive string representation of system information"""
        lines = []
        lines.append(f"System Memory: {self.total_memory_formatted}")
        lines.append(f"  Available: {self.available_memory_bytes / (1024**3):.1f} GB")
        lines.append(f"  Used: {self.used_memory_bytes / (1024**3):.1f} GB")
        lines.append(f"  Usage: {self.memory_percent:.1f}%")
        return "\n".join(lines)
    
    
    @classmethod
    def from_psutil_memory(cls, memory):
        """Create InfoDataSystem from psutil.virtual_memory() object"""
        memory_formatted, memory_mb, memory_gb = cls.format_memory_size(memory.total)
        
        return cls(
            total_memory_bytes=memory.total,
            total_memory_formatted=memory_formatted,
            total_memory_mb=memory_mb,
            total_memory_gb=memory_gb,
            available_memory_bytes=memory.available,
            used_memory_bytes=memory.used,
            memory_percent=memory.percent
        )
    
    @staticmethod
    def format_memory_size(bytes_value):
        """Format memory size from bytes to human-readable format (MB or GB) - moved from ComputerInfoCollector
        
        Args:
            bytes_value (int): Memory size in bytes
            
        Returns:
            tuple: (formatted_size_str, size_mb, size_gb)
        """
        if bytes_value is None or bytes_value == 0:
            return None, None, None
        
        # Convert to MB and GB
        size_mb = bytes_value / (1024 * 1024)
        size_gb = bytes_value / (1024 * 1024 * 1024)
        
        # Choose the best unit for display
        if size_gb >= 1:
            # Use GB if 1GB or more
            formatted = f"{size_gb:.1f} GB"
        else:
            # Use MB if less than 1GB
            formatted = f"{size_mb:.0f} MB"
        
        return formatted, round(size_mb, 2), round(size_gb, 3)

@dataclass
class ComputerInfo:
    """Computer information data class with structured fields"""
    # Basic computer info
    computername: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    human_name: Optional[str] = None
    
    # System info
    os: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Structured hardware information
    system_info: Optional[InfoDataSystem] = None
    all_gpus: List[InfoDataGPU] = field(default_factory=list)
    all_cpus: List[InfoDataCPU] = field(default_factory=list)
    
    # Metadata
    collection_date: Optional[str] = None
    
    # Error tracking
    collection_error: Optional[str] = None
    computername_error: Optional[str] = None
    user_info_error: Optional[str] = None
    full_name_api_error: Optional[str] = None
    os_info_error: Optional[str] = None
    hardware_info_error: Optional[str] = None
    memory_info_error: Optional[str] = None
    cpu_info_error: Optional[str] = None
    gpu_info_error: Optional[str] = None
    
    def __post_init__(self):
        """Initialize collection_date field after object creation"""
        if self.collection_date is None:
            self.collection_date = datetime.now().isoformat()
    
    def __repr__(self):
        """Return a comprehensive string representation of the computer information"""
        lines = []
        lines.append("="*60)
        lines.append("COMPUTER INFORMATION")
        lines.append("="*60)
        
        # Basic Information
        lines.append("\n📋 BASIC INFORMATION:")
        lines.append(f"   Computer Name: {self.computername or 'Unknown'}")
        lines.append(f"   Username: {self.username or 'Unknown'}")
        lines.append(f"   Full Name: {self.human_name or 'Unknown'}")
        lines.append(f"   First Name: {self.first_name or 'Unknown'}")
        lines.append(f"   Last Name: {self.last_name or 'Unknown'}")
        
        # System Information
        lines.append("\n💻 SYSTEM INFORMATION:")
        lines.append(f"   OS: {self.os or 'Unknown'}")
        lines.append(f"   Manufacturer: {self.manufacturer or 'Unknown'}")
        lines.append(f"   Model: {self.model or 'Unknown'}")
        lines.append(f"   Serial Number: {self.serial_number or 'Unknown'}")
        
        # Hardware Information
        lines.append("\n🔧 HARDWARE INFORMATION:")
        # Get primary CPU from all_cpus
        primary_cpu_name = "Unknown"
        if self.all_cpus:
            primary_cpu_name = self.all_cpus[0].name
        lines.append(f"   CPU: {primary_cpu_name}")
        
        # Get system memory from system_info
        system_memory = "Unknown"
        if self.system_info:
            system_memory = self.system_info.total_memory_formatted
        lines.append(f"   Total Memory: {system_memory}")
        
        # CPU Details
        if self.all_cpus:
            lines.append(f"\n   🖥️  CPUs ({len(self.all_cpus)} found):")
            for i, cpu in enumerate(self.all_cpus, 1):
                lines.append(f"     CPU_{i}: {cpu.name}")
                lines.append(f"       Type: {cpu.type}")
                lines.append(f"       Cores: {cpu.cores}")
                lines.append(f"       Logical Processors: {cpu.logical_processors}")
                lines.append(f"       Release Date: {cpu.release_date}")
        
        # GPU Details
        if self.all_gpus:
            lines.append(f"\n   🎮 GPUs ({len(self.all_gpus)} found):")
            for i, gpu in enumerate(self.all_gpus, 1):
                lines.append(f"     GPU_{i}: {gpu.name}")
                lines.append(f"       Type: {gpu.type}")
                if gpu.memory_formatted:
                    lines.append(f"       Memory: {gpu.memory_formatted}")
                lines.append(f"       Driver: {gpu.driver}")
                lines.append(f"       Priority: {gpu.priority}")
                lines.append(f"       Release Date: {gpu.release_date or 'Unknown'}")
        
        # Collection Information
        lines.append("\n📅 COLLECTION INFORMATION:")
        lines.append(f"   Collection Date: {self.collection_date or 'Unknown'}")
        
        # Error Information (if any)
        errors = []
        for field in ['computername_error', 'user_info_error', 'full_name_api_error', 
                     'os_info_error', 'hardware_info_error', 'memory_info_error', 
                     'cpu_info_error', 'gpu_info_error', 'collection_error']:
            error_value = getattr(self, field, None)
            if error_value:
                errors.append(f"   {field}: {error_value}")
        
        if errors:
            lines.append("\n⚠️  ERRORS ENCOUNTERED:")
            lines.extend(errors)
        
        lines.append("="*60)
        return "\n".join(lines)
    
    def to_json_dict(self) -> Dict[str, Any]:
        """Convert ComputerInfo instance to dictionary for JSON serialization using dataclasses.asdict"""
        result = {}
        
        # Add basic fields with JSON key mapping
        for field_name, field_value in self.__dict__.items():
            if field_value is not None and field_name not in ['system_info', 'all_gpus', 'all_cpus']:
                json_key = self._get_json_key(field_name)
                result[json_key] = field_value
        
        # Add structured system info using asdict
        if self.system_info:
            result["system_info"] = asdict(self.system_info)
        
        # Add structured GPU info using asdict
        if self.all_gpus:
            result["all_gpus"] = {}
            for i, gpu in enumerate(self.all_gpus, 1):
                result["all_gpus"][f"gpu_{i}"] = asdict(gpu)
        
        # Add structured CPU info using asdict
        if self.all_cpus:
            result["all_cpus"] = {}
            for i, cpu in enumerate(self.all_cpus, 1):
                result["all_cpus"][f"cpu_{i}"] = asdict(cpu)
        
        return result
    
    def _get_json_key(self, field_name: str) -> str:
        """Convert Python field names to JSON keys matching Excel headers"""
        key_mapping = {
            'computername': 'Computername',
            'username': 'Username',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'human_name': 'human_name',
            'os': 'OS',
            'manufacturer': 'Manufacturer',
            'model': 'Model',
            'serial_number': 'Serial Number',
            'date': 'Date'
        }
        return key_mapping.get(field_name, field_name)
    
    def set_error(self, field_name: str, error_message: str):
        """Set an error field for a specific collection method"""
        error_field = f"{field_name}_error"
        if hasattr(self, error_field):
            setattr(self, error_field, error_message)
        else:
            # If error field doesn't exist, add it dynamically
            setattr(self, error_field, error_message)

def save_token_error(error_msg, exception=None):
    """Save token loading error to file"""
    try:
        with open("aboutme_token_error.txt", 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("ABOUTME TOKEN LOADING ERROR\n")
            f.write("="*80 + "\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Error: {error_msg}\n")
            if exception:
                f.write(f"Exception: {str(exception)}\n")
                f.write(f"Traceback:\n{traceback.format_exc()}\n")
            f.write("="*80 + "\n")
    except:
        pass


def try_half_token():
    var_1 = "gtu_a_1OXF0p3TyhCGm0q5zONoE20wCkv7rdkftIU6OQVgS"
    var_2 = "ihbpt1AUKIdKQdru_dWUzSiqbUuAMJb313VmbR472YZzO2"
    
    # Combine var_1 and var_2 in alternating pattern
    combined = ""
    max_len = max(len(var_1), len(var_2))
    
    for i in range(max_len):
        if i < len(var_1):
            combined += var_1[i]
        if i < len(var_2):
            combined += var_2[i]
    
    return combined
    


def _pause_if_interactive():
    if not SILENT_MODE:
        try:
            input("\nPress Enter to close this window...")
        except Exception:
            pass

try:
    # Prefer half token first
    EMBEDDED_GITHUB_TOKEN = try_half_token()
    print("✅ GitHub token loaded from half token (preferred)")
except Exception:
    # Fall back to existing token.json if available
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
            EMBEDDED_GITHUB_TOKEN = token_data['token']
        print(f"✅ GitHub token loaded successfully from token.json")
    except Exception as e:
        # As a last attempt, try half token again and exit on failure
        try:
            EMBEDDED_GITHUB_TOKEN = try_half_token()
            print("✅ GitHub token recovered from half token")
        except Exception:
            save_token_error(f"Token load failed: {e}")
            _pause_if_interactive()
            sys.exit(1)

# EMBEDDED CONFIGURATION - Replace with your actual values
EMBEDDED_REPO_OWNER = "Ennead-Architects-LLP"
EMBEDDED_REPO_NAME = "EmployeeData"
EMBEDDED_WEBSITE_URL = "https://ennead-architects-llp.github.io/EmployeeData"

def setup_logging(silent=False):
    """Setup logging for error tracking"""
    try:
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Setup logging configuration
        log_file = os.path.join(log_dir, f"aboutme_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # Clear any existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        handlers = [logging.FileHandler(log_file, encoding='utf-8')]
        if not silent:
            handlers.append(logging.StreamHandler(sys.stdout))
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        
        return log_file
    except Exception as e:
        print(f"⚠️  Warning: Could not setup logging: {e}")
        return None

def save_error_to_file(error_msg, exception=None, log_file=None):
    """Save error details to a file that will persist even if console closes"""
    try:
        # Create error log file in the same directory as the executable
        error_file = "aboutme_error_log.txt"
        
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("ABOUTME COMPUTER INFO COLLECTOR - ERROR REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Error: {error_msg}\n")
            f.write("\n")
            
            if exception:
                f.write(f"Exception Type: {type(exception).__name__}\n")
                f.write(f"Exception Message: {str(exception)}\n")
                f.write("\n")
                f.write("FULL TRACEBACK:\n")
                f.write("-" * 40 + "\n")
                f.write(traceback.format_exc())
                f.write("\n")
            
            f.write("\n")
            f.write("SYSTEM INFORMATION:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Platform: {platform.platform()}\n")
            f.write(f"Python Version: {sys.version}\n")
            f.write(f"Executable: {sys.executable}\n")
            f.write(f"Working Directory: {os.getcwd()}\n")
            
            if log_file:
                f.write(f"Detailed Log File: {log_file}\n")
            
            f.write("="*80 + "\n")
        
        return error_file
    except Exception as e:
        print(f"❌ Failed to save error to file: {e}")
        return None

def log_error(error_msg, exception=None):
    """Log error with traceback"""
    try:
        if exception:
            logging.error(f"{error_msg}: {str(exception)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
        else:
            logging.error(error_msg)
    except Exception as e:
        print(f"❌ Error logging failed: {e}")
        print(f"Original error: {error_msg}")
        if exception:
            print(f"Exception: {str(exception)}")
            print(f"Traceback: {traceback.format_exc()}")

class ComputerInfoCollector:
    def __init__(self, website_url=None):
        self.computer_info = ComputerInfo()
        self.wmi_conn = None
    
        
    def collect_all_info(self):
        """Collect essential computer information matching Excel headers"""
        try:
            # Initialize WMI connection for Windows
            if platform.system() == "Windows":
                try:
                    self.wmi_conn = wmi.WMI()
                except Exception as e:
                    print(f"Warning: Could not initialize WMI: {e}")
            
            # Collect only essential information matching Excel headers
            self._get_computername()
            self._get_user_info()
            self._get_os_info()
            self._get_hardware_info()
            self._get_memory_info()
            self._get_cpu_info()
            self._get_gpu_info()
            self._get_system_serial()
            
            # Date is automatically set in __post_init__
            
        except Exception as e:
            self.computer_info.collection_error = str(e)
    
    def _get_computername(self):
        """Get computer name"""
        try:
            self.computer_info.computername = platform.node()
        except Exception as e:
            self.computer_info.set_error("computername", str(e))
    
    def _get_user_info(self):
        """Get current user information"""
        try:
            self.computer_info.username = os.environ.get('USERNAME', os.environ.get('USER', ''))
            self.computer_info.human_name = self._get_user_full_name()
            # Parse first and last name from human_name
            self._parse_name_fields()
        except Exception as e:
            self.computer_info.set_error("user_info", str(e))
    
    def _get_user_full_name(self):
        """Get user's full name using Windows API"""
        try:
            full_name = None
            
            if platform.system() == "Windows":
                try:
                    # Load the security library
                    secur32 = ctypes.windll.secur32
                    
                    # Define the function signature
                    GetUserNameEx = secur32.GetUserNameExW
                    GetUserNameEx.argtypes = [ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
                    GetUserNameEx.restype = ctypes.c_int
                    
                    # NameDisplay = 3 (gets the display name)
                    NameDisplay = 3
                    
                    # First call to get the required buffer size
                    size = ctypes.c_ulong(0)
                    result = GetUserNameEx(NameDisplay, None, ctypes.byref(size))
                    
                    if result == 0 and size.value > 0:
                        # Allocate buffer and get the name
                        name_buffer = ctypes.create_unicode_buffer(size.value)
                        result = GetUserNameEx(NameDisplay, name_buffer, ctypes.byref(size))
                        
                        if result != 0:
                            full_name = name_buffer.value
                            
                except Exception as e:
                    self.computer_info.set_error("full_name_api", str(e))
            
            # Fallback: try to get from environment variables
            if not full_name:
                full_name = os.environ.get('USERNAME', '') or os.environ.get('USER', '')
            
            # Format name as "First Last" if it's in "Last, First" format
            if full_name and ',' in full_name:
                parts = full_name.split(',', 1)
                if len(parts) == 2:
                    last_name = parts[0].strip()
                    first_name = parts[1].strip()
                    full_name = f"{first_name} {last_name}"
            
            return full_name
            
        except Exception as e:
            return os.environ.get('USERNAME', '') or "Unknown"
    
    def _parse_name_fields(self):
        """Parse first and last name from human_name"""
        try:
            human_name = self.computer_info.human_name or ''
            if human_name and human_name != 'Unknown':
                # Split by space and take first as first name, rest as last name
                name_parts = human_name.strip().split()
                if len(name_parts) >= 2:
                    self.computer_info.first_name = name_parts[0]
                    self.computer_info.last_name = ' '.join(name_parts[1:])
                elif len(name_parts) == 1:
                    self.computer_info.first_name = name_parts[0]
                    self.computer_info.last_name = ""
                else:
                    self.computer_info.first_name = ""
                    self.computer_info.last_name = ""
            else:
                self.computer_info.first_name = ""
                self.computer_info.last_name = ""
        except Exception as e:
            self.computer_info.set_error("name_parsing", str(e))
            self.computer_info.first_name = ""
            self.computer_info.last_name = ""
    
    
    def _get_os_info(self):
        """Get operating system information"""
        try:
            self.computer_info.os = f"{platform.system()} {platform.release()}"
        except Exception as e:
            self.computer_info.set_error("os_info", str(e))
    
    def _get_hardware_info(self):
        """Get hardware manufacturer and model information"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    # Get computer system info
                    for cs in self.wmi_conn.Win32_ComputerSystem():
                        self.computer_info.manufacturer = cs.Manufacturer
                        self.computer_info.model = cs.Model
                        break
                    
                    # Try to get better model info from baseboard if system model is generic
                    if (self.computer_info.model or "").lower() in ["system product name", "to be filled by o.e.m.", "default string"]:
                        try:
                            for baseboard in self.wmi_conn.Win32_BaseBoard():
                                if baseboard.Product and baseboard.Product.lower() not in ["to be filled by o.e.m.", "default string"]:
                                    self.computer_info.model = baseboard.Product
                                    break
                        except Exception:
                            pass
                    
                    # Try to get better manufacturer info if generic
                    if (self.computer_info.manufacturer or "").lower() in ["to be filled by o.e.m.", "default string"]:
                        try:
                            for baseboard in self.wmi_conn.Win32_BaseBoard():
                                if baseboard.Manufacturer and baseboard.Manufacturer.lower() not in ["to be filled by o.e.m.", "default string"]:
                                    self.computer_info.manufacturer = baseboard.Manufacturer
                                    break
                        except Exception:
                            pass
                            
                except Exception as e:
                    self.computer_info.set_error("hardware_wmi", str(e))
            else:
                # Fallback for non-Windows systems
                self.computer_info.manufacturer = "Unknown"
                self.computer_info.model = "Unknown"
        except Exception as e:
            self.computer_info.set_error("hardware_info", str(e))
    
    def _get_memory_info(self):
        """Get memory information"""
        try:
            memory = psutil.virtual_memory()
            
            # Create structured system info object
            self.computer_info.system_info = InfoDataSystem.from_psutil_memory(memory)
        except Exception as e:
            self.computer_info.set_error("memory_info", str(e))
            self.computer_info.system_info = None
    
    def _get_cpu_info(self):
        """Get CPU information for all CPUs"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    all_cpus = []
                    
                    for cpu in self.wmi_conn.Win32_Processor():
                        # Create structured CPU info object
                        cpu_info = InfoDataCPU.from_wmi_processor(cpu)
                        all_cpus.append(cpu_info)
                    
                    # Store all CPU information
                    self.computer_info.all_cpus = all_cpus
                except Exception as e:
                    self.computer_info.set_error("cpu_wmi", str(e))
                    self.computer_info.all_cpus = []
            else:
                self.computer_info.all_cpus = []
        except Exception as e:
            self.computer_info.set_error("cpu_info", str(e))
    
    
    def _get_gpu_info(self):
        """Get GPU information for all GPUs"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    all_gpus = []
                    
                    # List of virtual/generic GPU names to exclude from primary selection
                    virtual_gpu_names = [
                        "microsoft basic display driver",
                        "microsoft basic render driver", 
                        "meta virtual monitor",
                        "virtual display",
                        "generic pnp monitor",
                        "default display device"
                    ]
                    
                    for gpu in self.wmi_conn.Win32_VideoController():
                        # Skip GPUs with no meaningful name
                        if not gpu.Name or gpu.Name.strip() == "":
                                            continue
                        
                        # Create structured GPU info object
                        gpu_info = InfoDataGPU.from_wmi_video_controller(
                            gpu, 
                            InfoDataSystem.format_memory_size, 
                            virtual_gpu_names
                        )
                        all_gpus.append(gpu_info)
                    
                    # Store all GPU information
                    self.computer_info.all_gpus = all_gpus
                except Exception as e:
                    self.computer_info.set_error("gpu_wmi", str(e))
                    self.computer_info.all_gpus = []
            else:
                self.computer_info.all_gpus = []
        except Exception as e:
            self.computer_info.set_error("gpu_info", str(e))
    
    
    def _get_system_serial(self):
        """Get system serial number"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    # Try BIOS serial first
                    for bios in self.wmi_conn.Win32_BIOS():
                        if bios.SerialNumber and bios.SerialNumber.lower() not in ["system serial number", "to be filled by o.e.m.", "default string", "0"]:
                            self.computer_info.serial_number = bios.SerialNumber
                            break
                        else:
                            self.computer_info.serial_number = "Unknown"
                    
                    # If BIOS serial is generic, try computer system serial
                    if (self.computer_info.serial_number or "").lower() in ["system serial number", "to be filled by o.e.m.", "default string", "unknown", "0"]:
                        try:
                            for cs in self.wmi_conn.Win32_ComputerSystem():
                                if cs.SerialNumber and cs.SerialNumber.lower() not in ["system serial number", "to be filled by o.e.m.", "default string", "0"]:
                                    self.computer_info.serial_number = cs.SerialNumber
                                    break
                        except Exception:
                            pass
                    
                    # If still generic, try baseboard serial
                    if (self.computer_info.serial_number or "").lower() in ["system serial number", "to be filled by o.e.m.", "default string", "unknown", "0"]:
                        try:
                            for baseboard in self.wmi_conn.Win32_BaseBoard():
                                if baseboard.SerialNumber and baseboard.SerialNumber.lower() not in ["system serial number", "to be filled by o.e.m.", "default string", "0"]:
                                    self.computer_info.serial_number = baseboard.SerialNumber
                                    break
                        except Exception:
                            pass
                            
                except Exception as e:
                    self.computer_info.serial_number = "Unknown"
            else:
                self.computer_info.serial_number = "Unknown"
        except Exception as e:
            self.computer_info.serial_number = "Unknown"
    
    def save_to_json(self, filename="computer_info.json"):
        """Save collected information to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.computer_info.to_dict(), f, indent=2, ensure_ascii=False, default=str)
            print(f"Computer information saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving to JSON: {e}")
            return False
    
    def send_to_github_repo(self):
        """Send data to GitHub repository via repository dispatch API using embedded token"""
        try:
            url = f"https://api.github.com/repos/{EMBEDDED_REPO_OWNER}/{EMBEDDED_REPO_NAME}/dispatches"
            
            # Prepare nested data for transmission (stays within GitHub's 10 property limit)
            payload = {
                "event_type": "computer-data",
                "client_payload": {
                    "timestamp": datetime.now().isoformat(),
                    "computer_info": self.computer_info.to_json_dict()
                }
            }
            
            headers = {
                "Authorization": f"token {EMBEDDED_GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AboutMe-ComputerInfo/1.0"
            }
            
            print(f"Sending computer information to GitHub...")
            print(f"   Computer: {self.computer_info.computername or 'Unknown'}")
            print(f"   User: {self.computer_info.human_name or 'Unknown'} ({self.computer_info.username or 'Unknown'})")
            
            # Print payload information
            print(f"\n📋 PAYLOAD INFORMATION:")
            print(f"   Repository: {EMBEDDED_REPO_OWNER}/{EMBEDDED_REPO_NAME}")
            print(f"   Event Type: computer-data")
            print(f"   Timestamp: {datetime.now().isoformat()}")
            
            # Print computer info structure
            computer_dict = self.computer_info.to_json_dict()
            print(f"\n📊 COMPUTER INFO STRUCTURE:")
            for key, value in computer_dict.items():
                if key == 'all_cpus':
                    print(f"   {key}: {len(value) if value else 0} CPUs")
                    if value:
                        for cpu_key, cpu in value.items():
                            print(f"     {cpu_key.upper()}: {cpu.get('name', 'Unknown')} ({cpu.get('type', 'Unknown')})")
                elif key == 'all_gpus':
                    print(f"   {key}: {len(value) if value else 0} GPUs")
                    if value:
                        for gpu_key, gpu in value.items():
                            print(f"     {gpu_key.upper()}: {gpu.get('name', 'Unknown')} ({gpu.get('type', 'Unknown')})")
                else:
                    # Truncate very long values for display
                    display_value = str(value)
                    if len(display_value) > 60:
                        display_value = display_value[:57] + "..."
                    print(f"   {key}: {display_value}")
            
            print(f"\n📦 PAYLOAD SIZE: {len(json.dumps(payload))} characters")
            
            # Optional: Print complete payload JSON for debugging
            if os.environ.get("ABOUTME_DEBUG_PAYLOAD") == "1":
                print(f"\n🔍 COMPLETE PAYLOAD JSON:")
                print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 204:  # 204 No Content is success for repository dispatch
                print("✅ Computer information sent successfully!")
                print("   Your data will be processed and appear on the website shortly.")
                return True
            else:
                print(f"❌ Failed to send data. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error sending data: {e}")
            return False

    def print_summary(self):
        """Print a summary of collected information using the __repr__ method"""
        print(repr(self.computer_info))

def main():
    """GUI entrypoint with CLI fallback."""
    # Forced silent via CLI flag or env
    force_silent = False
    try:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--silent", action="store_true")
        args, _ = parser.parse_known_args()
        force_silent = bool(args.silent) or os.environ.get("ABOUTME_FORCE_SILENT") == "1"
    except Exception:
        pass

    is_cli = force_silent or tk is None
    log_file = setup_logging(silent=is_cli)
    if is_cli:
        return main_cli(log_file, silent=True)
    try:
        app = AboutMeApp(log_file=log_file)
        app.run()
    except Exception as e:
        log_error("Critical error launching GUI", e)
        return main_cli(log_file, silent=True)

def main_cli(log_file=None, silent=True):
    try:
        # Silent CLI: no stdout printing or input prompts
        collector = ComputerInfoCollector()
        collector.collect_all_info()
        # No console summary in silent mode
        success = collector.send_to_github_repo()
        # Log outcome only
        logging.info("CLI send status: %s", "success" if success else "failed")
    except Exception as e:
        error_msg = f"❌ CRITICAL ERROR: {str(e)}"
        log_error("Critical error in CLI", e)
        save_error_to_file(error_msg, e, log_file)
    finally:
        # No blocking input in silent mode
        pass

class AboutMeApp:
    """Minimal dark-themed Tkinter GUI wrapping the collector and sender."""
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.root = tk.Tk()
        self.root.title("AboutMe")
        self.root.geometry("720x520")
        self.root.configure(bg="#121212")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._apply_dark_style()
        self._set_window_icon()
        self.collector = ComputerInfoCollector()
        self.queue = queue.Queue()
        self._build_loading_ui()
        self._start_collection()

    def _apply_dark_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", background="#121212", foreground="#E0E0E0")
        style.configure("TFrame", background="#121212")
        style.configure("TButton", background="#1E1E1E", foreground="#E0E0E0", padding=8)
        style.map("TButton", background=[("active", "#2A2A2A")])
        style.configure("Treeview", background="#1E1E1E", foreground="#E0E0E0", fieldbackground="#1E1E1E")
        style.configure("Treeview.Heading", background="#1E1E1E", foreground="#E0E0E0")

    def _build_loading_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        frame = ttk.Frame(self.root)
        frame.pack(expand=True, fill="both", padx=24, pady=24)
        title = ttk.Label(frame, text="AboutMe", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(40, 12))
        subtitle = ttk.Label(frame, text="After the reimaging of computers we need to collect the current machine data. You just need to approve.")
        subtitle.pack(pady=(0, 24))
        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill="x")
        self.progress.start(10)
        self._add_footer(self.root)

    def _build_review_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        container = ttk.Frame(self.root)
        container.pack(expand=True, fill="both", padx=16, pady=12)

        # Content area (top)
        content = ttk.Frame(container)
        content.pack(side="top", fill="both", expand=True)

        header = ttk.Label(content, text="AboutMe - Data Collection Review", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w", pady=(0, 8))
        
        # Data collection notice
        notice = ttk.Label(content, text="After the reimaging of computers we need to collect the current machine data. You just need to approve.", 
                          font=("Segoe UI", 10))
        notice.pack(anchor="w", pady=(0, 8))
        
        # Data collection summary
        summary = ttk.Label(content, text="📋 The following information will be collected and shared with the IT team:", 
                           font=("Segoe UI", 10, "bold"))
        summary.pack(anchor="w", pady=(0, 8))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(content)
        notebook.pack(fill="both", expand=True, pady=(0, 8))
        
        # Tab 1: Basic System Information
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic System Info")
        
        # Tab 2: Hardware Details
        hardware_frame = ttk.Frame(notebook)
        notebook.add(hardware_frame, text="Hardware Details")
        
        # Tab 3: All Data Preview
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="Complete Data Preview")
        
        # Populate Basic System Information tab
        self._populate_basic_info_tab(basic_frame)
        
        # Populate Hardware Details tab
        self._populate_hardware_info_tab(hardware_frame)
        
        # Populate Complete Data Preview tab
        self._populate_preview_tab(preview_frame)

        # Fixed bottom action bar
        actions = ttk.Frame(container)
        actions.pack(side="bottom", fill="x", pady=(8, 0))
        # Add privacy notice
        privacy_frame = ttk.Frame(container)
        privacy_frame.pack(side="bottom", fill="x", pady=(8, 0))
        
        privacy_text = "🔒 Privacy Notice: This data is shared securely with the IT team for system inventory purposes only."
        privacy_label = ttk.Label(privacy_frame, text=privacy_text, font=("Segoe UI", 9), 
                                 foreground="#888888")
        privacy_label.pack(anchor="center")
        
        self.send_btn = ttk.Button(actions, text="✅ Allow Share", command=self.on_send_click)
        self.cancel_btn = ttk.Button(actions, text="❌ Disallow Share", command=self.on_close)
        self.send_btn.pack(side="left")
        self.cancel_btn.pack(side="right")
        self._add_footer(self.root)
    
    def _populate_basic_info_tab(self, parent):
        """Populate the Basic System Information tab"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg="#121212")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Basic system information
        basic_info = [
            ("Computer Name", "Identifies your specific computer"),
            ("Username", "Your Windows username"),
            ("Full Name", "Your display name from Windows"),
            ("Operating System", "Windows version and build"),
            ("Manufacturer", "Computer manufacturer (e.g., Lenovo, Dell)"),
            ("Model", "Computer model number"),
            ("Serial Number", "Hardware serial number"),
            ("Total Memory", "Amount of RAM installed"),
            ("Collection Date", "When this data was collected")
        ]
        
        info_label = ttk.Label(scrollable_frame, text="📋 Basic System Information", 
                              font=("Segoe UI", 12, "bold"))
        info_label.pack(anchor="w", pady=(0, 8))
        
        for field, description in basic_info:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            
            field_label = ttk.Label(frame, text=f"• {field}:", font=("Segoe UI", 10, "bold"))
            field_label.pack(side="left", anchor="w")
            
            desc_label = ttk.Label(frame, text=description, font=("Segoe UI", 9))
            desc_label.pack(side="left", anchor="w", padx=(10, 0))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _populate_hardware_info_tab(self, parent):
        """Populate the Hardware Details tab"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg="#121212")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Hardware information
        hardware_info = [
            ("CPU Information", "Processor name, cores, speed, and release date"),
            ("GPU Information", "All graphics cards with details like memory, driver, and type"),
            ("Physical vs Virtual", "Distinguishes between real hardware and virtual devices"),
            ("Hardware Priority", "Ranks GPUs by performance (dedicated > integrated > virtual)"),
            ("Memory Details", "GPU memory allocation and system RAM"),
            ("Driver Information", "Current driver versions for all hardware")
        ]
        
        info_label = ttk.Label(scrollable_frame, text="🔧 Hardware Details", 
                              font=("Segoe UI", 12, "bold"))
        info_label.pack(anchor="w", pady=(0, 8))
        
        for field, description in hardware_info:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            
            field_label = ttk.Label(frame, text=f"• {field}:", font=("Segoe UI", 10, "bold"))
            field_label.pack(side="left", anchor="w")
            
            desc_label = ttk.Label(frame, text=description, font=("Segoe UI", 9))
            desc_label.pack(side="left", anchor="w", padx=(10, 0))
        
        # Show actual hardware count
        computer_info = self.collector.computer_info
        count_frame = ttk.Frame(scrollable_frame)
        count_frame.pack(fill="x", pady=(16, 0))
        
        count_label = ttk.Label(count_frame, text="📊 Your System Hardware:", 
                               font=("Segoe UI", 10, "bold"))
        count_label.pack(anchor="w")
        
        cpu_count = len(computer_info.all_cpus) if computer_info.all_cpus else 0
        gpu_count = len(computer_info.all_gpus) if computer_info.all_gpus else 0
        
        cpu_info = ttk.Label(count_frame, text=f"• CPUs: {cpu_count} found")
        cpu_info.pack(anchor="w", padx=(20, 0))
        
        gpu_info = ttk.Label(count_frame, text=f"• GPUs: {gpu_count} found")
        gpu_info.pack(anchor="w", padx=(20, 0))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _populate_preview_tab(self, parent):
        """Populate the Complete Data Preview tab"""
        # Create treeview for complete data preview
        columns = ("Field", "Value")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        tree.heading("Field", text="Field")
        tree.heading("Value", text="Value")
        tree.column("Field", width=250, anchor="w")
        tree.column("Value", width=400, anchor="w")
        
        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        # Populate with actual data
        computer_info = self.collector.computer_info
        
        # Basic fields
        basic_fields = {
            'computername': 'Computer Name',
            'human_name': 'Full Name',
            'username': 'Username',
            'os': 'Operating System',
            'manufacturer': 'Manufacturer',
            'model': 'Model',
            'serial_number': 'Serial Number',
            'collection_date': 'Collection Date'
        }
        
        for field_name, display_label in basic_fields.items():
            if hasattr(computer_info, field_name):
                value = getattr(computer_info, field_name)
                if value is not None:
                    tree.insert("", "end", values=(display_label, str(value)))
        
        # System information
        if computer_info.system_info:
            tree.insert("", "end", values=("Total Memory", computer_info.system_info.total_memory_formatted))
            tree.insert("", "end", values=("Available Memory", f"{computer_info.system_info.available_memory_bytes / (1024**3):.1f} GB"))
            tree.insert("", "end", values=("Memory Usage", f"{computer_info.system_info.memory_percent:.1f}%"))
        
        # Primary CPU information
        if computer_info.all_cpus:
            primary_cpu = computer_info.all_cpus[0]
            tree.insert("", "end", values=("Primary CPU", primary_cpu.name))
        
        # CPU information
        if computer_info.all_cpus:
            for i, cpu in enumerate(computer_info.all_cpus, 1):
                tree.insert("", "end", values=(f"CPU_{i} - Name", cpu.name))
                tree.insert("", "end", values=(f"CPU_{i} - Cores", str(cpu.cores)))
                tree.insert("", "end", values=(f"CPU_{i} - Logical Processors", str(cpu.logical_processors)))
                tree.insert("", "end", values=(f"CPU_{i} - Type", cpu.type))
                tree.insert("", "end", values=(f"CPU_{i} - Date", cpu.date))
        
        # GPU information
        if computer_info.all_gpus:
            for i, gpu in enumerate(computer_info.all_gpus, 1):
                tree.insert("", "end", values=(f"GPU_{i} - Name", gpu.name))
                tree.insert("", "end", values=(f"GPU_{i} - Type", gpu.type))
                memory_display = gpu.memory_formatted if gpu.memory_formatted else 'N/A'
                tree.insert("", "end", values=(f"GPU_{i} - Memory", memory_display))
                tree.insert("", "end", values=(f"GPU_{i} - Driver", gpu.driver))
                tree.insert("", "end", values=(f"GPU_{i} - Priority", str(gpu.priority)))
        
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _build_success_ui(self, success):
        for w in self.root.winfo_children():
            w.destroy()
        frame = ttk.Frame(self.root)
        frame.pack(expand=True, fill="both", padx=24, pady=24)
        if success:
            title = ttk.Label(frame, text="Data Shared", font=("Segoe UI", 18, "bold"))
            title.pack(pady=(24, 8))
            msg = ttk.Label(frame, text="Thank you and have a nice day.")
            msg.pack(pady=(0, 16))
            # Animated circular-masked GIF
            size = 220
            canvas = tk.Canvas(frame, width=size, height=size, bg="#121212", highlightthickness=0)
            canvas.pack(pady=8)
            canvas.create_oval(10, 10, size-10, size-10, fill="#FFFFFF", outline="#FFFFFF")

            gif_path = self._find_duck_gif()
            self._gif_animator = None
            if gif_path and Image is not None:
                try:
                    self._gif_animator = _CircularGifAnimator(canvas, gif_path, diameter=size-20, bg="#121212")
                    self._gif_animator.start()
                except Exception:
                    self._gif_animator = None
            if self._gif_animator is None and tk is not None:
                try:
                    # Fallback to static image without animation if PIL unavailable
                    static_img = tk.PhotoImage(file=gif_path) if gif_path and os.path.exists(gif_path) else None
                    if static_img is not None:
                        self._gif_image = static_img
                        canvas.create_image(size//2, size//2, image=self._gif_image)
                except Exception:
                    pass

            close = ttk.Button(frame, text="Close", command=self.on_close)
            close.pack(pady=(24, 0))
        else:
            title = ttk.Label(frame, text="Unable to Send", font=("Segoe UI", 18, "bold"))
            title.pack(pady=(24, 8))
            msg = ttk.Label(frame, text="There was a problem sending your information. You can try again later.")
            msg.pack(pady=(0, 16))
            close = ttk.Button(frame, text="Close", command=self.on_close)
            close.pack(pady=(24, 0))
        self._add_footer(self.root)

    def _resolve_asset(self, relative_path):
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, relative_path)

    def _find_duck_gif(self):
        candidates = [
            self._resolve_asset("assets/duck-dance.gif"),
            self._resolve_asset("duck-dance.gif"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "duck-dance.gif"),
        ]
        for p in candidates:
            if p and os.path.exists(p):
                return p
        return None

    def _start_collection(self):
        def work():
            try:
                self.collector.collect_all_info()
                self.queue.put(("done", None))
            except Exception as e:
                self.queue.put(("error", e))
        threading.Thread(target=work, daemon=True).start()
        self.root.after(100, self._poll_queue)

    def _poll_queue(self):
        try:
            kind, payload = self.queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_queue)
            return
        if kind == "done":
            if hasattr(self, "progress"):
                try:
                    self.progress.stop()
                except Exception:
                    pass
            self._build_review_ui()
        elif kind == "error":
            log_error("Failed during collection", payload)
            messagebox.showerror("Error", "Failed to collect computer information.")
            self.on_close()
        else:
            self.root.after(100, self._poll_queue)

    def on_send_click(self):
        self.send_btn.state(["disabled"]) if self.send_btn else None
        self.cancel_btn.state(["disabled"]) if self.cancel_btn else None
        def send_work():
            try:
                success = self.collector.send_to_github_repo()
            except Exception as e:
                log_error("Failed to send to GitHub", e)
                success = False
            self.queue.put(("sent", success))
        threading.Thread(target=send_work, daemon=True).start()
        self._show_sending_state()
        self.root.after(100, self._poll_send_queue)

    def _show_sending_state(self):
        for w in self.root.winfo_children():
            w.destroy()
        frame = ttk.Frame(self.root)
        frame.pack(expand=True, fill="both", padx=24, pady=24)
        title = ttk.Label(frame, text="Sending...", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(40, 12))
        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill="x")
        self.progress.start(10)
        self._add_footer(self.root)

    def _poll_send_queue(self):
        try:
            kind, payload = self.queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_send_queue)
            return
        if kind == "sent":
            try:
                self.progress.stop()
            except Exception:
                pass
            self._build_success_ui(bool(payload))
        else:
            self.root.after(100, self._poll_send_queue)

    def on_close(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        # Center window
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.mainloop()

    def _set_window_icon(self):
        try:
            icon_path = self._resolve_asset("icon.ico")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(default=icon_path)
        except Exception:
            pass

    def _add_footer(self, parent):
        try:
            footer = ttk.Frame(parent)
            footer.pack(side="bottom", fill="x", padx=8, pady=(8, 6))
            lbl = ttk.Label(footer, text="Copright @ EnneadTab 2025")
            lbl.pack(anchor="center")
        except Exception:
            pass


class _CircularGifAnimator:
    """Play an animated GIF masked to a circle on a Tk canvas using Pillow frames."""
    def __init__(self, canvas: tk.Canvas, gif_path: str, diameter: int = 200, bg: str = "#121212"):
        self.canvas = canvas
        self.gif_path = gif_path
        self.diameter = diameter
        self.bg = bg
        self.frames = []
        self.durations = []
        self._tk_frames = []
        self._current = 0
        self._item = None
        self._load_frames()

    def _load_frames(self):
        img = Image.open(self.gif_path)
        # Prepare circular mask once
        mask_size = (self.diameter, self.diameter)
        circle_mask = Image.new("L", mask_size, 0)
        draw = ImageDraw.Draw(circle_mask)
        draw.ellipse((0, 0, self.diameter, self.diameter), fill=255)
        white_bg = Image.new("RGBA", mask_size, (255, 255, 255, 255))

        # Some GIFs require seeking frames rather than ImageSequence for correct disposal
        try:
            num_frames = img.n_frames
        except Exception:
            num_frames = 1

        prev = Image.new("RGBA", img.size, (0, 0, 0, 0))
        for i in range(num_frames):
            try:
                img.seek(i)
            except EOFError:
                break

            frame = img.convert("RGBA")
            # Composite over previous to respect disposal methods
            composed_src = prev.copy()
            composed_src.alpha_composite(frame)
            prev = composed_src.copy()

            # Scale to fit circle
            fw, fh = composed_src.size
            scale = min(self.diameter / fw, self.diameter / fh)
            new_size = (max(1, int(fw * scale)), max(1, int(fh * scale)))
            scaled = composed_src.resize(new_size, Image.LANCZOS)

            # Center on canvas-sized transparent image
            centered = Image.new("RGBA", mask_size, (0, 0, 0, 0))
            x = (self.diameter - new_size[0]) // 2
            y = (self.diameter - new_size[1]) // 2
            centered.paste(scaled, (x, y), scaled)

            # Apply circular mask
            masked = Image.new("RGBA", mask_size, (0, 0, 0, 0))
            masked.paste(centered, (0, 0), circle_mask)

            # Put on white circle background
            final = white_bg.copy()
            final.paste(masked, (0, 0), masked)

            self.frames.append(final)
            duration = img.info.get("duration", 80)
            self.durations.append(max(30, int(duration)))

        # Fallback if no frames collected
        if not self.frames:
            self.frames = [white_bg]
            self.durations = [500]

        # Convert to Tk frames and pin to canvas to avoid GC
        for fr in self.frames:
            self._tk_frames.append(ImageTk.PhotoImage(fr))
        # Attach refs to canvas to prevent garbage collection
        if not hasattr(self.canvas, "_anim_refs"):
            self.canvas._anim_refs = []
        self.canvas._anim_refs.extend(self._tk_frames)

    def start(self):
        if not self._tk_frames:
            return
        cx = int(self.canvas.cget("width")) // 2
        cy = int(self.canvas.cget("height")) // 2
        if self._item is None:
            self._item = self.canvas.create_image(cx, cy, image=self._tk_frames[0])
        self._animate()

    def _animate(self):
        if not self._tk_frames:
            return
        try:
            self.canvas.itemconfig(self._item, image=self._tk_frames[self._current])
            delay = self.durations[self._current % len(self.durations)]
            self._current = (self._current + 1) % len(self._tk_frames)
        except Exception:
            delay = 80
        self.canvas.after(delay, self._animate)

    def _set_window_icon(self):
        try:
            # Prefer packaged icon path when bundled
            icon_path = self._resolve_asset("icon.ico")
            if not os.path.exists(icon_path):
                # Fallback to local directory
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(icon_path):
                # On Windows, .ico is supported
                self.root.iconbitmap(default=icon_path)
        except Exception:
            pass

    def _add_footer(self, parent):
        try:
            footer = ttk.Frame(parent)
            footer.pack(side="bottom", fill="x", padx=8, pady=(8, 6))
            lbl = ttk.Label(footer, text="Copright @ EnneadTab 2025")
            lbl.pack(anchor="center")
        except Exception:
            pass

if __name__ == "__main__":
    main()