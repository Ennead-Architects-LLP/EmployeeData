#!/usr/bin/env python3
"""
Chater Server Time API Client
This script connects to the Chater server and retrieves time information.
Supports server discovery and multiple connection options.
"""

import requests
import json
import sys
import socket
import threading
from datetime import datetime
import time
import argparse

# Default server configuration
DEFAULT_HOSTS = ["localhost", "127.0.0.1"]
DEFAULT_PORTS = [3000, 8000, 8080, 5000, 3001]
TIMEOUT = 5  # seconds for discovery
REQUEST_TIMEOUT = 10  # seconds for API requests

def get_local_network_hosts():
    """Get potential hosts on the local network."""
    hosts = ["localhost", "127.0.0.1"]
    
    try:
        # Get local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Generate network range (assuming /24 subnet)
        network_base = ".".join(local_ip.split(".")[:-1])
        for i in range(1, 255):
            hosts.append(f"{network_base}.{i}")
            
    except Exception as e:
        print(f"⚠️  Could not determine local network: {e}")
    
    return hosts

def discover_servers(scan_network=False):
    """Discover Chater servers on the network."""
    print("🔍 Discovering Chater servers...")
    found_servers = []
    
    def check_server(host, port):
        """Check if a server is running on the given host:port."""
        try:
            url = f"http://{host}:{port}"
            response = requests.get(f"{url}/health", timeout=TIMEOUT)
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
            pass  # Server not available on this host:port
    
    # Determine which hosts to scan
    if scan_network:
        print("🌐 Scanning local network for servers...")
        hosts = get_local_network_hosts()
    else:
        print("🏠 Checking local hosts only...")
        hosts = DEFAULT_HOSTS
    
    # Create threads for parallel discovery
    threads = []
    for host in hosts:
        for port in DEFAULT_PORTS:
            thread = threading.Thread(target=check_server, args=(host, port))
            threads.append(thread)
            thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    return found_servers

def select_server(servers):
    """Let user select which server to use."""
    if not servers:
        return None
    
    if len(servers) == 1:
        print(f"✅ Found server: {servers[0]['server_name']} at {servers[0]['url']}")
        return servers[0]
    
    print(f"\n🔍 Found {len(servers)} Chater server(s):")
    for i, server in enumerate(servers, 1):
        print(f"  {i}. {server['server_name']} ({server['server_id']}) at {server['url']}")
    
    while True:
        try:
            choice = input(f"\nSelect server (1-{len(servers)}): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(servers):
                    return servers[idx]
            print("Invalid choice. Please try again.")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def check_server_health(server_url):
    """Check if the server is running and healthy."""
    try:
        print(f"🔍 Checking server health at {server_url}...")
        response = requests.get(f"{server_url}/health", timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            health_data = response.json()
            if health_data.get('success') and health_data.get('data', {}).get('status') == 'healthy':
                print("✅ Server is healthy and running")
                return True
            else:
                print("⚠️  Server is running but not healthy")
                return False
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {server_url}")
        return False
    except requests.exceptions.Timeout:
        print("❌ Server request timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking server health: {e}")
        return False

def get_current_time(server_url):
    """Get current time from the server using the main API endpoint."""
    try:
        print("🕐 Getting current time from server...")
        response = requests.post(f"{server_url}/local_time", timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            time_data = response.json()
            if time_data.get('success'):
                data = time_data.get('data', {})
                print("\n" + "="*50)
                print("🕐 CURRENT TIME FROM SERVER")
                print("="*50)
                print(f"Server Time: {data.get('local_time', 'N/A')}")
                print(f"Timezone: {data.get('timezone', 'N/A')}")
                print(f"Server ID: {data.get('server_id', 'N/A')}")
                print(f"Server Name: {data.get('server_name', 'N/A')}")
                
                # Display formatted time
                formatted = data.get('formatted_time', {})
                if formatted:
                    print(f"Formatted Date: {formatted.get('date', 'N/A')}")
                    print(f"Formatted Time: {formatted.get('time', 'N/A')}")
                    print(f"Full DateTime: {formatted.get('datetime', 'N/A')}")
                
                print("="*50)
                return True
            else:
                print(f"❌ Server returned error: {time_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error getting time: {e}")
        return False

def get_server_uptime(server_url):
    """Get server uptime information."""
    try:
        print("\n⏱️  Getting server uptime...")
        response = requests.get(f"{server_url}/api/v1/time/uptime", timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            uptime_data = response.json()
            print(f"Server Uptime: {uptime_data.get('uptime_human', 'N/A')}")
            print(f"Started At: {uptime_data.get('started_at', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to get uptime. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting uptime: {e}")
        return False

def get_timezone_info(server_url):
    """Get server timezone information."""
    try:
        print("\n🌍 Getting timezone information...")
        response = requests.get(f"{server_url}/api/v1/time/timezone", timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            tz_data = response.json()
            print(f"Timezone: {tz_data.get('timezone', 'N/A')}")
            print(f"Offset: {tz_data.get('offset_hours', 'N/A')} hours")
            print(f"DST Active: {tz_data.get('is_dst', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to get timezone info. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting timezone info: {e}")
        return False

def main():
    """Main function to orchestrate the time request process."""
    parser = argparse.ArgumentParser(description='Chater Server Time API Client')
    parser.add_argument('--host', help='Server host (e.g., localhost, 192.168.1.100)')
    parser.add_argument('--port', type=int, help='Server port (e.g., 3000)')
    parser.add_argument('--discover', action='store_true', help='Discover servers automatically')
    parser.add_argument('--scan-network', action='store_true', help='Scan local network for servers (slower)')
    args = parser.parse_args()
    
    print("🚀 Chater Server Time API Client")
    print("=" * 40)
    
    server = None
    
    # If specific host/port provided, use it directly
    if args.host and args.port:
        server_url = f"http://{args.host}:{args.port}"
        print(f"🎯 Using specified server: {server_url}")
        if check_server_health(server_url):
            server = {'url': server_url, 'host': args.host, 'port': args.port}
    else:
        # Discover servers automatically
        servers = discover_servers(scan_network=args.scan_network)
        if servers:
            server = select_server(servers)
        else:
            print("\n❌ No Chater servers found!")
            print("💡 Make sure the Chater server is running and accessible")
            print("   You can also:")
            print("   - Specify a server manually: python ask.py --host <IP> --port <PORT>")
            print("   - Scan the network: python ask.py --scan-network")
            sys.exit(1)
    
    if not server:
        print("\n❌ No server selected")
        sys.exit(1)
    
    # Get current time
    success = get_current_time(server['url'])
    
    if success:
        # Get additional information
        get_server_uptime(server['url'])
        get_timezone_info(server['url'])
        
        print("\n✅ Time request completed successfully!")
    else:
        print("\n❌ Failed to get time from server")
        sys.exit(1)

if __name__ == "__main__":
    main()
