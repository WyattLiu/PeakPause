#!/usr/bin/env python3
"""
PeakPause - Smart Mining Controller
Modernized Python version with updated ULO rates and flexible temperature monitoring
"""

import json
import subprocess
import time
import logging
import os
import signal
import socket
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class RatePeriod(Enum):
    ULTRA_LOW = "ultra_low"      # 2.8¢/kWh - 11pm-7am daily
    WEEKEND_OFF_PEAK = "weekend_off_peak"  # 7.6¢/kWh - Weekends 7am-11pm
    MID_PEAK = "mid_peak"        # 12.2¢/kWh - Weekdays 7am-4pm, 9pm-11pm
    ON_PEAK = "on_peak"          # 28.4¢/kWh - Weekdays 4pm-9pm

@dataclass
class ULORates:
    """ULO electricity rates effective Nov 1, 2024 - Oct 31, 2025"""
    ultra_low: float = 2.8      # ¢/kWh
    weekend_off_peak: float = 7.6
    mid_peak: float = 12.2
    on_peak: float = 28.4

@dataclass
class TempThresholds:
    """Temperature thresholds for different rate periods"""
    ultra_low: float = 30.0      # Most permissive - cheapest rate
    weekend_off_peak: float = 28.0
    mid_peak: float = 24.0       # Moderate - medium cost
    on_peak: float = 20.0        # Most restrictive - expensive rate

class TemperatureSource(Enum):
    SOCKET_SERVER = "socket"
    HOMEKIT = "homekit"
    HTTP_API = "http"
    SYSTEM_THERMAL = "system"

class PeakPauseConfig:
    """Configuration management for PeakPause"""
    
    def __init__(self, config_file: str = "peakpause_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self.create_default_config()
    
    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        config = {
            "mining": {
                "executable": "./xmrig",
                "config_file": "./config.json",
                "log_file": "./xmrig.log"
            },
            "temperature": {
                "source": "http",  # Use HTTP API as default
                "socket_host": "192.168.1.185",
                "socket_port": 48910,
                "homekit_url": "",
                "http_url": "http://192.168.1.149:3000/api/temperature/latest",
                "bias": 0.0,
                "thresholds": {
                    "ultra_low": 30.0,
                    "weekend_off_peak": 28.0,
                    "mid_peak": 24.0,
                    "on_peak": 20.0
                }
            },
            "rates": {
                "ultra_low": 2.8,
                "weekend_off_peak": 7.6,
                "mid_peak": 12.2,
                "on_peak": 28.4
            },
            "mining_policy": {
                "mine_on_peak": False,  # Only mine on peak if absolutely necessary
                "force_mine_threshold": 50.0,  # Force mine if profitability > 50¢/kWh
                "min_profit_margin": 1.5  # Minimum profit margin ratio
            },
            "logging": {
                "level": "INFO",
                "file": "peakpause.log",
                "max_bytes": 10485760,  # 10MB
                "backup_count": 5
            }
        }
        
        self.save_config(config)
        return config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

class TemperatureMonitor:
    """Modern temperature monitoring with multiple sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.source = TemperatureSource(config.get("source", "socket"))
        self.bias = config.get("bias", 0.0)
    
    def get_temperature(self) -> Optional[float]:
        """Get current temperature from configured source"""
        try:
            if self.source == TemperatureSource.SOCKET_SERVER:
                return self._get_socket_temperature()
            elif self.source == TemperatureSource.HOMEKIT:
                return self._get_homekit_temperature()
            elif self.source == TemperatureSource.HTTP_API:
                return self._get_http_temperature()
            elif self.source == TemperatureSource.SYSTEM_THERMAL:
                return self._get_system_temperature()
        except Exception as e:
            logging.warning(f"Failed to get temperature: {e}")
            return None
    
    def _get_socket_temperature(self) -> Optional[float]:
        """Get temperature from socket server (legacy method)"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((self.config["socket_host"], self.config["socket_port"]))
                sock.send(b"temp")
                data = sock.recv(1024).decode().strip()
                return float(data) + self.bias
        except Exception as e:
            logging.warning(f"Socket temperature failed: {e}")
            return None
    
    def _get_homekit_temperature(self) -> Optional[float]:
        """Get temperature from HomeKit via Home Assistant API"""
        # Example for Home Assistant REST API
        url = self.config.get("homekit_url")
        if not url:
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.get('homekit_token', '')}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Adjust based on your HomeKit/Home Assistant sensor format
            temp = float(data.get("state", 0))
            return temp + self.bias
        except Exception as e:
            logging.warning(f"HomeKit temperature failed: {e}")
            return None
    
    def _get_http_temperature(self) -> Optional[float]:
        """Get temperature from HTTP API - returns minimum if multiple sensors"""
        url = self.config.get("http_url")
        if not url:
            return None
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            # Try JSON first
            try:
                data = response.json()
                
                # Handle your specific API format
                if data.get("success") and "data" in data and len(data["data"]) > 0:
                    # Extract temperatures from all devices in the data array
                    temperatures = []
                    device_names = []
                    
                    for device_data in data["data"]:
                        if "temperature" in device_data:
                            temp = float(device_data.get("temperature", 0))
                            device_name = device_data.get("device_name", "Unknown Device")
                            temperatures.append(temp)
                            device_names.append(f"{device_name}({temp}°C)")
                    
                    if temperatures:
                        # Take the minimum temperature for safety (most conservative approach)
                        min_temp = min(temperatures)
                        
                        if len(temperatures) > 1:
                            logging.info(f"Multiple sensors: {', '.join(device_names)} → Using minimum: {min_temp}°C")
                        else:
                            logging.info(f"Temperature from {device_names[0]}")
                        
                        return min_temp + self.bias
                    else:
                        logging.warning("No temperature data found in API response")
                        return None
                        
                else:
                    # Fallback to generic JSON format
                    temp = float(data.get("temperature", data.get("temp", 0)))
                    logging.info(f"Temperature from HTTP API: {temp}°C")
                    return temp + self.bias
                    
            except json.JSONDecodeError:
                # Fallback to plain text
                temp = float(response.text.strip())
                logging.info(f"Temperature from HTTP API (text): {temp}°C")
                return temp + self.bias
            
        except Exception as e:
            logging.warning(f"HTTP temperature failed: {e}")
            return None
    
    def _get_system_temperature(self) -> Optional[float]:
        """Get temperature from system thermal zones"""
        try:
            # Try common thermal zone paths
            thermal_paths = [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/thermal/thermal_zone1/temp",
            ]
            
            for path in thermal_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        # Usually in millidegrees
                        temp_millidegrees = int(f.read().strip())
                        temp_celsius = temp_millidegrees / 1000.0
                        return temp_celsius + self.bias
            
            return None
        except Exception as e:
            logging.warning(f"System temperature failed: {e}")
            return None

class ULOScheduler:
    """ULO rate period scheduler with updated 2024-2025 rates"""
    
    def __init__(self, rates: ULORates):
        self.rates = rates
    
    def get_current_period(self, dt: Optional[datetime] = None) -> RatePeriod:
        """Get current ULO rate period"""
        if dt is None:
            dt = datetime.now()
        
        hour = dt.hour
        weekday = dt.weekday()  # 0=Monday, 6=Sunday
        is_weekend = weekday >= 5  # Saturday=5, Sunday=6
        
        # Ultra-low overnight: 11 PM to 7 AM every day
        if hour >= 23 or hour < 7:
            return RatePeriod.ULTRA_LOW
        
        # Weekend off-peak: Weekends 7 AM to 11 PM
        if is_weekend:
            return RatePeriod.WEEKEND_OFF_PEAK
        
        # Weekday periods
        if 7 <= hour < 16:  # 7 AM to 4 PM
            return RatePeriod.MID_PEAK
        elif 16 <= hour < 21:  # 4 PM to 9 PM
            return RatePeriod.ON_PEAK
        elif 21 <= hour < 23:  # 9 PM to 11 PM
            return RatePeriod.MID_PEAK
        
        return RatePeriod.MID_PEAK  # Fallback
    
    def get_rate(self, period: RatePeriod) -> float:
        """Get rate for given period in ¢/kWh"""
        return getattr(self.rates, period.value)

class MiningController:
    """Mining process controller"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.executable = config["executable"]
        self.config_file = config["config_file"]
        self.log_file = config["log_file"]
        self.process_pid = None
    
    def analyze_vm_activity(self) -> tuple[bool, str]:
        """Analyze VM activity level to determine if VMs are actively being used"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode != 0:
                return False, "ps command failed"
            
            vm_processes = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                line_lower = line.lower()
                if any(vm in line_lower for vm in ['qemu', 'kvm']) and 'grep' not in line:
                    parts = line.split()
                    if len(parts) >= 11 and '/usr/bin/kvm' in line:
                        try:
                            cpu_usage = float(parts[2])
                            mem_usage = float(parts[3])
                            vm_processes.append({
                                'cpu': cpu_usage,
                                'memory': mem_usage,
                                'command': ' '.join(parts[10:])
                            })
                        except (ValueError, IndexError):
                            continue
            
            if not vm_processes:
                return False, "No VMs detected"
            
            # Analyze VM activity levels
            active_vms = []
            idle_vms = []
            
            for vm in vm_processes:
                # Thresholds for "active" usage
                cpu_threshold = 50.0    # > 50% CPU = active
                memory_threshold = 20.0  # > 20% memory = significant workload
                
                vm_id = "Unknown"
                if "-id " in vm['command']:
                    try:
                        id_index = vm['command'].find("-id ") + 4
                        vm_id = vm['command'][id_index:].split()[0]
                    except:
                        pass
                
                is_active = (vm['cpu'] > cpu_threshold or vm['memory'] > memory_threshold)
                
                if is_active:
                    active_vms.append(f"VM{vm_id}({vm['cpu']:.1f}%CPU/{vm['memory']:.1f}%MEM)")
                else:
                    idle_vms.append(f"VM{vm_id}({vm['cpu']:.1f}%CPU/{vm['memory']:.1f}%MEM)")
            
            # Decision logic
            if active_vms:
                reason = f"Active VMs: {', '.join(active_vms)}"
                if idle_vms:
                    reason += f" | Idle: {', '.join(idle_vms)}"
                return True, reason
            else:
                reason = f"All VMs idle: {', '.join(idle_vms)}"
                return False, reason
                
        except Exception as e:
            logging.warning(f"VM activity analysis failed: {e}")
            return False, "Analysis failed"

    def get_optimal_cpu_settings(self) -> tuple[str, int]:
        """Determine optimal CPU cores and thread count based on system load and VM activity"""
        try:
            # Get system load average
            with open('/proc/loadavg', 'r') as f:
                load_avg = float(f.read().split()[0])  # 1-minute load average
            
            # Get number of CPU cores dynamically
            cpu_count = os.cpu_count() or 8  # Default to 8 if detection fails
            
            # Calculate load percentage
            load_percentage = (load_avg / cpu_count) * 100
            
            # Enhanced VM activity detection
            vm_active, vm_reason = self.analyze_vm_activity()
            
            # Decision logic for CPU affinity and thread count
            if vm_active or load_percentage > 50:
                # Conservative: Use only half the cores when VMs are active
                # Reserve first quarter for system, use middle half for mining
                quarter_cores = max(1, cpu_count // 4)
                start_core = quarter_cores
                end_core = quarter_cores + (cpu_count // 2) - 1
                
                # Ensure we don't exceed available cores
                end_core = min(end_core, cpu_count - 1)
                
                if start_core <= end_core:
                    cores = f"{start_core}-{end_core}"
                    available_cores = end_core - start_core + 1
                else:
                    # Fallback for very small CPU counts
                    cores = f"{max(1, cpu_count // 2)}-{cpu_count - 1}"
                    available_cores = cpu_count // 2
                
                # Thread count: half of available cores (accounting for hyperthreading)
                threads = max(1, available_cores // 2) if available_cores >= 2 else available_cores
                
                reason = f"Conservative mode: {vm_reason} | Load: {load_percentage:.1f}% | Using {available_cores}/{cpu_count} cores"
            else:
                # Aggressive: Use ALL cores when VMs are idle
                cores = f"0-{cpu_count-1}"
                threads = cpu_count  # Maximum threads when VMs are idle
                reason = f"Full hashrate mode: {vm_reason} | Load: {load_percentage:.1f}% | Using all {cpu_count} cores"
            
            logging.info(f"CPU settings: {cores} cores, {threads} threads - {reason}")
            return cores, threads
            
        except Exception as e:
            logging.warning(f"Failed to detect optimal CPU settings: {e}")
            # Safe fallback: use half the cores conservatively
            cpu_count = os.cpu_count() or 8
            half_cores = max(1, cpu_count // 2)
            fallback_cores = f"{half_cores}-{cpu_count - 1}"
            return fallback_cores, max(1, half_cores // 2)
    
    def get_thread_count_for_cores(self, cores_range: str) -> int:
        """Calculate optimal thread count based on core range"""
        try:
            if '-' in cores_range:
                start, end = map(int, cores_range.split('-'))
                core_count = end - start + 1
            else:
                core_count = len([int(c.strip()) for c in cores_range.split(',')])
            
            # For RandomX, typically 1 thread per physical core is optimal
            # Since we have hyperthreading (32 logical cores on 16 physical),
            # we'll use half the logical cores to avoid hyperthreading competition
            thread_count = max(1, core_count // 2)
            
            logging.info(f"Using {thread_count} threads for {core_count} cores")
            return thread_count
            
        except Exception as e:
            logging.warning(f"Failed to calculate thread count: {e}")
            return 8  # Safe fallback
    
    def is_running(self) -> bool:
        """Check if mining process is running"""
        pid = self.get_mining_pid()
        return pid is not None
    
    def get_mining_pid(self) -> Optional[int]:
        """Get PID of running mining process"""
        try:
            result = subprocess.run([
                'pgrep', '-f', self.executable
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                # Return first PID, kill others if multiple
                main_pid = int(pids[0])
                
                # Kill duplicate processes
                for pid_str in pids[1:]:
                    try:
                        os.kill(int(pid_str), signal.SIGTERM)
                        logging.info(f"Killed duplicate mining process: {pid_str}")
                    except ProcessLookupError:
                        pass
                
                return main_pid
            
            return None
        except Exception as e:
            logging.error(f"Error getting mining PID: {e}")
            return None
    
    def start_mining(self) -> bool:
        """Start mining process"""
        if self.is_running():
            logging.info("Mining already running")
            return True
        
        try:
            # Get optimal CPU settings based on current system load and VM activity
            cpu_cores, thread_count = self.get_optimal_cpu_settings()
            
            # Start mining with XMRig native CPU affinity, thread control, and logging
            process = subprocess.Popen([
                'nice', '-n', '19', 
                self.executable, '--config', self.config_file,
                '--threads', str(thread_count),
                '--cpu-affinity', cpu_cores,
                '--log-file', self.log_file
            ])
            
            self.process_pid = process.pid
            logging.info(f"Started mining process: PID {self.process_pid}")
            return True
        
        except Exception as e:
            logging.error(f"Failed to start mining: {e}")
            return False
    
    def stop_mining(self) -> bool:
        """Stop mining process"""
        pid = self.get_mining_pid()
        if pid is None:
            logging.info("No mining process to stop")
            return True
        
        try:
            # Try graceful shutdown first
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            
            # Force kill if still running
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Process already dead
            
            logging.info(f"Stopped mining process: PID {pid}")
            return True
        
        except Exception as e:
            logging.error(f"Failed to stop mining: {e}")
            return False

class PeakPause:
    """Main PeakPause controller"""
    
    def __init__(self, config_file: str = "peakpause_config.json"):
        self.config_manager = PeakPauseConfig(config_file)
        self.config = self.config_manager.config
        
        # Initialize components
        self.temp_monitor = TemperatureMonitor(self.config["temperature"])
        self.rates = ULORates(**self.config["rates"])
        self.scheduler = ULOScheduler(self.rates)
        self.temp_thresholds = TempThresholds(**self.config["temperature"]["thresholds"])
        self.mining_controller = MiningController(self.config["mining"])
        
        # Setup logging
        self._setup_logging()
        
        logging.info("PeakPause initialized")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config["logging"]
        
        from logging.handlers import RotatingFileHandler
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = RotatingFileHandler(
            log_config["file"],
            maxBytes=log_config["max_bytes"],
            backupCount=log_config["backup_count"]
        )
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_config["level"]),
            handlers=[file_handler, console_handler]
        )
    
    def should_mine(self, dt: Optional[datetime] = None) -> tuple[bool, str]:
        """Determine if mining should run based on rates and temperature"""
        if dt is None:
            dt = datetime.now()
        
        period = self.scheduler.get_current_period(dt)
        rate = self.scheduler.get_rate(period)
        
        # Get temperature
        temp = self.temp_monitor.get_temperature()
        temp_available = temp is not None
        
        if not temp_available:
            # No temperature reading - only mine during ultra-low rate period for safety
            if period == RatePeriod.ULTRA_LOW:
                # Only mine during ultra-low rate period (2.8¢/kWh) - cheapest electricity
                return True, f"Mining approved: {period.value} at {rate}¢/kWh (no temp sensor, ULO only)"
            else:
                # Be conservative during all other periods without temperature
                return False, f"Mining blocked: {period.value} at {rate}¢/kWh (no temp sensor, ULO only policy)"
        else:
            temp = float(temp)
        
        # Get temperature threshold for current period
        threshold = getattr(self.temp_thresholds, period.value)
        
        # Check temperature if we have a reading or are in expensive periods
        if temp_available or period in [RatePeriod.MID_PEAK, RatePeriod.ON_PEAK]:
            if temp > threshold:
                return False, f"Temperature too high: {temp:.1f}°C > {threshold}°C for {period.value}"
        
        # Check mining policy
        policy = self.config["mining_policy"]
        
        if period == RatePeriod.ON_PEAK:
            if not policy["mine_on_peak"]:
                return False, f"On-peak period blocked by policy: {rate}¢/kWh"
            
            # Only mine on peak if forced by high profitability
            if rate < policy["force_mine_threshold"]:
                return False, f"On-peak rate too high: {rate}¢/kWh < {policy['force_mine_threshold']}¢/kWh threshold"
        
        # Mine during all other periods (with temperature check passed if available)
        temp_status = f"temp {temp:.1f}°C" if temp_available else "no temp sensor"
        return True, f"Mining approved: {period.value} at {rate}¢/kWh, {temp_status}"
    
    def run_once(self, force_mining: bool = False) -> None:
        """Single execution cycle"""
        if force_mining:
            # Force mining regardless of rates or temperature
            is_running = self.mining_controller.is_running()
            if not is_running:
                logging.info("FORCE MODE: Starting mining regardless of conditions")
                self.mining_controller.start_mining()
            else:
                logging.info("FORCE MODE: Mining already running")
            return
        
        should_run, reason = self.should_mine()
        is_running = self.mining_controller.is_running()
        
        logging.info(f"Check: {reason}")
        
        if should_run and not is_running:
            logging.info("Starting mining")
            self.mining_controller.start_mining()
        elif not should_run and is_running:
            logging.info("Stopping mining")
            self.mining_controller.stop_mining()
        elif should_run and is_running:
            logging.info("Mining continues")
        else:
            logging.info("Mining remains stopped")
    
    def run_continuous(self, check_interval: int = 300) -> None:
        """Run continuous monitoring (for testing)"""
        logging.info(f"Starting continuous monitoring (check every {check_interval}s)")
        
        try:
            while True:
                self.run_once()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            logging.info("Shutting down...")
            self.mining_controller.stop_mining()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PeakPause - Smart Mining Controller")
    parser.add_argument("--config", default="peakpause_config.json", help="Config file path")
    parser.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds")
    parser.add_argument("--test", action="store_true", help="Test current conditions")
    parser.add_argument("--force", action="store_true", help="Force mining to start regardless of conditions")
    
    args = parser.parse_args()
    
    controller = PeakPause(args.config)
    
    if args.test:
        should_run, reason = controller.should_mine()
        print(f"Should mine: {should_run}")
        print(f"Reason: {reason}")
        
        # Show current status
        period = controller.scheduler.get_current_period()
        rate = controller.scheduler.get_rate(period)
        temp = controller.temp_monitor.get_temperature()
        is_running = controller.mining_controller.is_running()
        
        print(f"\nCurrent Status:")
        print(f"Period: {period.value}")
        print(f"Rate: {rate}¢/kWh")
        print(f"Temperature: {temp}°C" if temp else "Temperature: N/A")
        print(f"Mining running: {is_running}")
        
    elif args.continuous:
        controller.run_continuous(args.interval)
    elif args.force:
        print("🚨 FORCE MODE: Starting mining regardless of rates or temperature")
        controller.run_once(force_mining=True)
        print("✅ Force mining command executed")
    else:
        controller.run_once()

if __name__ == "__main__":
    main()
