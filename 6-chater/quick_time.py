#!/usr/bin/env python3
"""
Quick Time Check - Simple script to get time from Chater server
"""

import sys
import os

# Add current directory to path to import helpers
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from helpers import quick_time_check, list_servers, test_server

def main():
    """Main function for quick time check."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            scan_network = "--scan-network" in sys.argv
            print(list_servers(scan_network))
        elif command == "test" and len(sys.argv) >= 4:
            host, port = sys.argv[2], int(sys.argv[3])
            print(test_server(host, port))
        elif command == "help":
            print_help()
        else:
            print("Unknown command. Use 'help' for usage information.")
    else:
        print("🕐 Quick Time Check")
        print("=" * 20)
        print(quick_time_check())

def print_help():
    """Print help information."""
    print("""
🕐 Quick Time Check - Chater Server Time Utility

Usage:
  python quick_time.py                    # Get time from any available server
  python quick_time.py list              # List all available servers
  python quick_time.py list --scan-network  # Scan entire network
  python quick_time.py test <host> <port>   # Test specific server
  python quick_time.py help              # Show this help

Examples:
  python quick_time.py
  python quick_time.py list
  python quick_time.py test 10.20.133.57 3000
  python quick_time.py list --scan-network

This script automatically discovers and connects to Chater servers
to retrieve current time information.
    """.strip())

if __name__ == "__main__":
    main()
