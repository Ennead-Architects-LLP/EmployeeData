#!/usr/bin/env python3
"""
Computer Information Collector - Embedded Token Version
Generates a JSON file with comprehensive computer information
Embedded with GitHub token for easy distribution to non-technical users
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

# Load GitHub token with error handling
token_file = "token.json"
EMBEDDED_GITHUB_TOKEN = None

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

def setup_logging():
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
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
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
        self.data = {}
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
            self._get_system_serial()
            
            # Add timestamp
            self.data["Date"] = datetime.now().isoformat()
            
        except Exception as e:
            self.data["collection_error"] = str(e)
    
    def _get_computername(self):
        """Get computer name"""
        try:
            self.data["Computername"] = platform.node()
        except Exception as e:
            self.data["computername_error"] = str(e)
    
    def _get_user_info(self):
        """Get current user information"""
        try:
            self.data["Username"] = os.environ.get('USERNAME', os.environ.get('USER', ''))
            self.data["human_name"] = self._get_user_full_name()
        except Exception as e:
            self.data["user_info_error"] = str(e)
    
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
                    self.data["full_name_api_error"] = str(e)
            
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
    
    
    def _get_os_info(self):
        """Get operating system information"""
        try:
            self.data["OS"] = f"{platform.system()} {platform.release()}"
        except Exception as e:
            self.data["os_info_error"] = str(e)
    
    def _get_hardware_info(self):
        """Get hardware manufacturer and model information"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    # Get computer system info
                    for cs in self.wmi_conn.Win32_ComputerSystem():
                        self.data["Manufacturer"] = cs.Manufacturer
                        self.data["Model"] = cs.Model
                        break
                except Exception as e:
                    self.data["hardware_wmi_error"] = str(e)
            else:
                # Fallback for non-Windows systems
                self.data["Manufacturer"] = "Unknown"
                self.data["Model"] = "Unknown"
        except Exception as e:
            self.data["hardware_info_error"] = str(e)
    
    def _get_memory_info(self):
        """Get memory information"""
        try:
            memory = psutil.virtual_memory()
            self.data["Total Physical Memory"] = memory.total
        except Exception as e:
            self.data["memory_info_error"] = str(e)
    
    def _get_cpu_info(self):
        """Get CPU information"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    for cpu in self.wmi_conn.Win32_Processor():
                        self.data["CPU"] = cpu.Name
                        break
                except Exception as e:
                    self.data["CPU"] = platform.processor()
            else:
                self.data["CPU"] = platform.processor()
        except Exception as e:
            self.data["cpu_info_error"] = str(e)
    
    def _get_gpu_info(self):
        """Get GPU information"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    for gpu in self.wmi_conn.Win32_VideoController():
                        self.data["GPU Name"] = gpu.Name
                        self.data["GPU Processor"] = gpu.VideoProcessor
                        self.data["GPU Driver"] = gpu.DriverVersion
                        self.data["GPU Memory"] = gpu.AdapterRAM if gpu.AdapterRAM else None
                        break
                except Exception as e:
                    self.data["gpu_wmi_error"] = str(e)
            else:
                self.data["GPU Name"] = "Unknown"
                self.data["GPU Processor"] = "Unknown"
                self.data["GPU Driver"] = "Unknown"
                self.data["GPU Memory"] = None
        except Exception as e:
            self.data["gpu_info_error"] = str(e)
    
    
    def _get_system_serial(self):
        """Get system serial number"""
        try:
            if platform.system() == "Windows" and self.wmi_conn:
                try:
                    for bios in self.wmi_conn.Win32_BIOS():
                        self.data["Serial Number"] = bios.SerialNumber
                        break
                except Exception as e:
                    self.data["Serial Number"] = "Unknown"
            else:
                self.data["Serial Number"] = "Unknown"
        except Exception as e:
            self.data["Serial Number"] = "Unknown"
    
    def save_to_json(self, filename="computer_info.json"):
        """Save collected information to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
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
                    "computer_info": {
                        "computer_name": self.data.get('Computername', 'Unknown'),
                        "human_name": self.data.get('human_name', 'Unknown'),
                        "username": self.data.get('Username', 'Unknown'),
                        "cpu": self.data.get('CPU', 'Unknown'),
                        "os": self.data.get('OS', 'Unknown'),
                        "manufacturer": self.data.get('Manufacturer', 'Unknown'),
                        "model": self.data.get('Model', 'Unknown'),
                        "gpu_name": self.data.get('GPU Name', 'Unknown'),
                        "gpu_driver": self.data.get('GPU Driver', 'Unknown'),
                        "gpu_memory": self.data.get('GPU Memory'),
                        "memory_bytes": self.data.get('Total Physical Memory'),
                        "serial_number": self.data.get('Serial Number', 'Unknown')
                    }
                }
            }
            
            headers = {
                "Authorization": f"token {EMBEDDED_GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AboutMe-ComputerInfo/1.0"
            }
            
            print(f"Sending computer information to GitHub...")
            print(f"   Computer: {self.data.get('Computername', 'Unknown')}")
            print(f"   User: {self.data.get('human_name', 'Unknown')} ({self.data.get('Username', 'Unknown')})")
            
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
        print(f"Computer Name: {self.data.get('Computername', 'Unknown')}")
        print(f"User: {self.data.get('human_name', 'Unknown')} ({self.data.get('Username', 'Unknown')})")
        print(f"OS: {self.data.get('OS', 'Unknown')}")
        print(f"Manufacturer: {self.data.get('Manufacturer', 'Unknown')}")
        print(f"Model: {self.data.get('Model', 'Unknown')}")
        print(f"CPU: {self.data.get('CPU', 'Unknown')}")
        
        # Format memory nicely
        memory_bytes = self.data.get('Total Physical Memory', 0)
        if memory_bytes and memory_bytes != 'Unknown':
            memory_gb = memory_bytes / (1024**3)
            print(f"Memory: {memory_gb:.1f} GB")
        else:
            print(f"Memory: {memory_bytes}")
            
        print(f"GPU: {self.data.get('GPU Name', 'Unknown')}")
        print(f"Serial Number: {self.data.get('Serial Number', 'Unknown')}")
        print("="*50)

def main():
    """Main function - simplified for non-technical users with comprehensive error handling"""
    log_file = None
    try:
        # Setup logging first
        print("🔧 Setting up error logging...")
        log_file = setup_logging()
        if log_file:
            print(f"   Error log will be saved to: {log_file}")
        
        print("\n🔍 Collecting your computer information...")
        print("   This may take a few seconds...")
        
        # Initialize collector with error handling
        try:
            collector = ComputerInfoCollector()
            logging.info("ComputerInfoCollector initialized successfully")
        except Exception as e:
            log_error("Failed to initialize ComputerInfoCollector", e)
            raise
        
        # Collect information with error handling
        try:
            collector.collect_all_info()
            logging.info("Computer information collection completed")
        except Exception as e:
            log_error("Failed to collect computer information", e)
            raise
        
        # Print summary with error handling
        try:
            collector.print_summary()
            logging.info("Summary printed successfully")
        except Exception as e:
            log_error("Failed to print summary", e)
            print("⚠️  Warning: Could not display summary, but continuing...")
        
        # Send to GitHub with error handling
        print("\n📤 Sending information to the server...")
        try:
            success = collector.send_to_github_repo()
            if success:
                logging.info("Data sent to GitHub successfully")
                print("\n🎉 All done! Your computer information has been submitted successfully.")
                print("   You can close this window now.")
            else:
                logging.error("Failed to send data to GitHub")
                print("\n⚠️  There was a problem sending your information.")
                print("   Please try again later or contact support.")
        except Exception as e:
            log_error("Failed to send data to GitHub", e)
            print("\n❌ Error sending information to server.")
            print("   Please check the error log for details.")
            raise
    
    except Exception as e:
        # Comprehensive error handling
        error_msg = f"❌ CRITICAL ERROR: {str(e)}"
        print(f"\n{error_msg}")
        print("="*60)
        print("DETAILED ERROR INFORMATION:")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"Traceback:")
        print(traceback.format_exc())
        print("="*60)
        
        # Log the error
        log_error("Critical error in main function", e)
        
        # Save error to persistent file
        error_file = save_error_to_file(error_msg, e, log_file)
        
        # Show log file locations
        print(f"\n📝 ERROR LOG FILES CREATED:")
        if error_file:
            print(f"   📄 Main error log: {error_file}")
        if log_file:
            print(f"   📄 Detailed log: {log_file}")
        
        print("\n⚠️  The application encountered an error and cannot continue.")
        print("   Please send the error log files to support for assistance.")
        print("   The error log files are saved in the same folder as this program.")
    
    finally:
        # Keep window open so user can see the result
        try:
            input("\nPress Enter to close this window...")
        except:
            # If input fails, just wait a bit
            import time
            time.sleep(5)

if __name__ == "__main__":
    main()