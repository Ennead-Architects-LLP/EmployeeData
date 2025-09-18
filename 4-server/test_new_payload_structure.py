#!/usr/bin/env python3
"""
Test script for the updated server payload structure handling
Tests both new structured payload and legacy payload compatibility
"""

import json
import sys
import os

# Add the server directory to the path so we can import server functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_new_payload_structure():
    """Test the new structured payload from ComputerInfo.to_json_dict()"""
    
    # Simulate new structured payload from About Me app
    new_payload = {
        "event_type": "computer-data",
        "client_payload": {
            "timestamp": "2024-01-15T10:30:00",
            "computer_info": {
                "Computername": "TEST-WORKSTATION-01",
                "Username": "test.user",
                "human_name": "Test User",
                "os": "Windows 11 Pro",
                "manufacturer": "Dell Inc.",
                "model": "OptiPlex 7090",
                "serial_number": "ABC123456",
                "Collection Date": "2024-01-15T10:30:00",
                
                # NEW: Structured system information
                "system_info": {
                    "total_memory_bytes": 34359738368,
                    "total_memory_formatted": "32.0 GB",
                    "total_memory_mb": 32768.0,
                    "total_memory_gb": 32.0,
                    "available_memory_bytes": 26843545600,
                    "used_memory_bytes": 7516192768,
                    "memory_percent": 21.9
                },
                
                # NEW: Structured GPU information (dict of dicts)
                "all_gpus": {
                    "gpu_1": {
                        "name": "NVIDIA GeForce RTX 4070",
                        "processor": "NVIDIA GeForce RTX 4070",
                        "driver": "31.0.15.5186",
                        "memory_bytes": 8589934592,
                        "memory_mb": 8192.0,
                        "memory_gb": 8.0,
                        "memory_formatted": "8.0 GB",
                        "release_date": "2023-04-13T00:00:00",
                        "type": "Physical",
                        "priority": 3,
                        "is_virtual": False
                    },
                    "gpu_2": {
                        "name": "Intel UHD Graphics",
                        "processor": "Intel UHD Graphics",
                        "driver": "31.0.101.2115",
                        "memory_bytes": None,
                        "memory_mb": None,
                        "memory_gb": None,
                        "memory_formatted": None,
                        "release_date": "2017-01-03T00:00:00",
                        "type": "Physical",
                        "priority": 1,
                        "is_virtual": False
                    }
                },
                
                # NEW: Structured CPU information (dict of dicts)
                "all_cpus": {
                    "cpu_1": {
                        "name": "Intel Core i7-13700",
                        "processor": "Intel Core i7-13700",
                        "driver": "N/A",
                        "memory_mb": None,
                        "memory_bytes": None,
                        "release_date": "2022-10-20T00:00:00",
                        "type": "Physical",
                        "cores": 16,
                        "logical_processors": 24,
                        "max_clock_speed": 5100,
                        "architecture": 9,
                        "family": 6,
                        "model": 183,
                        "stepping": 1,
                        "virtualization_support": True,
                        "hyperthreading_enabled": True,
                        "cache_l3_size": 30720
                    }
                }
            }
        }
    }
    
    print("🧪 Testing New Structured Payload")
    print("=" * 50)
    
    try:
        # Import server functions
        from server import extract_computer_data_from_request, get_computer_summary, flatten_nested_structure
        
        # Extract computer data from new payload
        computer_data = extract_computer_data_from_request(new_payload)
        
        print(f"✅ Successfully extracted computer data")
        print(f"   Payload Version: {computer_data.get('payload_version', 'Unknown')}")
        print(f"   Data Source: {computer_data.get('data_source', 'Unknown')}")
        
        # Test summary extraction
        summary = get_computer_summary(computer_data)
        print(f"\n📊 Computer Summary:")
        print(f"   Computer: {summary['computer_name']}")
        print(f"   User: {summary['human_name']}")
        print(f"   CPU: {summary['cpu_name']} (Count: {summary['cpu_count']})")
        print(f"   GPU: {summary['gpu_name']} (Count: {summary['gpu_count']})")
        print(f"   Memory: {summary['memory']}")
        
        # Test backward compatibility fields
        print(f"\n🔄 Backward Compatibility Fields:")
        print(f"   GPU Name: {computer_data.get('GPU Name', 'Not found')}")
        print(f"   GPU Driver: {computer_data.get('GPU Driver', 'Not found')}")
        print(f"   GPU Memory: {computer_data.get('GPU Memory', 'Not found')}")
        print(f"   CPU Name: {computer_data.get('CPU Name', 'Not found')}")
        print(f"   Total Memory: {computer_data.get('Total Physical Memory Formatted', 'Not found')}")
        
        # Test structured data preservation
        print(f"\n🏗️  Structured Data Preservation:")
        print(f"   system_info present: {'system_info' in computer_data}")
        print(f"   all_gpus present: {'all_gpus' in computer_data}")
        print(f"   all_cpus present: {'all_cpus' in computer_data}")
        
        if 'all_gpus' in computer_data:
            print(f"   GPU count in structure: {len(computer_data['all_gpus'])}")
        if 'all_cpus' in computer_data:
            print(f"   CPU count in structure: {len(computer_data['all_cpus'])}")
        
        print(f"\n✅ New payload structure test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ New payload structure test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_legacy_payload_structure():
    """Test legacy payload structure for backward compatibility"""
    
    # Simulate legacy payload structure
    legacy_payload = {
        "computer_data": {
            "Computername": "LEGACY-WORKSTATION-01",
            "Username": "legacy.user",
            "human_name": "Legacy User",
            "os": "Windows 10 Pro",
            "manufacturer": "HP Inc.",
            "model": "EliteBook 850",
            "serial_number": "XYZ789012",
            "GPU Name": "Intel UHD Graphics 630",
            "GPU Driver": "27.20.100.8681",
            "GPU Memory": "Shared",
            "CPU Name": "Intel Core i5-10210U",
            "Total Physical Memory": "17179869184",
            "Total Physical Memory Formatted": "16.0 GB"
        }
    }
    
    print("\n🧪 Testing Legacy Payload Structure")
    print("=" * 50)
    
    try:
        # Import server functions
        from server import extract_computer_data_from_request, get_computer_summary
        
        # Extract computer data from legacy payload
        computer_data = extract_computer_data_from_request(legacy_payload)
        
        print(f"✅ Successfully extracted legacy computer data")
        print(f"   Payload Version: {computer_data.get('payload_version', 'Unknown')}")
        print(f"   Data Source: {computer_data.get('data_source', 'Unknown')}")
        
        # Test summary extraction
        summary = get_computer_summary(computer_data)
        print(f"\n📊 Legacy Computer Summary:")
        print(f"   Computer: {summary['computer_name']}")
        print(f"   User: {summary['human_name']}")
        print(f"   CPU: {summary['cpu_name']} (Count: {summary['cpu_count']})")
        print(f"   GPU: {summary['gpu_name']} (Count: {summary['gpu_count']})")
        print(f"   Memory: {summary['memory']}")
        
        print(f"\n✅ Legacy payload structure test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Legacy payload structure test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Server Payload Structure Updates")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # Test new structured payload
    if test_new_payload_structure():
        success_count += 1
    
    # Test legacy payload compatibility
    if test_legacy_payload_structure():
        success_count += 1
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 30)
    print(f"Tests Passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All tests PASSED! Server is ready for new payload structure.")
        return True
    else:
        print("❌ Some tests FAILED! Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
