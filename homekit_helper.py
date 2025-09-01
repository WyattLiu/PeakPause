#!/usr/bin/env python3
"""
HomeKit Temperature Monitor Example
Shows how to integrate with HomeKit via Home Assistant
"""

import requests
import json
from typing import Optional

class HomeKitTemperatureMonitor:
    """Example HomeKit integration for temperature monitoring"""
    
    def __init__(self, ha_url: str, token: str, entity_id: str):
        """
        Initialize HomeKit monitor
        
        Args:
            ha_url: Home Assistant URL (e.g., "http://homeassistant.local:8123")
            token: Long-lived access token from HA
            entity_id: Entity ID of temperature sensor (e.g., "sensor.living_room_temperature")
        """
        self.ha_url = ha_url.rstrip('/')
        self.token = token
        self.entity_id = entity_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_temperature(self) -> Optional[float]:
        """Get current temperature from HomeKit sensor"""
        try:
            url = f"{self.ha_url}/api/states/{self.entity_id}"
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            temp_str = data.get("state")
            
            if temp_str in ["unavailable", "unknown", None]:
                return None
            
            return float(temp_str)
            
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"HomeKit temperature error: {e}")
            return None
    
    def get_sensor_info(self) -> dict:
        """Get detailed sensor information"""
        try:
            url = f"{self.ha_url}/api/states/{self.entity_id}"
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            print(f"HomeKit info error: {e}")
            return {}

class ESPHomeTemperatureMonitor:
    """Example ESPHome integration"""
    
    def __init__(self, device_url: str, sensor_path: str = "/sensor/temperature"):
        """
        Initialize ESPHome monitor
        
        Args:
            device_url: ESPHome device URL (e.g., "http://esp-sensor.local")
            sensor_path: API path for temperature sensor
        """
        self.device_url = device_url.rstrip('/')
        self.sensor_path = sensor_path
    
    def get_temperature(self) -> Optional[float]:
        """Get temperature from ESPHome device"""
        try:
            url = f"{self.device_url}{self.sensor_path}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            # ESPHome typically returns JSON like: {"value": 23.5, "state": "23.5"}
            data = response.json()
            
            # Try different field names
            temp = data.get("value") or data.get("state") or data.get("temperature")
            
            if temp is None:
                return None
                
            return float(temp)
            
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"ESPHome temperature error: {e}")
            return None

def setup_home_assistant_token():
    """Guide for setting up Home Assistant token"""
    print("🏠 Setting up Home Assistant for PeakPause")
    print("\n1. Open Home Assistant web interface")
    print("2. Click on your profile (bottom left)")
    print("3. Scroll down to 'Long-lived access tokens'")
    print("4. Click 'CREATE TOKEN'")
    print("5. Name it 'PeakPause' and click 'OK'")
    print("6. Copy the token and add it to peakpause_config.json")
    print("\n7. Find your temperature sensor entity ID:")
    print("   - Go to Developer Tools → States")
    print("   - Look for sensor.* entities with temperature")
    print("   - Common examples:")
    print("     * sensor.living_room_temperature")
    print("     * sensor.thermostat_temperature") 
    print("     * sensor.outdoor_temperature")

def test_homekit_integration():
    """Test HomeKit integration"""
    print("🧪 Testing HomeKit Integration")
    
    # Example configuration
    ha_url = input("Enter Home Assistant URL (e.g., http://homeassistant.local:8123): ").strip()
    token = input("Enter your long-lived access token: ").strip()
    entity_id = input("Enter temperature sensor entity ID (e.g., sensor.living_room_temperature): ").strip()
    
    if not all([ha_url, token, entity_id]):
        print("❌ Missing required information")
        return
    
    monitor = HomeKitTemperatureMonitor(ha_url, token, entity_id)
    
    print(f"\n📊 Testing sensor: {entity_id}")
    
    # Get sensor info
    info = monitor.get_sensor_info()
    if info:
        print(f"✅ Sensor found: {info.get('attributes', {}).get('friendly_name', entity_id)}")
        print(f"📍 Current state: {info.get('state')}")
        print(f"🏷️ Unit: {info.get('attributes', {}).get('unit_of_measurement', 'N/A')}")
    else:
        print("❌ Could not retrieve sensor information")
        return
    
    # Get temperature
    temp = monitor.get_temperature()
    if temp is not None:
        print(f"🌡️ Current temperature: {temp}°C")
        
        # Generate config snippet
        config_snippet = {
            "temperature": {
                "source": "homekit",
                "homekit_url": f"{ha_url}/api/states/{entity_id}",
                "homekit_token": token
            }
        }
        
        print("\n📄 Add this to your peakpause_config.json:")
        print(json.dumps(config_snippet, indent=2))
        
    else:
        print("❌ Could not read temperature")

def main():
    """Main function"""
    print("🏠 HomeKit Integration Helper for PeakPause")
    print("\nChoose an option:")
    print("1. Setup guide for Home Assistant")
    print("2. Test HomeKit integration")
    print("3. ESPHome example")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        setup_home_assistant_token()
    elif choice == "2":
        test_homekit_integration()
    elif choice == "3":
        print("\n🔌 ESPHome Example Configuration:")
        print("""
# In your ESPHome device YAML:
sensor:
  - platform: dht
    pin: GPIO2
    temperature:
      name: "Room Temperature"
      id: room_temp
    humidity:
      name: "Room Humidity"
    update_interval: 60s

# Web server for API access
web_server:
  port: 80

# This creates endpoints like:
# http://esp-device.local/sensor/room_temperature
        """)
        
        esphome_url = input("Enter ESPHome device URL (e.g., http://esp-sensor.local): ").strip()
        if esphome_url:
            monitor = ESPHomeTemperatureMonitor(esphome_url)
            temp = monitor.get_temperature()
            if temp is not None:
                print(f"🌡️ Temperature: {temp}°C")
            else:
                print("❌ Could not read temperature")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
