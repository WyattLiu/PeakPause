# PeakPause - Modern Python Version

A smart cryptocurrency mining controller that optimizes mining operations based on Ontario's ULO electricity rates and temperature monitoring.

## Features

### 🔋 Smart Rate Management
- **Updated ULO Rates (Nov 2024 - Oct 2025)**:
  - Ultra-low overnight: 2.8¢/kWh (11 PM - 7 AM daily)
  - Weekend off-peak: 7.6¢/kWh (Weekends 7 AM - 11 PM)
  - Mid-peak: 12.2¢/kWh (Weekdays 7 AM - 4 PM, 9 PM - 11 PM)
  - On-peak: 28.4¢/kWh (Weekdays 4 PM - 9 PM)

### 🌡️ Modern Temperature Monitoring
- **Multiple Sources**: Socket server, HomeKit/Home Assistant, HTTP API, system thermal
- **Dynamic Thresholds**: Different temperature limits based on electricity rates
- **Smart Cooling**: More restrictive during expensive peak hours

### ⚙️ Intelligent Mining Policy
- Automatically avoids expensive peak hours
- Temperature-based safety controls
- Configurable profit margin thresholds
- Clean process management

## Quick Setup

### Method 1: Automated Setup (Recommended)
```bash
# Download and run the deployment script
curl -sSL https://raw.githubusercontent.com/WyattLiu/PeakPause/main/deploy.sh | bash

# Or clone and run locally
git clone https://github.com/WyattLiu/PeakPause.git
cd PeakPause
./quick_setup.sh
```

### Method 2: Manual Setup
```bash
# 1. Setup virtual environment
./setup_venv.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Generate configuration (with smart worker naming)
python3 setup_config.py

# 4. Test the system
python3 peakpause.py --test

# 5. Add to cron
sudo crontab -e
# Add: */5 * * * * /path/to/PeakPause/peakpause_cron.py
```

### Smart Worker Naming
The system automatically generates descriptive worker names in the format:
**`hostname_cpumodel_corecount`**

Examples:
- `server1_AMD_Ryzen_9_5950X_16_32c`
- `mining-rig_Intel_Core_i7_12700K_20c`
- `homepc_AMD_Ryzen_5_3600_12c`

This helps you easily identify machines in your mining pool dashboard.

## Temperature Monitoring Options

### 1. HomeKit/Home Assistant (Recommended)
Modern smart home integration:
```json
{
  "temperature": {
    "source": "homekit",
    "homekit_url": "http://homeassistant.local:8123/api/states/sensor.your_temp_sensor",
    "homekit_token": "your_long_lived_access_token"
  }
}
```

**Setup Home Assistant Token:**
1. Go to Profile → Long-Lived Access Tokens
2. Generate new token
3. Add to configuration

### 2. HTTP API
For custom temperature sensors:
```json
{
  "temperature": {
    "source": "http",
    "http_url": "http://your-sensor-device/api/temperature"
  }
}
```

### 3. System Thermal (Linux)
Use system temperature sensors:
```json
{
  "temperature": {
    "source": "system"
  }
}
```

### 4. Legacy Socket Server
Original socket-based monitoring:
```json
{
  "temperature": {
    "source": "socket",
    "socket_host": "192.168.1.185",
    "socket_port": 48910
  }
}
```

## Configuration Reference

### Mining Policy
```json
{
  "mining_policy": {
    "mine_on_peak": false,           // Avoid peak hours by default
    "force_mine_threshold": 50.0,    // Mine on peak if profit > 50¢/kWh
    "min_profit_margin": 1.5         // Minimum profit margin
  }
}
```

### Temperature Thresholds
```json
{
  "temperature": {
    "thresholds": {
      "ultra_low": 30.0,        // 11pm-7am (cheapest)
      "weekend_off_peak": 28.0, // Weekend days
      "mid_peak": 25.0,         // Regular weekday hours
      "on_peak": 20.0           // Expensive peak hours (most restrictive)
    }
  }
}
```

## Usage Examples

### Check Current Status
```bash
python3 peakpause.py --test
```

### Run Once (Manual Check)
```bash
python3 peakpause.py
```

### Continuous Monitoring (Testing)
```bash
python3 peakpause.py --continuous --interval 60
```

## Modern Improvements

### Compared to Original Perl Version:
- ✅ **Updated ULO rates** for 2024-2025
- ✅ **Modern temperature sources** (HomeKit, HTTP APIs)
- ✅ **Better error handling** and logging
- ✅ **Configurable policies** via JSON
- ✅ **Type hints** and clean Python code
- ✅ **Proper process management**
- ✅ **Comprehensive logging** with rotation

## Multi-Machine Deployment

### For Mining Farms
The system is designed to work across multiple machines with automatic configuration:

```bash
# Deploy to multiple machines
for host in mining-rig-{1..10}; do
  ssh $host "curl -sSL https://raw.githubusercontent.com/WyattLiu/PeakPause/main/deploy.sh | bash"
done
```

### Pre-configured Settings
- **Wallet**: `3EdDNCU8nDx2bidh1DjJ8fjqgQCpg3WrDZ` (NiceHash BTC)
- **Pool**: `192.168.1.207:3333` (local mining proxy)
- **Temperature**: Socket server at `192.168.1.185:48910`

### Worker Identification
Each machine automatically generates a unique worker name:
- CPU detection from `/proc/cpuinfo`
- Core count from `nproc`
- Hostname from system
- Format: `hostname_cpumodel_corecount`

### Verification
```bash
# Check deployment status
./deploy_verify.sh

# Test individual machine
python3 peakpause.py --test
```

## Recommended Smart Home Setup

### Option 1: Home Assistant + Zigbee Temperature Sensor
1. Install Home Assistant
2. Add Zigbee temperature sensor (Aqara, Sonoff, etc.)
3. Configure PeakPause to read from HA API

### Option 2: ESPHome Temperature Sensor
1. Create ESP32/ESP8266 with temperature sensor
2. Use ESPHome to expose HTTP API
3. Configure PeakPause to read from HTTP endpoint

### Option 3: Smart Thermostat Integration
Use existing smart thermostat (Nest, Ecobee) via their APIs.

## Performance Optimization

The script includes CPU optimization support via `randomx_boost.sh`:
```bash
# Run before starting mining for better performance
sudo ./randomx_boost.sh
```

## Monitoring and Logs

- **Main log**: `peakpause.log` - Main controller decisions
- **Mining log**: `xmrig.log` - XMRig mining output  
- **Cron log**: `cron.log` - Cron execution results

## License

MIT License - See LICENSE file for details.
