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
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
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
    
    # Hardware specs
    cpu: Optional[str] = None
    total_physical_memory: Optional[int] = None
    gpu_name: Optional[str] = None
    gpu_processor: Optional[str] = None
    gpu_driver: Optional[str] = None
    gpu_memory: Optional[float] = None
    gpu_date: Optional[str] = None
    
    # Metadata
    date: Optional[str] = None
    
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
    gpu_date_error: Optional[str] = None
    
    def __post_init__(self):
        """Initialize date field after object creation"""
        if self.date is None:
            self.date = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ComputerInfo instance to dictionary for JSON serialization"""
        result = {}
        
        # Add all non-None fields to the result
        for field_name, field_value in self.__dict__.items():
            if field_value is not None:
                # Convert field names to match expected JSON keys
                json_key = self._get_json_key(field_name)
                result[json_key] = field_value
        
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
            'cpu': 'CPU',
            'total_physical_memory': 'Total Physical Memory',
            'gpu_name': 'GPU Name',
            'gpu_processor': 'GPU Processor',
            'gpu_driver': 'GPU Driver',
            'gpu_memory': 'GPU Memory',
            'gpu_date': 'GPU Date',
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
    


try:
    with open(token_file, 'r') as f:
        token_data = json.load(f)
        EMBEDDED_GITHUB_TOKEN = token_data['token']
    print(f"✅ GitHub token loaded successfully")
except FileNotFoundError:

    error_msg = f"❌ Error: {token_file} not found!"
    print(error_msg)
    print("   Please ensure the token.json file is in the same directory as the executable.")
    save_token_error(error_msg)
    try:
        EMBEDDED_GITHUB_TOKEN = try_half_token()
        print(f"✅ GitHub token loaded successfully from half token")
        with open(token_file, 'w') as f:
            json.dump({'token': EMBEDDED_GITHUB_TOKEN}, f)
    except Exception as e:
        error_msg = f"❌ Error: Failed to load GitHub token from half token: {e}"
        print(error_msg)
        save_token_error(error_msg, e)
        input("\nPress Enter to close this window...")
        sys.exit(1)
    
except json.JSONDecodeError as e:
    error_msg = f"❌ Error: Invalid JSON in {token_file}: {e}"
    print(error_msg)
    save_token_error(error_msg, e)
    input("\nPress Enter to close this window...")
    sys.exit(1)
except KeyError:
    error_msg = f"❌ Error: 'token' key not found in {token_file}"
    print(error_msg)
    save_token_error(error_msg)
    input("\nPress Enter to close this window...")
    sys.exit(1)
except Exception as e:
    error_msg = f"❌ Error loading token: {e}"
    print(error_msg)
    save_token_error(error_msg, e)
    input("\nPress Enter to close this window...")
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
        self.website_url = website_url or EMBEDDED_WEBSITE_URL
        
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
            self._get_gpu_date()
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
            self.computer_info.total_physical_memory = memory.total
        except Exception as e:
            self.computer_info.set_error("memory_info", str(e))
    
    def _get_cpu_info(self):
        """Get CPU information"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    for cpu in self.wmi_conn.Win32_Processor():
                        self.computer_info.cpu = cpu.Name
                        break
                except Exception as e:
                    self.computer_info.cpu = platform.processor()
            else:
                self.computer_info.cpu = platform.processor()
        except Exception as e:
            self.computer_info.set_error("cpu_info", str(e))
    
    def _get_gpu_info(self):
        """Get GPU information"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    max_memory_bytes = None
                    chosen_gpu = None

                    for gpu in self.wmi_conn.Win32_VideoController():
                        # Prefer the adapter with the largest memory size
                        raw = getattr(gpu, 'AdapterRAM', None)
                        mem_bytes = None
                        if raw is not None:
                            try:
                                # Some systems return strings; coerce to int safely
                                raw_int = int(raw)
                                if raw_int < 0:
                                    # Unsigned wrap (32-bit) → fix by adding 2^32
                                    raw_int = raw_int + (2 ** 32)
                                mem_bytes = int(raw_int)
                            except Exception:
                                mem_bytes = None

                        if mem_bytes is None:
                            # Try registry fallback for this adapter
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

                        if mem_bytes is not None:
                            if max_memory_bytes is None or mem_bytes > max_memory_bytes:
                                max_memory_bytes = mem_bytes
                                chosen_gpu = gpu

                    if chosen_gpu is not None:
                        self.computer_info.gpu_name = chosen_gpu.Name
                        self.computer_info.gpu_processor = chosen_gpu.VideoProcessor
                        self.computer_info.gpu_driver = chosen_gpu.DriverVersion
                    # Set memory in MB with clamping
                    if max_memory_bytes is not None:
                        mem_mb = max(0, int(round(max_memory_bytes / (1024 * 1024))))
                        self.computer_info.gpu_memory = mem_mb
                    else:
                        self.computer_info.gpu_memory = None
                except Exception as e:
                    self.computer_info.set_error("gpu_wmi", str(e))
            else:
                self.computer_info.gpu_name = "Unknown"
                self.computer_info.gpu_processor = "Unknown"
                self.computer_info.gpu_driver = "Unknown"
                self.computer_info.gpu_memory = None
        except Exception as e:
            self.computer_info.set_error("gpu_info", str(e))
    
    def _get_gpu_date(self):
        """Get GPU release date (age calculation done on website side)"""
        try:
            gpu_name = self.computer_info.gpu_name or ''
            if gpu_name and gpu_name != 'Unknown':
                # GPU date mapping based on common GPU release dates
                gpu_dates = {
                    # Quadro Professional Series
                    'Quadro P5000': '2016-10-01T00:00:00',
                    'Quadro P2000': '2017-02-01T00:00:00',
                    'Quadro P4000': '2017-02-01T00:00:00',
                    'Quadro P6000': '2016-10-01T00:00:00',
                    'Quadro RTX 4000': '2018-11-13T00:00:00',
                    'Quadro RTX 5000': '2018-11-13T00:00:00',
                    'Quadro RTX 6000': '2018-11-13T00:00:00',
                    'Quadro RTX 8000': '2018-11-13T00:00:00',
                    'Quadro RTX A2000': '2021-05-31T00:00:00',
                    'Quadro RTX A4000': '2021-04-12T00:00:00',
                    'Quadro RTX A5000': '2021-04-12T00:00:00',
                    'Quadro RTX A6000': '2020-10-05T00:00:00',
                    'Quadro T1000': '2019-05-27T00:00:00',
                    'Quadro T2000': '2019-05-27T00:00:00',
                    'Quadro T400': '2020-05-14T00:00:00',
                    'Quadro T600': '2021-04-12T00:00:00',
                    'Quadro T1000': '2019-05-27T00:00:00',
                    
                    # GeForce Gaming Series
                    'GeForce GTX 1060': '2016-07-19T00:00:00',
                    'GeForce GTX 1070': '2016-06-10T00:00:00',
                    'GeForce GTX 1080': '2016-05-27T00:00:00',
                    'GeForce GTX 1650': '2019-04-23T00:00:00',
                    'GeForce GTX 1660': '2019-03-14T00:00:00',
                    'GeForce RTX 2060': '2019-01-15T00:00:00',
                    'GeForce RTX 2070': '2018-10-17T00:00:00',
                    'GeForce RTX 2080': '2018-09-20T00:00:00',
                    'GeForce RTX 3060': '2021-02-25T00:00:00',
                    'GeForce RTX 3070': '2020-10-29T00:00:00',
                    'GeForce RTX 3080': '2020-09-17T00:00:00',
                    'GeForce RTX 3090': '2020-09-24T00:00:00',
                    'GeForce RTX 4060': '2023-05-18T00:00:00',
                    'GeForce RTX 4070': '2023-04-13T00:00:00',
                    'GeForce RTX 4080': '2022-11-16T00:00:00',
                    'GeForce RTX 4090': '2022-10-12T00:00:00',
                    
                    # RTX A Series (Professional)
                    'RTX A2000': '2021-05-31T00:00:00',
                    'RTX A4000': '2021-04-12T00:00:00',
                    'RTX A5000': '2021-04-12T00:00:00',
                    'RTX A6000': '2020-10-05T00:00:00',
                    
                    # AMD Radeon Series
                    'Radeon RX 580': '2017-04-18T00:00:00',
                    'Radeon RX 6600': '2021-10-13T00:00:00',
                    'Radeon RX 6700': '2021-06-09T00:00:00',
                    'Radeon RX 6800': '2020-11-18T00:00:00',
                    'Radeon RX 6900': '2020-12-08T00:00:00',
                    'Radeon Pro WX 3200': '2019-07-15T00:00:00',
                    'Radeon Pro WX 4100': '2017-02-27T00:00:00',
                    'Radeon Pro WX 5100': '2017-02-27T00:00:00',
                    'Radeon Pro WX 7100': '2017-02-27T00:00:00',
                    'Radeon Pro WX 8200': '2018-08-13T00:00:00',
                    
                    # Intel Graphics
                    'Intel UHD Graphics': '2017-01-03T00:00:00',
                    'Intel HD Graphics': '2015-01-05T00:00:00',
                    'Intel Iris Xe': '2020-09-02T00:00:00',
                    'Intel Arc A380': '2022-06-14T00:00:00',
                    'Intel Arc A750': '2022-10-12T00:00:00',
                    'Intel Arc A770': '2022-10-12T00:00:00',
                }
                
                # Find matching GPU date with improved matching
                gpu_date = None
                gpu_name_lower = gpu_name.lower()
                
                # First try exact matches
                for gpu_key, date in gpu_dates.items():
                    if gpu_key.lower() in gpu_name_lower:
                        gpu_date = date
                        break
                
                # If no exact match, try partial matches for common patterns
                if not gpu_date:
                    # Extract key terms from GPU name
                    gpu_terms = []
                    if 'rtx' in gpu_name_lower:
                        gpu_terms.append('rtx')
                    if 'gtx' in gpu_name_lower:
                        gpu_terms.append('gtx')
                    if 'quadro' in gpu_name_lower:
                        gpu_terms.append('quadro')
                    if 'radeon' in gpu_name_lower:
                        gpu_terms.append('radeon')
                    
                    # Look for number patterns
                    import re
                    numbers = re.findall(r'\d+', gpu_name)
                    
                    # Try to match based on series and numbers
                    for gpu_key, date in gpu_dates.items():
                        key_lower = gpu_key.lower()
                        # Check if all terms match
                        if all(term in key_lower for term in gpu_terms):
                            # Check if any number from GPU name is in the key
                            if any(num in key_lower for num in numbers):
                                gpu_date = date
                                break
                
                if gpu_date:
                    self.computer_info.gpu_date = gpu_date
                else:
                    self.computer_info.gpu_date = "Unknown"
            else:
                self.computer_info.gpu_date = "Unknown"
        except Exception as e:
            self.computer_info.set_error("gpu_date", str(e))
            self.computer_info.gpu_date = "Unknown"
    
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
                    "computer_info": self.computer_info.to_dict()
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
        """Print a summary of collected information"""
        print("\n" + "="*50)
        print("COMPUTER INFORMATION SUMMARY")
        print("="*50)
        
        # Define field mappings with formatters
        field_mappings = {
            'computername': ('Computer Name', None),
            'human_name': ('User', None),
            'username': ('Username', None),
            'first_name': ('First Name', None),
            'last_name': ('Last Name', None),
            'os': ('OS', None),
            'manufacturer': ('Manufacturer', None),
            'model': ('Model', None),
            'cpu': ('CPU', None),
            'total_physical_memory': ('Memory', lambda v: f"{v / (1024**3):.1f} GB" if isinstance(v, int) else v),
            'gpu_name': ('GPU', None),
            'gpu_memory': ('GPU Memory', lambda v: f"{v:.0f} MB" if isinstance(v, (int, float)) and v is not None else v),
            'gpu_date': ('GPU Date', None),
            'serial_number': ('Serial Number', None),
            'date': ('Collection Date', None)
        }
        
        # Print all available fields
        for field_name, (display_label, formatter) in field_mappings.items():
            if hasattr(self.computer_info, field_name):
                value = getattr(self.computer_info, field_name)
                if value is not None:
                    # Apply formatter if available
                    if formatter:
                        try:
                            value = formatter(value)
                        except (TypeError, ValueError):
                            pass  # Keep original value if formatting fails
                    
                    # Special handling for User field to include username
                    if field_name == 'human_name' and self.computer_info.username:
                        print(f"{display_label}: {value} ({self.computer_info.username})")
                    else:
                        print(f"{display_label}: {value}")
        
        print("="*50)

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

        header = ttk.Label(content, text="AboutMe", font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w", pady=(0, 8))
        note = ttk.Label(content, text="After the reimaging of computers we need to collect the current machine data. You just need to approve.")
        note.pack(anchor="w", pady=(0, 12))

        columns = ("Key", "Value")
        tree = ttk.Treeview(content, columns=columns, show="headings", height=12)
        tree.heading("Key", text="Key")
        tree.heading("Value", text="Value")
        tree.column("Key", width=220, anchor="w")
        tree.column("Value", width=460, anchor="w")
        vsb = ttk.Scrollbar(content, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Dynamically get all available fields from ComputerInfo class
        computer_info = self.collector.computer_info
        display_items = []
        
        # Define field mappings: (field_name, display_label, formatter_function)
        field_mappings = {
            'computername': ('Computername', None),
            'human_name': ('Human Name', None),
            'first_name': ('First Name', None),
            'last_name': ('Last Name', None),
            'username': ('Username', None),
            'os': ('OS', None),
            'manufacturer': ('Manufacturer', None),
            'model': ('Model', None),
            'cpu': ('CPU', None),
            'total_physical_memory': ('Total Physical Memory', lambda v: f"{v / (1024**3):.1f} GB" if isinstance(v, int) else v),
            'gpu_name': ('GPU Name', None),
            'gpu_processor': ('GPU Processor', None),
            'gpu_driver': ('GPU Driver', None),
            'gpu_memory': ('GPU Memory', lambda v: f"{v:.0f} MB" if isinstance(v, (int, float)) and v is not None else v),
            'gpu_date': ('GPU Date', None),
            'serial_number': ('Serial Number', None),
            'date': ('Date', None)
        }
        
        # Add fields that have values (not None)
        for field_name, (display_label, formatter) in field_mappings.items():
            if hasattr(computer_info, field_name):
                value = getattr(computer_info, field_name)
                if value is not None:
                    # Apply formatter if available
                    if formatter:
                        try:
                            value = formatter(value)
                        except (TypeError, ValueError):
                            pass  # Keep original value if formatting fails
                    display_items.append((display_label, value))
        
        # Insert items into tree
        for label, value in display_items:
            tree.insert("", "end", values=(label, value))

        # Fixed bottom action bar
        actions = ttk.Frame(container)
        actions.pack(side="bottom", fill="x", pady=(8, 0))
        self.send_btn = ttk.Button(actions, text="Allow Share", command=self.on_send_click)
        self.cancel_btn = ttk.Button(actions, text="Disallow Share", command=self.on_close)
        self.send_btn.pack(side="left")
        self.cancel_btn.pack(side="right")
        self._add_footer(self.root)

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