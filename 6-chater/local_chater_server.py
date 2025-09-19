#!/usr/bin/env python3
"""
Local Chater Time Server
A simple Flask-based time server that implements the Chater API.
"""

from flask import Flask, jsonify, request
from datetime import datetime, timezone
import time
import platform
import socket
import uuid

app = Flask(__name__)

# Server configuration
SERVER_ID = f"chater-local-{uuid.uuid4().hex[:8]}"
SERVER_NAME = "Local Chater Server"
START_TIME = datetime.now(timezone.utc)

def get_current_time():
    """Get current time in various formats."""
    now = datetime.now(timezone.utc)
    local_now = datetime.now()
    
    return {
        "local_time": now.isoformat(),
        "timezone": str(local_now.astimezone().tzinfo),
        "server_id": SERVER_ID,
        "server_name": SERVER_NAME,
        "formatted_time": {
            "date": local_now.strftime("%m/%d/%Y"),
            "time": local_now.strftime("%I:%M:%S %p"),
            "datetime": local_now.strftime("%m/%d/%Y, %I:%M:%S %p")
        }
    }

def get_uptime():
    """Calculate server uptime."""
    uptime_seconds = (datetime.now(timezone.utc) - START_TIME).total_seconds()
    
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    
    uptime_human = f"{days}d {hours}h {minutes}m {seconds}s"
    
    return {
        "uptime_seconds": uptime_seconds,
        "uptime_human": uptime_human,
        "started_at": START_TIME.isoformat()
    }

def get_timezone_info():
    """Get timezone information."""
    local_now = datetime.now()
    tz = local_now.astimezone().tzinfo
    
    return {
        "timezone": str(tz),
        "offset_hours": local_now.utcoffset().total_seconds() / 3600,
        "is_dst": local_now.dst() != timezone.utc.localize(datetime.now()).dst()
    }

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "success": True,
        "data": {
            "status": "healthy",
            "server": {
                "id": SERVER_ID,
                "name": SERVER_NAME,
                "version": "1.0.0",
                "platform": platform.system(),
                "python_version": platform.python_version()
            },
            "uptime_human": get_uptime()["uptime_human"]
        }
    })

@app.route('/local_time', methods=['POST'])
def local_time():
    """Get current local time."""
    try:
        time_data = get_current_time()
        return jsonify({
            "success": True,
            "data": time_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/time/uptime', methods=['GET'])
def uptime():
    """Get server uptime."""
    try:
        uptime_data = get_uptime()
        return jsonify(uptime_data)
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/api/v1/time/timezone', methods=['GET'])
def timezone_info():
    """Get timezone information."""
    try:
        tz_data = get_timezone_info()
        return jsonify(tz_data)
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """Get server status."""
    return jsonify({
        "server": {
            "id": SERVER_ID,
            "name": SERVER_NAME,
            "status": "running",
            "uptime": get_uptime()["uptime_human"]
        },
        "time": get_current_time()
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with basic info."""
    return jsonify({
        "service": "Chater Time Server",
        "version": "1.0.0",
        "server_id": SERVER_ID,
        "server_name": SERVER_NAME,
        "endpoints": {
            "health": "/health",
            "time": "/local_time",
            "uptime": "/api/v1/time/uptime",
            "timezone": "/api/v1/time/timezone",
            "status": "/status"
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Local Chater Time Server")
    print("=" * 40)
    print(f"Server ID: {SERVER_ID}")
    print(f"Server Name: {SERVER_NAME}")
    print(f"Platform: {platform.system()}")
    print(f"Python: {platform.python_version()}")
    print("=" * 40)
    print("Available endpoints:")
    print("  GET  /health - Health check")
    print("  POST /local_time - Get current time")
    print("  GET  /api/v1/time/uptime - Server uptime")
    print("  GET  /api/v1/time/timezone - Timezone info")
    print("  GET  /status - Server status")
    print("  GET  / - Root info")
    print("=" * 40)
    print("Starting server on http://localhost:3000")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    app.run(host='0.0.0.0', port=3000, debug=False)
