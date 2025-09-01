#!/usr/bin/env python3
"""
Configuration generator for PeakPause
Creates initial configuration files with modern defaults
"""

import json
import socket
import os
from pathlib import Path

def get_cpu_info():
    """Get CPU information for worker naming"""
    import subprocess
    import re
    
    try:
        # Get CPU model name
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        # Extract CPU model
        cpu_match = re.search(r'model name\s*:\s*(.+)', cpuinfo)
        if cpu_match:
            cpu_model = cpu_match.group(1).strip()
            # Clean up the CPU name - remove common suffixes and spaces
            cpu_model = re.sub(r'\s*(CPU|Processor|\(.*\)|@.*|with.*)', '', cpu_model, flags=re.IGNORECASE)
            cpu_model = re.sub(r'\s+', '_', cpu_model.strip())
            # Limit length and remove special chars
            cpu_model = re.sub(r'[^\w\-]', '', cpu_model)[:20]
        else:
            cpu_model = "Unknown"
        
        # Get CPU core count
        cpu_count = len([line for line in cpuinfo.split('\n') if line.startswith('processor')])
        
        return cpu_model, cpu_count
        
    except Exception:
        # Fallback method
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            return "Unknown", cpu_count
        except:
            return "Unknown", 1

def generate_xmrig_config():
    """Generate modern XMRig configuration with intelligent worker naming"""
    hostname = socket.gethostname()
    cpu_model, cpu_count = get_cpu_info()
    
    # Create descriptive worker name: hostname_cpumodel_corecount
    worker_name = f"{hostname}_{cpu_model}_{cpu_count}c"
    
    config = {
        "api": {
            "id": None,
            "worker-id": None
        },
        "http": {
            "enabled": False,
            "host": "127.0.0.1",
            "port": 0,
            "access-token": None,
            "restricted": True
        },
        "autosave": True,
        "background": False,
        "colors": True,
        "title": True,
        "randomx": {
            "init": -1,
            "init-avx2": 0,
            "mode": "auto",
            "1gb-pages": True,
            "rdmsr": True,
            "wrmsr": True,
            "cache_qos": False,
            "numa": True,
            "scratchpad_prefetch_mode": 1
        },
        "cpu": {
            "enabled": True,
            "huge-pages": True,
            "huge-pages-jit": False,
            "hw-aes": None,
            "priority": None,
            "memory-pool": True,
            "yield": True,
            "max-threads-hint": 100,
            "asm": True,
            "argon2-impl": None,
            "cn/0": False,
            "cn-lite/0": False
        },
        "opencl": {
            "enabled": False,
            "cache": True,
            "loader": None,
            "platform": "AMD",
            "adl": True,
            "cn/0": False,
            "cn-lite/0": False
        },
        "cuda": {
            "enabled": False,
            "loader": None,
            "nvml": True,
            "cn/0": False,
            "cn-lite/0": False
        },
        "donate-level": 1,
        "donate-over-proxy": 1,
        "log-file": None,
        "pools": [
            {
                "algo": None,
                "coin": "monero",
                "url": "192.168.1.207:3333",  # Local mining proxy
                "user": f"3EdDNCU8nDx2bidh1DjJ8fjqgQCpg3WrDZ.{worker_name}",
                "pass": "x",
                "rig-id": worker_name,
                "nicehash": False,
                "keepalive": True,
                "enabled": True,
                "tls": False,
                "tls-fingerprint": None,
                "daemon": False,
                "socks5": None,
                "self-select": None,
                "submit-to-origin": False
            }
        ],
        "print-time": 60,
        "health-print-time": 60,
        "dmi": True,
        "retries": 5,
        "retry-pause": 5,
        "syslog": False,
        "tls": {
            "enabled": False,
            "protocols": None,
            "cert": None,
            "cert_key": None,
            "ciphers": None,
            "ciphersuites": None,
            "dhparam": None
        },
        "dns": {
            "ipv6": False,
            "ttl": 30
        },
        "user-agent": None,
        "verbose": 0,
        "watch": True,
        "pause-on-battery": False,
        "pause-on-active": False
    }
    
    return config

def generate_peakpause_config():
    """Generate PeakPause configuration"""
    script_dir = Path(__file__).parent.absolute()
    
    config = {
        "mining": {
            "executable": str(script_dir / "xmrig"),
            "config_file": str(script_dir / "xmrig_config.json"),
            "log_file": str(script_dir / "xmrig.log")
        },
        "temperature": {
            "source": "socket",  # Options: socket, homekit, http, system
            "socket_host": "192.168.1.185",
            "socket_port": 48910,
            "homekit_url": "http://homeassistant.local:8123/api/states/sensor.temperature",
            "homekit_token": "YOUR_HOME_ASSISTANT_TOKEN",
            "http_url": "http://your-temp-sensor/api/temperature",
            "bias": 0.0,
            "thresholds": {
                "ultra_low": 30.0,      # 11pm-7am (2.8¢/kWh) - most permissive
                "weekend_off_peak": 28.0, # Weekends 7am-11pm (7.6¢/kWh)
                "mid_peak": 25.0,       # Weekdays 7am-4pm, 9pm-11pm (12.2¢/kWh)
                "on_peak": 20.0         # Weekdays 4pm-9pm (28.4¢/kWh) - most restrictive
            }
        },
        "rates": {
            "ultra_low": 2.8,           # ¢/kWh - 11pm-7am daily
            "weekend_off_peak": 7.6,    # ¢/kWh - Weekends 7am-11pm
            "mid_peak": 12.2,           # ¢/kWh - Weekdays 7am-4pm, 9pm-11pm
            "on_peak": 28.4             # ¢/kWh - Weekdays 4pm-9pm
        },
        "mining_policy": {
            "mine_on_peak": False,      # Generally avoid peak hours
            "force_mine_threshold": 50.0, # Force mine if profitability > 50¢/kWh
            "min_profit_margin": 1.5    # Minimum profit margin ratio
        },
        "logging": {
            "level": "INFO",
            "file": str(script_dir / "peakpause.log"),
            "max_bytes": 10485760,      # 10MB
            "backup_count": 5
        }
    }
    
    return config

def main():
    """Generate configuration files"""
    print("🔧 Generating PeakPause configuration files...")
    
    # Get CPU info for display
    cpu_model, cpu_count = get_cpu_info()
    hostname = socket.gethostname()
    worker_name = f"{hostname}_{cpu_model}_{cpu_count}c"
    
    print(f"🖥️  Detected: {hostname}")
    print(f"🔧 CPU: {cpu_model} ({cpu_count} cores)")
    print(f"🏷️  Worker name: {worker_name}")
    
    # Generate XMRig config
    xmrig_config = generate_xmrig_config()
    with open("xmrig_config.json", "w") as f:
        json.dump(xmrig_config, f, indent=2)
    print("✅ Generated xmrig_config.json")
    
    # Generate PeakPause config
    peakpause_config = generate_peakpause_config()
    with open("peakpause_config.json", "w") as f:
        json.dump(peakpause_config, f, indent=2)
    print("✅ Generated peakpause_config.json")
    
    print("\n📝 Configuration Summary:")
    print(f"   💰 Wallet: 3EdDNCU8nDx2bidh1DjJ8fjqgQCpg3WrDZ")
    print(f"   🏊 Pool: 192.168.1.207:3333 (local proxy)")
    print(f"   👤 Worker: {worker_name}")
    print(f"   🌡️  Temperature: Socket server (192.168.1.185:48910)")
    
    print("\n📋 Next steps:")
    print("1. Verify pool configuration in xmrig_config.json")
    print("2. Update wallet address if different")
    print("3. Configure temperature monitoring in peakpause_config.json")
    print("4. Test: python3 peakpause.py --test")
    print("5. Add to cron: */5 * * * * $(pwd)/peakpause_cron.py")
    
    print("\n💡 Worker naming format: hostname_cpumodel_corecount")
    print("   This helps identify machines in your mining pool dashboard")

if __name__ == "__main__":
    main()
