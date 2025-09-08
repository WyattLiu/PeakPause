#!/usr/bin/env python3
"""
Advanced farm configuration management
Handles bulk configuration updates across the farm
"""

import json
import os
import sys
import subprocess
import argparse
from farm_manager import FarmManager

class ConfigManager:
    def __init__(self):
        self.farm = FarmManager()
    
    def update_mining_config(self, **kwargs):
        """Update mining configuration across all hosts"""
        updates = {}
        
        if 'pool_address' in kwargs:
            updates['pool_address'] = kwargs['pool_address']
            
        if 'temperature_server' in kwargs:
            updates['temperature_server'] = kwargs['temperature_server']
            
        if 'max_temp' in kwargs:
            updates['max_temp'] = float(kwargs['max_temp'])
            
        if 'max_threads' in kwargs:
            updates['max_threads'] = int(kwargs['max_threads'])
            
        if updates:
            self.farm.config['mining_config'].update(updates)
            self.farm.save_config(self.farm.config)
            print(f"Updated mining config: {updates}")
            
            # Trigger redeployment
            print("Redeploying to apply changes...")
            results = self.farm.update_all_hosts()
            
            for host, status in results.items():
                print(f"{host}: {status}")
    
    def set_electricity_rates(self, rates_file):
        """Update electricity rates from JSON file"""
        if not os.path.exists(rates_file):
            print(f"Error: {rates_file} not found")
            return
            
        with open(rates_file, 'r') as f:
            rates = json.load(f)
            
        # Update template config
        with open('template_config.json', 'r') as f:
            template = json.load(f)
            
        template['electricity_rates'] = rates
        
        with open('template_config.json', 'w') as f:
            json.dump(template, f, indent=2)
            
        print("Updated electricity rates in template")
        
        # Redeploy
        print("Redeploying to apply new rates...")
        results = self.farm.update_all_hosts()
        
        for host, status in results.items():
            print(f"{host}: {status}")
    
    def emergency_stop(self):
        """Emergency stop mining on all hosts"""
        print("EMERGENCY STOP: Stopping mining on all hosts...")
        
        for host in self.farm.config["hosts"]:
            host_config = self.farm.get_host_ssh_config(host)
            ssh_key = os.path.expanduser(host_config["ssh_key"])
            ssh_user = host_config["ssh_user"]
            host_ip = host_config["ip"]
            host_name = host_config["name"]
            
            try:
                # Kill all xmrig processes
                subprocess.run([
                    'ssh', '-i', ssh_key, f'{ssh_user}@{host_ip}',
                    'pkill -f xmrig || true'
                ], timeout=10)
                
                print(f"✓ Stopped mining on {host_name} ({host_ip})")
                
            except Exception as e:
                print(f"✗ Failed to stop {host_name} ({host_ip}): {e}")
    
    def emergency_start(self):
        """Emergency start mining on all hosts"""
        print("EMERGENCY START: Starting mining on all hosts...")
        
        remote_path = self.farm.config["remote_path"]
        
        for host in self.farm.config["hosts"]:
            host_config = self.farm.get_host_ssh_config(host)
            ssh_key = os.path.expanduser(host_config["ssh_key"])
            ssh_user = host_config["ssh_user"] 
            host_ip = host_config["ip"]
            host_name = host_config["name"]
            
            try:
                # Force start mining
                subprocess.run([
                    'ssh', '-i', ssh_key, f'{ssh_user}@{host_ip}',
                    f'cd {remote_path} && ./venv/bin/python3 peakpause.py --force-start'
                ], timeout=15)
                
                print(f"✓ Started mining on {host_name} ({host_ip})")
                
            except Exception as e:
                print(f"✗ Failed to start {host_name} ({host_ip}): {e}")
    
    def show_farm_summary(self):
        """Show comprehensive farm summary"""
        print("PeakPause Farm Summary")
        print("=" * 50)
        
        print(f"Control Host: {self.farm.local_ip}")
        print(f"Total Hosts: {len(self.farm.config['hosts'])}")
        
        if self.farm.config['hosts']:
            print("\nConfigured Hosts:")
            for host in self.farm.config['hosts']:
                print(f"  - {host}")
        
        print(f"\nMining Config:")
        mining_config = self.farm.config['mining_config']
        for key, value in mining_config.items():
            print(f"  {key}: {value}")
        
        print(f"\nDeployment Settings:")
        deploy_config = self.farm.config['deployment']
        for key, value in deploy_config.items():
            print(f"  {key}: {value}")

def main():
    parser = argparse.ArgumentParser(description="PeakPause Farm Configuration Manager")
    parser.add_argument("--pool", help="Update pool address")
    parser.add_argument("--temp-server", help="Update temperature server")
    parser.add_argument("--max-temp", type=float, help="Update maximum temperature")
    parser.add_argument("--max-threads", type=int, help="Update maximum threads")
    parser.add_argument("--rates", help="Update electricity rates from JSON file")
    parser.add_argument("--emergency-stop", action="store_true", help="Emergency stop all mining")
    parser.add_argument("--emergency-start", action="store_true", help="Emergency start all mining")
    parser.add_argument("--summary", action="store_true", help="Show farm summary")
    
    args = parser.parse_args()
    
    config_mgr = ConfigManager()
    
    if args.emergency_stop:
        config_mgr.emergency_stop()
    elif args.emergency_start:
        config_mgr.emergency_start()
    elif args.rates:
        config_mgr.set_electricity_rates(args.rates)
    elif args.summary:
        config_mgr.show_farm_summary()
    elif any([args.pool, args.temp_server, args.max_temp, args.max_threads]):
        kwargs = {}
        if args.pool:
            kwargs['pool_address'] = args.pool
        if args.temp_server:
            kwargs['temperature_server'] = args.temp_server
        if args.max_temp:
            kwargs['max_temp'] = args.max_temp
        if args.max_threads:
            kwargs['max_threads'] = args.max_threads
            
        config_mgr.update_mining_config(**kwargs)
    else:
        config_mgr.show_farm_summary()

if __name__ == "__main__":
    main()
