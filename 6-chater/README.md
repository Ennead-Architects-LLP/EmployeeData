# Chater Server Time API Client

A Python client for connecting to Chater servers and retrieving time information. This client can automatically discover servers on your network or connect to specific servers.

## Features

- 🔍 **Automatic Server Discovery** - Finds Chater servers on your local network
- 🌐 **Network Scanning** - Scans the entire local network for servers
- 🎯 **Manual Connection** - Connect to specific servers by host and port
- ⏰ **Time Information** - Get current time, uptime, and timezone data
- 🛡️ **Error Handling** - Comprehensive error handling and user feedback

## Installation

1. Install dependencies:
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Usage

### Basic Usage (Auto-discovery)
```bash
.venv\Scripts\python.exe ask.py
```
This will automatically discover and connect to Chater servers on localhost.

### Network Scanning
```bash
.venv\Scripts\python.exe ask.py --scan-network
```
This will scan your entire local network for Chater servers (slower but more comprehensive).

### Manual Connection
```bash
.venv\Scripts\python.exe ask.py --host 192.168.1.100 --port 3000
```
Connect to a specific server at the given host and port.

### Help
```bash
.venv\Scripts\python.exe ask.py --help
```

## Examples

### Connect to a server on another computer
```bash
.venv\Scripts\python.exe ask.py --host 192.168.1.50 --port 3000
```

### Find all servers on the network
```bash
.venv\Scripts\python.exe ask.py --scan-network
```

### Connect to localhost on a different port
```bash
.venv\Scripts\python.exe ask.py --host localhost --port 8080
```

## Output

The script will display:
- Server health status
- Current time from the server
- Server uptime information
- Timezone details
- Any errors encountered

## Troubleshooting

- **No servers found**: Make sure the Chater server is running and accessible
- **Connection refused**: Check if the server is running on the specified host/port
- **Timeout errors**: The server might be slow to respond or unreachable

## API Endpoints Used

- `GET /health` - Check server health
- `POST /local_time` - Get current time
- `GET /api/v1/time/uptime` - Get server uptime
- `GET /api/v1/time/timezone` - Get timezone information
