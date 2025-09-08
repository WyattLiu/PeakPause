#!/usr/bin/env python3
"""
PeakPause Farm Dashboard
Real-time monitoring and control interface
"""

import json
import os
import time
import subprocess
from datetime import datetime
from farm_manager import FarmManager

class FarmDashboard:
    def __init__(self):
        self.farm = FarmManager()
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_farm_overview(self):
        """Get comprehensive farm overview"""
        overview = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'control_host': self.farm.local_ip,
            'total_hosts': len(self.farm.config['hosts']),
            'hosts': {}
        }
        
        # Get status from all hosts
        if self.farm.config['hosts']:
            status_results = self.farm.status_all_hosts()
            
            for host in self.farm.config['hosts']:
                host_config = self.farm.get_host_ssh_config(host)
                host_ip = host_config["ip"]
                host_name = host_config["name"]
                
                display_key = f"{host_name} ({host_ip})"
                
                if host_ip in status_results:
                    result = status_results[host_ip]
                    
                    overview['hosts'][display_key] = {
                        'status': result['status'],
                        'mining': 'unknown',
                        'temperature': 'unknown',
                        'rate': 'unknown'
                    }
                    
                    # Parse status output
                    if result['status'] == 'online' and 'output' in result:
                        output = result['output']
                        
                        # Extract mining status
                        if 'Mining running: True' in output:
                            overview['hosts'][display_key]['mining'] = 'active'
                        elif 'Mining running: False' in output:
                            overview['hosts'][display_key]['mining'] = 'stopped'
                        
                        # Extract temperature
                        for line in output.split('\n'):
                            if 'Temperature:' in line:
                                temp = line.split('Temperature:')[1].strip()
                                overview['hosts'][display_key]['temperature'] = temp
                            elif 'Rate:' in line:
                                rate = line.split('Rate:')[1].strip()
                                overview['hosts'][display_key]['rate'] = rate
                else:
                    overview['hosts'][display_key] = {
                        'status': 'unknown',
                        'mining': 'unknown',
                        'temperature': 'unknown',
                        'rate': 'unknown'
                    }
        
        return overview
    
    def display_dashboard(self, overview):
        """Display the dashboard"""
        self.clear_screen()
        
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 25 + "PeakPause Farm Dashboard" + " " * 29 + "║")
        print("╠" + "═" * 78 + "╣")
        
        print(f"║ Control Host: {overview['control_host']:<20} │ Total Hosts: {overview['total_hosts']:<15} │ {overview['timestamp']} ║")
        print("╠" + "═" * 78 + "╣")
        
        if overview['total_hosts'] == 0:
            print("║" + " " * 30 + "No hosts configured" + " " * 29 + "║")
        else:
            print("║ Host            │ Status     │ Mining    │ Temperature │ Rate      ║")
            print("╠" + "═" * 16 + "┼" + "═" * 11 + "┼" + "═" * 10 + "┼" + "═" * 12 + "┼" + "═" * 10 + "╣")
            
            for host, info in overview['hosts'].items():
                # Format host IP (truncate if needed)
                host_display = host[-15:] if len(host) > 15 else host
                
                # Color coding for status
                status_display = info['status'][:10]
                mining_display = info['mining'][:9]
                temp_display = info['temperature'][:11]
                rate_display = info['rate'][:9]
                
                print(f"║ {host_display:<15} │ {status_display:<10} │ {mining_display:<9} │ {temp_display:<11} │ {rate_display:<9} ║")
        
        print("╚" + "═" * 78 + "╝")
        
        # Show summary stats
        if overview['total_hosts'] > 0:
            online_count = sum(1 for h in overview['hosts'].values() if h['status'] == 'online')
            mining_count = sum(1 for h in overview['hosts'].values() if h['mining'] == 'active')
            
            print(f"\nSummary: {online_count}/{overview['total_hosts']} hosts online, {mining_count} mining")
        
        print("\nCommands:")
        print("  r - Refresh    s - Show status    d - Deploy    u - Update")
        print("  e - Emergency stop    a - Emergency start    q - Quit")
    
    def interactive_mode(self):
        """Run interactive dashboard"""
        try:
            while True:
                overview = self.get_farm_overview()
                self.display_dashboard(overview)
                
                print("\nPress command key (or Enter to refresh): ", end='', flush=True)
                
                # Non-blocking input with timeout
                import select
                import sys
                
                if select.select([sys.stdin], [], [], 5) == ([sys.stdin], [], []):
                    command = sys.stdin.readline().strip().lower()
                    
                    if command == 'q':
                        break
                    elif command == 's':
                        self.show_detailed_status()
                    elif command == 'd':
                        self.run_deployment()
                    elif command == 'u':
                        self.run_update()
                    elif command == 'e':
                        self.emergency_stop()
                    elif command == 'a':
                        self.emergency_start()
                    elif command == 'r' or command == '':
                        continue
                    else:
                        print(f"Unknown command: {command}")
                        time.sleep(2)
                else:
                    # Auto-refresh after timeout
                    continue
                    
        except KeyboardInterrupt:
            print("\nExiting dashboard...")
    
    def show_detailed_status(self):
        """Show detailed status"""
        self.clear_screen()
        print("Detailed Status Report")
        print("=" * 50)
        
        subprocess.run([sys.executable, 'farm_manager.py', '--status'])
        
        input("\nPress Enter to return to dashboard...")
    
    def run_deployment(self):
        """Run deployment"""
        self.clear_screen()
        print("Running Deployment...")
        print("=" * 30)
        
        subprocess.run([sys.executable, 'farm_manager.py', '--deploy'])
        
        input("\nPress Enter to return to dashboard...")
    
    def run_update(self):
        """Run update"""
        self.clear_screen()
        print("Running Update...")
        print("=" * 20)
        
        subprocess.run([sys.executable, 'farm_manager.py', '--update'])
        
        input("\nPress Enter to return to dashboard...")
    
    def emergency_stop(self):
        """Emergency stop"""
        self.clear_screen()
        print("EMERGENCY STOP")
        print("=" * 20)
        
        subprocess.run([sys.executable, 'config_manager.py', '--emergency-stop'])
        
        input("\nPress Enter to return to dashboard...")
    
    def emergency_start(self):
        """Emergency start"""
        self.clear_screen()
        print("EMERGENCY START")
        print("=" * 20)
        
        subprocess.run([sys.executable, 'config_manager.py', '--emergency-start'])
        
        input("\nPress Enter to return to dashboard...")
    
    def static_report(self):
        """Generate static report"""
        overview = self.get_farm_overview()
        self.display_dashboard(overview)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="PeakPause Farm Dashboard")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run interactive dashboard")
    parser.add_argument("--report", "-r", action="store_true", help="Generate static report")
    
    args = parser.parse_args()
    
    dashboard = FarmDashboard()
    
    if args.interactive:
        dashboard.interactive_mode()
    elif args.report:
        dashboard.static_report()
    else:
        # Default to static report
        dashboard.static_report()

if __name__ == "__main__":
    main()
