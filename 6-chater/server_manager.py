#!/usr/bin/env python3
"""
Chater Server Manager
Advanced server management and monitoring tools.
"""

import sys
import os
import time
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from helpers import ChaterHelper
from server_addresses import KNOWN_SERVERS, get_server_url, update_server_status

class ServerManager:
    """Advanced server management class."""
    
    def __init__(self):
        self.helper = ChaterHelper()
        self.monitoring = False
        self.monitor_interval = 30  # seconds
    
    def status_all_servers(self):
        """Check status of all known servers."""
        print("🔍 Checking Status of All Known Servers")
        print("=" * 45)
        
        for name, server in KNOWN_SERVERS.items():
            print(f"\n📡 {server['name']} ({server['host']}:{server['port']})")
            print("-" * 40)
            
            server_url = get_server_url(name)
            if not server_url:
                print("❌ Invalid server configuration")
                continue
            
            # Check health
            health = self.helper.get_health(server_url)
            if health and health.get('success'):
                print("✅ Server is healthy")
                server_data = health.get('data', {})
                server_info = server_data.get('server', {})
                print(f"   Server ID: {server_info.get('id', 'N/A')}")
                print(f"   Uptime: {server_data.get('uptime_human', 'N/A')}")
                
                # Update status
                update_server_status(name, 'active', datetime.now().isoformat())
            else:
                print("❌ Server is not responding")
                update_server_status(name, 'inactive')
            
            # Try to get time
            time_data = self.helper.get_time(server_url)
            if time_data and time_data.get('success'):
                data = time_data.get('data', {})
                print(f"🕐 Current Time: {data.get('local_time', 'N/A')}")
                print(f"🌍 Timezone: {data.get('timezone', 'N/A')}")
            else:
                print("❌ Failed to get time")
    
    def monitor_servers(self, duration_minutes=5):
        """Monitor servers continuously."""
        print(f"📊 Starting server monitoring for {duration_minutes} minutes")
        print("Press Ctrl+C to stop early")
        print("=" * 50)
        
        self.monitoring = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        try:
            while self.monitoring and time.time() < end_time:
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{current_time}] Server Status Check")
                print("-" * 30)
                
                for name, server in KNOWN_SERVERS.items():
                    server_url = get_server_url(name)
                    if server_url:
                        health = self.helper.get_health(server_url)
                        status = "✅" if health and health.get('success') else "❌"
                        print(f"{status} {server['name']}: {server['host']}:{server['port']}")
                
                if time.time() < end_time:
                    print(f"\n⏳ Waiting {self.monitor_interval} seconds...")
                    time.sleep(self.monitor_interval)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
        
        self.monitoring = False
        print("📊 Monitoring completed")
    
    def test_connectivity(self):
        """Test connectivity to all servers."""
        print("🔌 Testing Connectivity to All Servers")
        print("=" * 40)
        
        results = []
        for name, server in KNOWN_SERVERS.items():
            server_url = get_server_url(name)
            if not server_url:
                results.append((name, "❌ Invalid config", 0))
                continue
            
            start_time = time.time()
            health = self.helper.get_health(server_url)
            response_time = (time.time() - start_time) * 1000  # ms
            
            if health and health.get('success'):
                results.append((name, "✅ Connected", response_time))
            else:
                results.append((name, "❌ Failed", response_time))
        
        # Display results
        for name, status, response_time in results:
            print(f"{status} {name}: {response_time:.1f}ms")
    
    def export_server_list(self, filename="server_list.json"):
        """Export current server list to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(KNOWN_SERVERS, f, indent=2)
            print(f"✅ Server list exported to {filename}")
        except Exception as e:
            print(f"❌ Failed to export server list: {e}")
    
    def import_server_list(self, filename="server_list.json"):
        """Import server list from JSON file."""
        try:
            with open(filename, 'r') as f:
                imported_servers = json.load(f)
            
            # Update known servers
            KNOWN_SERVERS.update(imported_servers)
            print(f"✅ Server list imported from {filename}")
            print(f"   Total servers: {len(KNOWN_SERVERS)}")
        except FileNotFoundError:
            print(f"❌ File {filename} not found")
        except Exception as e:
            print(f"❌ Failed to import server list: {e}")

def main():
    """Main function for server manager."""
    manager = ServerManager()
    
    if len(sys.argv) < 2:
        print("""
🔧 Chater Server Manager

Usage:
  python server_manager.py <command> [options]

Commands:
  status              - Check status of all known servers
  monitor [minutes]   - Monitor servers continuously (default: 5 minutes)
  test               - Test connectivity to all servers
  export [filename]   - Export server list to JSON (default: server_list.json)
  import [filename]   - Import server list from JSON (default: server_list.json)
  help               - Show this help

Examples:
  python server_manager.py status
  python server_manager.py monitor 10
  python server_manager.py test
  python server_manager.py export my_servers.json
        """.strip())
        return
    
    command = sys.argv[1]
    
    if command == "status":
        manager.status_all_servers()
    elif command == "monitor":
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        manager.monitor_servers(duration)
    elif command == "test":
        manager.test_connectivity()
    elif command == "export":
        filename = sys.argv[2] if len(sys.argv) > 2 else "server_list.json"
        manager.export_server_list(filename)
    elif command == "import":
        filename = sys.argv[2] if len(sys.argv) > 2 else "server_list.json"
        manager.import_server_list(filename)
    elif command == "help":
        main()  # Show help
    else:
        print(f"Unknown command: {command}")
        print("Use 'help' for available commands")

if __name__ == "__main__":
    main()
