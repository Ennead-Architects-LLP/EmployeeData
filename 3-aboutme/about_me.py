#!/usr/bin/env python3
"""
Computer Information Collector
Generates a JSON file with comprehensive computer information
Based on the GPU by User.xlsx header structure
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

class ComputerInfoCollector:
    def __init__(self, website_url=None):
        self.data = {}
        self.wmi_conn = None
        self.website_url = website_url or "https://szhang.github.io/EmployeeData"
        
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
    
    def send_to_github_repo(self, github_token, repo_owner="szhang", repo_name="EmployeeData"):
        """Send data to GitHub repository via repository dispatch API"""
        try:
            if not github_token:
                print("GitHub token required for repository dispatch")
                return False
                
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
            
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
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AboutMe-ComputerInfo/1.0"
            }
            
            print(f"Sending data to GitHub repository {repo_owner}/{repo_name}...")
            print(f"   Computer: {self.data.get('Computername', 'Unknown')}")
            print(f"   User: {self.data.get('Name', 'Unknown')} ({self.data.get('Username', 'Unknown')})")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 204:  # 204 No Content is success for repository dispatch
                print("Data successfully sent to GitHub repository!")
                print("   The data will be processed by GitHub Actions and appear on the website shortly.")
                print(f"   View workflow: https://github.com/{repo_owner}/{repo_name}/actions")
                return True
            else:
                print(f"Failed to send data. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Network error sending data: {e}")
            return False
        except Exception as e:
            print(f"Error sending data: {e}")
            return False
    
    def send_to_direct_server(self, server_url="http://localhost:5000"):
        """Send data directly to a running server (for testing)"""
        try:
            url = f"{server_url}/api/computer-data"
            
            payload = {
                "computer_data": self.data,
                "timestamp": datetime.now().isoformat(),
                "source": "about_me_app"
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AboutMe-ComputerInfo/1.0"
            }
            
            print(f"Sending data to local server at {server_url}...")
            print(f"   Computer: {self.data.get('Computername', 'Unknown')}")
            print(f"   User: {self.data.get('Name', 'Unknown')} ({self.data.get('Username', 'Unknown')})")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print("Data successfully sent to server!")
                print(f"   Response: {result.get('message', 'Success')}")
                if 'updated_employees' in result:
                    print(f"   Updated {result['updated_employees']} employee(s)")
                return True
            else:
                print(f"Failed to send data. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Network error sending data to server: {e}")
            return False
        except Exception as e:
            print(f"Error sending data to server: {e}")
            return False
    
    def send_to_github_issue(self, github_token=None, repo_owner="szhang", repo_name="EmployeeData"):
        """Send data as a GitHub issue (alternative method for static sites)"""
        try:
            if not github_token:
                print("GitHub token required for issue creation")
                return False
                
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
            
            # Format data as markdown
            data_md = self._format_data_as_markdown()
            
            payload = {
                "title": f"Computer Info: {self.data.get('Computername', 'Unknown')} - {self.data.get('Name', 'Unknown')}",
                "body": f"## Computer Information Report\n\n{data_md}\n\n---\n*Generated by AboutMe app on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                "labels": ["computer-info", "automated"]
            }
            
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            print(f"Creating GitHub issue for computer data...")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 201:
                issue_url = response.json().get("html_url")
                print(f"Data sent as GitHub issue: {issue_url}")
                return True
            else:
                print(f"Failed to create GitHub issue. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Network error creating GitHub issue: {e}")
            return False
        except Exception as e:
            print(f"Error creating GitHub issue: {e}")
            return False
    
    def _format_data_as_markdown(self):
        """Format collected data as markdown for GitHub issues"""
        md_lines = []
        
        # Basic info
        md_lines.append(f"**Computer Name:** {self.data.get('Computername', 'Unknown')}")
        md_lines.append(f"**User:** {self.data.get('Name', 'Unknown')} ({self.data.get('Username', 'Unknown')})")
        md_lines.append(f"**OS:** {self.data.get('OS', 'Unknown')}")
        md_lines.append(f"**Manufacturer:** {self.data.get('Manufacturer', 'Unknown')}")
        md_lines.append(f"**Model:** {self.data.get('Model', 'Unknown')}")
        md_lines.append(f"**CPU:** {self.data.get('CPU', 'Unknown')}")
        
        # Memory info
        memory_bytes = self.data.get('Total Physical Memory', 0)
        if memory_bytes and memory_bytes != 'Unknown':
            memory_gb = memory_bytes / (1024**3)
            md_lines.append(f"**Memory:** {memory_gb:.1f} GB ({memory_bytes:,} bytes)")
        else:
            md_lines.append(f"**Memory:** {memory_bytes}")
        
        # GPU info
        md_lines.append(f"**GPU:** {self.data.get('GPU Name', 'Unknown')}")
        md_lines.append(f"**GPU Driver:** {self.data.get('GPU Driver', 'Unknown')}")
        md_lines.append(f"**Serial Number:** {self.data.get('Serial Number', 'Unknown')}")
        
        # Raw JSON data
        md_lines.append("\n### Raw Data (JSON)")
        md_lines.append("```json")
        md_lines.append(json.dumps(self.data, indent=2, ensure_ascii=False, default=str))
        md_lines.append("```")
        
        return "\n".join(md_lines)

    def print_summary(self):
        """Print a summary of collected information"""
        print("\n=== Computer Information Summary ===")
        print(f"Computer Name: {self.data.get('Computername', 'Unknown')}")
        print(f"User: {self.data.get('Name', 'Unknown')} ({self.data.get('Username', 'Unknown')})")
        print(f"OS: {self.data.get('OS', 'Unknown')}")
        print(f"Manufacturer: {self.data.get('Manufacturer', 'Unknown')}")
        print(f"Model: {self.data.get('Model', 'Unknown')}")
        print(f"CPU: {self.data.get('CPU', 'Unknown')}")
        print(f"Memory: {self.data.get('Total Physical Memory', 'Unknown')} bytes")
        print(f"GPU: {self.data.get('GPU Name', 'Unknown')}")
        print(f"Serial Number: {self.data.get('Serial Number', 'Unknown')}")
        print("=" * 40)

def main():
    """Main function with command-line arguments"""
    parser = argparse.ArgumentParser(description="Collect computer information and optionally send to website")
    parser.add_argument("--website-url", type=str, 
                       default="https://szhang.github.io/EmployeeData",
                       help="Website URL to send data to")
    parser.add_argument("--send-to-github", action="store_true",
                       help="Send data to GitHub repository (recommended)")
    parser.add_argument("--send-to-server", action="store_true",
                       help="Send data to local server (for testing)")
    parser.add_argument("--server-url", type=str, default="http://localhost:5000",
                       help="Server URL for direct POST requests")
    parser.add_argument("--send-as-issue", action="store_true",
                       help="Send data as GitHub issue (alternative method)")
    parser.add_argument("--github-token", type=str,
                       help="GitHub token for issue creation")
    parser.add_argument("--repo-owner", type=str, default="szhang",
                       help="GitHub repository owner")
    parser.add_argument("--repo-name", type=str, default="EmployeeData",
                       help="GitHub repository name")
    parser.add_argument("--output", type=str, default="computer_info.json",
                       help="Output JSON filename")
    parser.add_argument("--no-save", action="store_true",
                       help="Don't save to local JSON file")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug output")
    
    args = parser.parse_args()
    
    print("Collecting computer information...")
    
    collector = ComputerInfoCollector(website_url=args.website_url)
    collector.collect_all_info()
    
    # Print summary
    collector.print_summary()
    
    if args.debug:
        print("\nDebug: Raw collected data:")
        print(json.dumps(collector.data, indent=2, default=str))
    
    # Save to JSON (unless disabled)
    if not args.no_save:
        collector.save_to_json(args.output)
    
    # Send data based on arguments
    success = True
    
    if args.send_to_github:
        print("\nSending data to GitHub repository...")
        success &= collector.send_to_github_repo(
            github_token=args.github_token,
            repo_owner=args.repo_owner,
            repo_name=args.repo_name
        )
    
    if args.send_to_server:
        print("\nSending data to local server...")
        success &= collector.send_to_direct_server(server_url=args.server_url)
    
    if args.send_as_issue:
        print("\nSending data as GitHub issue...")
        success &= collector.send_to_github_issue(
            github_token=args.github_token,
            repo_owner=args.repo_owner,
            repo_name=args.repo_name
        )
    
    if not args.send_to_github and not args.send_to_server and not args.send_as_issue:
        print("\nTips for sending data:")
        print("   • GitHub (recommended): --send-to-github --github-token YOUR_TOKEN")
        print("   • Local server (testing): --send-to-server")
        print("   • GitHub issue (fallback): --send-as-issue --github-token YOUR_TOKEN")
        print("   The data will be processed and appear on the website.")
    
    if success:
        print("\nCollection and transmission complete!")
    else:
        print("\nCollection complete, but some transmissions failed!")

if __name__ == "__main__":
    main()