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
from datetime import datetime

token_file = "token.json"
with open(token_file, 'r') as f:
    token_data = json.load(f)
    EMBEDDED_GITHUB_TOKEN = token_data['token']

# EMBEDDED CONFIGURATION - Replace with your actual values
EMBEDDED_REPO_OWNER = "Ennead-Architects-LLP"
EMBEDDED_REPO_NAME = "EmployeeData"
EMBEDDED_WEBSITE_URL = "https://ennead-architects-llp.github.io/EmployeeData"

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
            self.data["Name"] = self._get_user_full_name()
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
            
            # Prepare data for transmission
            payload = {
                "event_type": "computer-data",
                "client_payload": {
                    "computer_data": self.data,
                    "timestamp": datetime.now().isoformat(),
                    "source": "about_me_app"
                }
            }
            
            headers = {
                "Authorization": f"token {EMBEDDED_GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AboutMe-ComputerInfo/1.0"
            }
            
            print(f"Sending computer information to GitHub...")
            print(f"   Computer: {self.data.get('Computername', 'Unknown')}")
            print(f"   User: {self.data.get('Name', 'Unknown')} ({self.data.get('Username', 'Unknown')})")
            
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
        print(f"User: {self.data.get('Name', 'Unknown')} ({self.data.get('Username', 'Unknown')})")
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
    """Main function - simplified for non-technical users"""
    print("🔍 Collecting your computer information...")
    print("   This may take a few seconds...")
    
    collector = ComputerInfoCollector()
    collector.collect_all_info()
    
    # Print summary
    collector.print_summary()
    
    # Send to GitHub
    print("\n📤 Sending information to the server...")
    success = collector.send_to_github_repo()
    
    if success:
        print("\n🎉 All done! Your computer information has been submitted successfully.")
        print("   You can close this window now.")
    else:
        print("\n⚠️  There was a problem sending your information.")
        print("   Please try again later or contact support.")
    
    # Keep window open so user can see the result
    input("\nPress Enter to close this window...")

if __name__ == "__main__":
    main()