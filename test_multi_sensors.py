#!/usr/bin/env python3
"""
Test script to demonstrate multiple temperature sensor handling
"""

import json
import requests
from unittest.mock import patch, MagicMock
import sys
import os

# Add the current directory to path so we can import peakpause
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from peakpause import TemperatureMonitor

def test_multiple_sensors():
    """Test temperature monitoring with multiple sensors"""
    
    # Mock response with multiple temperature sensors
    mock_response_data = {
        "success": True,
        "data": [
            {
                "device_name": "Living Room Sensor",
                "temperature": 23.5
            },
            {
                "device_name": "Server Room Sensor", 
                "temperature": 19.2
            },
            {
                "device_name": "Outdoor Sensor",
                "temperature": 25.8
            }
        ]
    }
    
    # Create temperature monitor with mock config
    config = {
        "source": "http",
        "http_url": "http://test/api/temperature",
        "bias": 0
    }
    
    temp_monitor = TemperatureMonitor(config)
    
    # Mock the HTTP request
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Get temperature (should return minimum)
        temperature = temp_monitor._get_http_temperature()
        
        print(f"Test with multiple sensors:")
        print(f"Sensor readings: 23.5°C, 19.2°C, 25.8°C")
        print(f"Returned temperature (minimum): {temperature}°C")
        print(f"Expected: 19.2°C (minimum for safety)")
        
        assert temperature == 19.2, f"Expected 19.2°C but got {temperature}°C"
        print("✓ Test passed: Correctly returned minimum temperature")

def test_single_sensor():
    """Test temperature monitoring with single sensor (current behavior)"""
    
    # Mock response with single temperature sensor  
    mock_response_data = {
        "success": True,
        "data": [
            {
                "device_name": "Wifi Thermometer",
                "temperature": 22.1
            }
        ]
    }
    
    # Create temperature monitor with mock config
    config = {
        "source": "http", 
        "http_url": "http://test/api/temperature",
        "bias": 0
    }
    
    temp_monitor = TemperatureMonitor(config)
    
    # Mock the HTTP request
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Get temperature
        temperature = temp_monitor._get_http_temperature()
        
        print(f"\nTest with single sensor:")
        print(f"Sensor reading: 22.1°C")
        print(f"Returned temperature: {temperature}°C")
        
        assert temperature == 22.1, f"Expected 22.1°C but got {temperature}°C"
        print("✓ Test passed: Correctly returned single sensor temperature")

if __name__ == "__main__":
    print("Testing enhanced temperature monitoring with multiple sensor support...\n")
    test_multiple_sensors()
    test_single_sensor()
    print("\n✓ All tests passed! The code now robustly handles multiple temperature sensors.")
