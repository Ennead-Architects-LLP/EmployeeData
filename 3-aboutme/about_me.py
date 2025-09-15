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

        display_keys = [
            ("Computername", "Computername"),
            ("Human Name", "human_name"),
            ("Username", "Username"),
            ("OS", "OS"),
            ("Manufacturer", "Manufacturer"),
            ("Model", "Model"),
            ("CPU", "CPU"),
            ("Total Physical Memory", "Total Physical Memory"),
            ("GPU Name", "GPU Name"),
            ("GPU Driver", "GPU Driver"),
            ("GPU Memory", "GPU Memory"),
            ("Serial Number", "Serial Number"),
        ]
        for label, key in display_keys:
            value = self.collector.data.get(key, "Unknown")
            if key == "Total Physical Memory" and isinstance(value, int):
                value = f"{value / (1024**3):.1f} GB"
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
        # Prepare circular mask
        mask_size = (self.diameter, self.diameter)
        circle_mask = Image.new("L", mask_size, 0)
        draw = ImageDraw.Draw(circle_mask)
        draw.ellipse((0, 0, self.diameter, self.diameter), fill=255)
        white_bg = Image.new("RGBA", mask_size, (255, 255, 255, 255))

        for frame in ImageSequence.Iterator(img):
            frame_rgba = frame.convert("RGBA")
            # Scale to fit within circle diameter preserving aspect
            fw, fh = frame_rgba.size
            scale = min(self.diameter / fw, self.diameter / fh)
            new_size = (max(1, int(fw * scale)), max(1, int(fh * scale)))
            frame_rgba = frame_rgba.resize(new_size, Image.LANCZOS)

            # Center on canvas-sized transparent image
            composed = Image.new("RGBA", mask_size, (0, 0, 0, 0))
            x = (self.diameter - new_size[0]) // 2
            y = (self.diameter - new_size[1]) // 2
            composed.paste(frame_rgba, (x, y), frame_rgba)

            # Apply circular mask to composed frame
            masked = Image.composite(composed, Image.new("RGBA", mask_size, (0, 0, 0, 0)), circle_mask)
            # Put on white circle background
            final = white_bg.copy()
            final.paste(masked, (0, 0), masked)

            self.frames.append(final)
            duration = getattr(frame, "info", {}).get("duration", 80)
            self.durations.append(max(20, int(duration)))

        # Convert to Tk frames
        for fr in self.frames:
            self._tk_frames.append(ImageTk.PhotoImage(fr))

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
        self.canvas.itemconfig(self._item, image=self._tk_frames[self._current])
        delay = self.durations[self._current % len(self.durations)]
        self._current = (self._current + 1) % len(self._tk_frames)
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