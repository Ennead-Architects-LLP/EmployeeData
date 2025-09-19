#!/usr/bin/env python3
"""
Chater Server Helper Functions
Common utility functions for working with Chater servers.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class ChaterHelper:
    """Helper class for Chater server operations."""
    
    def __init__(self, server_url: str = None):
        """Initialize with optional server URL."""
        self.server_url = server_url
        self.timeout = 10
    
    def discover_servers(self, scan_network: bool = False) -> List[Dict]:
        """Discover available Chater servers."""
        import threading
        import socket
        
        found_servers = []
        ports = [3000, 8000, 8080, 5000, 3001]
        
        def get_local_network_hosts():
            """Get potential hosts on the local network."""
            hosts = ["localhost", "127.0.0.1"]
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                network_base = ".".join(local_ip.split(".")[:-1])
                for i in range(1, 255):
                    hosts.append(f"{network_base}.{i}")
            except:
                pass
            return hosts
        
        def check_server(host, port):
            try:
                url = f"http://{host}:{port}"
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('data', {}).get('status') == 'healthy':
                        found_servers.append({
                            'host': host,
                            'port': port,
                            'url': url,
                            'server_id': data.get('data', {}).get('server', {}).get('id', 'unknown'),
                            'server_name': data.get('data', {}).get('server', {}).get('name', 'Unknown Server')
                        })
            except:
                pass
        
        hosts = get_local_network_hosts() if scan_network else ["localhost", "127.0.0.1"]
        
        threads = []
        for host in hosts:
            for port in ports:
                thread = threading.Thread(target=check_server, args=(host, port))
                threads.append(thread)
                thread.start()
        
        for thread in threads:
            thread.join()
        
        return found_servers
    
    def get_time(self, server_url: str = None) -> Optional[Dict]:
        """Get current time from server."""
        url = server_url or self.server_url
        if not url:
            return None
        
        try:
            response = requests.post(f"{url}/local_time", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def get_health(self, server_url: str = None) -> Optional[Dict]:
        """Get server health status."""
        url = server_url or self.server_url
        if not url:
            return None
        
        try:
            response = requests.get(f"{url}/health", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def format_time(self, time_data: Dict) -> str:
        """Format time data for display."""
        if not time_data or not time_data.get('success'):
            return "❌ Failed to get time"
        
        data = time_data.get('data', {})
        formatted = data.get('formatted_time', {})
        
        return f"""
🕐 Server Time: {data.get('local_time', 'N/A')}
🌍 Timezone: {data.get('timezone', 'N/A')}
🖥️  Server: {data.get('server_name', 'N/A')} ({data.get('server_id', 'N/A')})
📅 Date: {formatted.get('date', 'N/A')}
⏰ Time: {formatted.get('time', 'N/A')}
📝 Full: {formatted.get('datetime', 'N/A')}
        """.strip()
    
    def quick_time(self) -> str:
        """Quick time check - discover and get time from first available server."""
        servers = self.discover_servers()
        if not servers:
            return "❌ No Chater servers found"
        
        time_data = self.get_time(servers[0]['url'])
        if time_data:
            return f"✅ {servers[0]['server_name']} at {servers[0]['url']}\n{self.format_time(time_data)}"
        else:
            return f"❌ Failed to get time from {servers[0]['url']}"

def quick_time_check():
    """Quick function to get time from any available server."""
    helper = ChaterHelper()
    return helper.quick_time()

def list_servers(scan_network: bool = False):
    """List all available Chater servers."""
    helper = ChaterHelper()
    servers = helper.discover_servers(scan_network)
    
    if not servers:
        return "❌ No Chater servers found"
    
    result = f"🔍 Found {len(servers)} Chater server(s):\n"
    for i, server in enumerate(servers, 1):
        result += f"  {i}. {server['server_name']} ({server['server_id']}) at {server['url']}\n"
    
    return result.strip()

def test_server(host: str, port: int) -> str:
    """Test connection to a specific server."""
    helper = ChaterHelper()
    server_url = f"http://{host}:{port}"
    
    health = helper.get_health(server_url)
    if not health:
        return f"❌ Cannot connect to {server_url}"
    
    time_data = helper.get_time(server_url)
    if not time_data:
        return f"⚠️  Connected to {server_url} but failed to get time"
    
    return f"✅ {server_url} is working!\n{helper.format_time(time_data)}"

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            scan_network = "--scan-network" in sys.argv
            print(list_servers(scan_network))
        elif command == "quick":
            print(quick_time_check())
        elif command == "test" and len(sys.argv) >= 4:
            host, port = sys.argv[2], int(sys.argv[3])
            print(test_server(host, port))
        else:
            print("Usage: python helpers.py [list|quick|test <host> <port>] [--scan-network]")
    else:
        print(quick_time_check())
