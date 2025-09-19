# Chater Server Time API Client Suite

A comprehensive Python suite for connecting to Chater servers and retrieving time information. This suite includes multiple tools for server discovery, management, and time retrieval.

## 🚀 Features

- 🔍 **Automatic Server Discovery** - Finds Chater servers on your local network
- 🌐 **Network Scanning** - Scans the entire local network for servers
- 🎯 **Manual Connection** - Connect to specific servers by host and port
- ⏰ **Time Information** - Get current time, uptime, and timezone data
- 🛡️ **Error Handling** - Comprehensive error handling and user feedback
- 📊 **Server Management** - Monitor and manage multiple servers
- 🔧 **Helper Functions** - Reusable utility functions
- 📋 **Address Management** - Manage known server addresses

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `ask.py` | Main time client with discovery and selection |
| `helpers.py` | Helper functions and utility classes |
| `server_addresses.py` | Known server addresses and configuration |
| `quick_time.py` | Simple quick time check script |
| `server_manager.py` | Advanced server management and monitoring |
| `requirements.txt` | Python dependencies |

## 🛠️ Installation

1. Install dependencies:
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 🎯 Quick Start

### Get Time from Any Server
```bash
# Auto-discover and get time
.venv\Scripts\python.exe quick_time.py

# Or use the main client
.venv\Scripts\python.exe ask.py
```

### List Available Servers
```bash
# List local servers
.venv\Scripts\python.exe quick_time.py list

# Scan entire network
.venv\Scripts\python.exe quick_time.py list --scan-network
```

## 📖 Detailed Usage

### Main Client (ask.py)

#### Basic Usage (Auto-discovery)
```bash
.venv\Scripts\python.exe ask.py
```

#### Network Scanning
```bash
.venv\Scripts\python.exe ask.py --scan-network
```

#### Manual Connection
```bash
.venv\Scripts\python.exe ask.py --host 10.20.133.57 --port 3000
```

#### Help
```bash
.venv\Scripts\python.exe ask.py --help
```

### Quick Time Check (quick_time.py)

```bash
# Get time from any available server
.venv\Scripts\python.exe quick_time.py

# List all servers
.venv\Scripts\python.exe quick_time.py list

# Test specific server
.venv\Scripts\python.exe quick_time.py test 10.20.133.57 3000

# Help
.venv\Scripts\python.exe quick_time.py help
```

### Server Manager (server_manager.py)

```bash
# Check status of all known servers
.venv\Scripts\python.exe server_manager.py status

# Monitor servers for 10 minutes
.venv\Scripts\python.exe server_manager.py monitor 10

# Test connectivity
.venv\Scripts\python.exe server_manager.py test

# Export server list
.venv\Scripts\python.exe server_manager.py export my_servers.json

# Import server list
.venv\Scripts\python.exe server_manager.py import my_servers.json
```

### Server Addresses (server_addresses.py)

```bash
# List known servers
.venv\Scripts\python.exe server_addresses.py list

# Show network configuration
.venv\Scripts\python.exe server_addresses.py network

# Show API endpoints
.venv\Scripts\python.exe server_addresses.py api

# Show connection commands
.venv\Scripts\python.exe server_addresses.py commands
```

### Helper Functions (helpers.py)

```bash
# Quick time check
.venv\Scripts\python.exe helpers.py quick

# List servers
.venv\Scripts\python.exe helpers.py list

# Test server
.venv\Scripts\python.exe helpers.py test 10.20.133.57 3000
```

## 🌐 Known Servers

The suite includes pre-configured known servers:

- **Main Office Server**: `10.20.133.57:3000` (Primary server)
- **Local Development**: `localhost:3000` (Local development)
- **Backup Server**: `10.20.133.58:3000` (Backup server)

## 📊 Examples

### Connect to a server on another computer
```bash
.venv\Scripts\python.exe ask.py --host 10.20.133.57 --port 3000
```

### Find all servers on the network
```bash
.venv\Scripts\python.exe ask.py --scan-network
```

### Monitor servers continuously
```bash
.venv\Scripts\python.exe server_manager.py monitor 5
```

### Quick time check
```bash
.venv\Scripts\python.exe quick_time.py
```

## 🔧 Configuration

### Adding New Servers
Edit `server_addresses.py` to add new known servers:

```python
KNOWN_SERVERS["new_server"] = {
    "name": "New Server",
    "host": "192.168.1.100",
    "port": 3000,
    "description": "Description of the server",
    "status": "unknown",
    "last_seen": None
}
```

### Network Configuration
Modify `NETWORK_CONFIG` in `server_addresses.py` to change:
- Default ports to scan
- Timeout values
- Network range
- Discovery settings

## 📋 Output Examples

### Time Information
```
🕐 CURRENT TIME FROM SERVER
==================================================
Server Time: 2025-09-19T21:54:04.176704+00:00
Timezone: Eastern Daylight Time
Server ID: chater-001
Server Name: Chater Office Server
Formatted Date: 09/19/2025
Formatted Time: 09:54:04 PM
Full DateTime: 09/19/2025, 09:54:04 PM
==================================================
```

### Server Discovery
```
🔍 Found 3 Chater server(s):
  1. Unknown Server (unknown) at http://127.0.0.1:3000
  2. Unknown Server (unknown) at http://10.20.133.57:3000
  3. Unknown Server (unknown) at http://localhost:3000
```

## 🚨 Troubleshooting

- **No servers found**: Make sure the Chater server is running and accessible
- **Connection refused**: Check if the server is running on the specified host/port
- **Timeout errors**: The server might be slow to respond or unreachable
- **Network scanning slow**: Use `--scan-network` only when needed, it scans 254 IPs

## 🔌 API Endpoints Used

- `GET /health` - Check server health
- `POST /local_time` - Get current time
- `GET /api/v1/time/uptime` - Get server uptime
- `GET /api/v1/time/timezone` - Get timezone information
- `GET /status` - Get server status
- `GET /` - Root endpoint

## 📝 Development

### Adding New Features
1. Add helper functions to `helpers.py`
2. Update server configuration in `server_addresses.py`
3. Add new scripts as needed
4. Update this README

### Testing
```bash
# Test all components
.venv\Scripts\python.exe ask.py --help
.venv\Scripts\python.exe quick_time.py help
.venv\Scripts\python.exe server_manager.py help
.venv\Scripts\python.exe server_addresses.py list
```
