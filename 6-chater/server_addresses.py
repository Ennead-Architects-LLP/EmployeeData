#!/usr/bin/env python3
"""
Chater Server Address Configuration
Known server addresses and connection information.
"""

# Known Chater Server Addresses
KNOWN_SERVERS = {
    "main_office": {
        "name": "Main Office Server",
        "host": "10.20.133.57",
        "port": 3000,
        "description": "Primary Chater server for office operations",
        "status": "active",
        "last_seen": "2025-09-19T21:55:00Z"
    },
    "localhost": {
        "name": "Local Development Server",
        "host": "localhost",
        "port": 3000,
        "description": "Local development instance",
        "status": "active",
        "last_seen": "2025-09-19T21:55:00Z"
    },
    "backup": {
        "name": "Backup Server",
        "host": "10.20.133.58",
        "port": 3000,
        "description": "Backup server for redundancy",
        "status": "unknown",
        "last_seen": None
    }
}

# Network Configuration
NETWORK_CONFIG = {
    "default_ports": [3000, 8000, 8080, 5000, 3001],
    "scan_timeout": 5,
    "request_timeout": 10,
    "network_range": "10.20.133.0/24",
    "discovery_enabled": True
}

# API Endpoints
API_ENDPOINTS = {
    "health": "/health",
    "time": "/local_time",
    "uptime": "/api/v1/time/uptime",
    "timezone": "/api/v1/time/timezone",
    "status": "/status",
    "root": "/"
}

def get_server_url(server_name: str) -> str:
    """Get full URL for a known server."""
    if server_name in KNOWN_SERVERS:
        server = KNOWN_SERVERS[server_name]
        return f"http://{server['host']}:{server['port']}"
    return None

def list_known_servers() -> str:
    """List all known servers with their information."""
    result = "📋 Known Chater Servers:\n"
    result += "=" * 50 + "\n"
    
    for name, server in KNOWN_SERVERS.items():
        status_icon = "✅" if server['status'] == 'active' else "❌" if server['status'] == 'inactive' else "❓"
        result += f"{status_icon} {server['name']}\n"
        result += f"   Host: {server['host']}:{server['port']}\n"
        result += f"   Description: {server['description']}\n"
        result += f"   Status: {server['status']}\n"
        if server['last_seen']:
            result += f"   Last Seen: {server['last_seen']}\n"
        result += "\n"
    
    return result.strip()

def get_primary_server() -> dict:
    """Get the primary server configuration."""
    return KNOWN_SERVERS.get("main_office", {})

def get_network_info() -> str:
    """Get network configuration information."""
    result = "🌐 Network Configuration:\n"
    result += "=" * 30 + "\n"
    result += f"Network Range: {NETWORK_CONFIG['network_range']}\n"
    result += f"Default Ports: {', '.join(map(str, NETWORK_CONFIG['default_ports']))}\n"
    result += f"Scan Timeout: {NETWORK_CONFIG['scan_timeout']}s\n"
    result += f"Request Timeout: {NETWORK_CONFIG['request_timeout']}s\n"
    result += f"Discovery Enabled: {NETWORK_CONFIG['discovery_enabled']}\n"
    return result

def get_api_info() -> str:
    """Get API endpoints information."""
    result = "🔌 API Endpoints:\n"
    result += "=" * 20 + "\n"
    for name, endpoint in API_ENDPOINTS.items():
        result += f"{name}: {endpoint}\n"
    return result

def update_server_status(server_name: str, status: str, last_seen: str = None):
    """Update server status and last seen time."""
    if server_name in KNOWN_SERVERS:
        KNOWN_SERVERS[server_name]['status'] = status
        if last_seen:
            KNOWN_SERVERS[server_name]['last_seen'] = last_seen

def add_server(name: str, host: str, port: int, description: str = ""):
    """Add a new server to the known servers list."""
    KNOWN_SERVERS[name] = {
        "name": name.replace('_', ' ').title(),
        "host": host,
        "port": port,
        "description": description,
        "status": "unknown",
        "last_seen": None
    }

def get_connection_commands() -> str:
    """Get example connection commands."""
    result = "💻 Connection Commands:\n"
    result += "=" * 25 + "\n"
    result += "# Using ask.py:\n"
    result += "python ask.py --host 10.20.133.57 --port 3000\n"
    result += "python ask.py --scan-network\n"
    result += "python ask.py\n\n"
    result += "# Using helpers.py:\n"
    result += "python helpers.py quick\n"
    result += "python helpers.py list\n"
    result += "python helpers.py test 10.20.133.57 3000\n\n"
    result += "# Direct API calls:\n"
    result += "curl -X POST http://10.20.133.57:3000/local_time\n"
    result += "curl http://10.20.133.57:3000/health\n"
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            print(list_known_servers())
        elif command == "network":
            print(get_network_info())
        elif command == "api":
            print(get_api_info())
        elif command == "commands":
            print(get_connection_commands())
        elif command == "primary":
            primary = get_primary_server()
            if primary:
                print(f"Primary Server: {primary['name']} at {primary['host']}:{primary['port']}")
            else:
                print("No primary server configured")
        else:
            print("Usage: python server_addresses.py [list|network|api|commands|primary]")
    else:
        print(list_known_servers())
        print("\n" + get_network_info())
        print("\n" + get_api_info())
