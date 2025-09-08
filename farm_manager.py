#!/usr/bin/env python3
"""
PeakPause Farm Deployment and Management System
Automatically deploys and manages mining across multiple hosts
"""

import os
import sys
import json
import subprocess
import socket
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional
import ipaddress
import threading
import time

class FarmManager:
    def __init__(self, config_file: str = "farm_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.local_ip = self.get_local_ip()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for farm operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
            handlers=[
                logging.FileHandler('farm_deploy.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('FarmManager')
        
    def get_local_ip(self) -> str:
        """Get the local IP address"""
        try:
            # Connect to a dummy address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def load_config(self) -> Dict:
        """Load farm configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default config
            default_config = {
                "ssh_user": "root",
                "ssh_key": "~/.ssh/id_rsa",
                "remote_path": "~/mining",
                "hosts": [],
                "deployment": {
                    "create_user": False,
                    "install_dependencies": True,
                    "setup_cron": True,
                    "start_mining": False
                },
                "mining_config": {
                    "pool_address": "192.168.1.149:3333",
                    "temperature_server": "192.168.1.149:3000"
                }
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_host_ssh_config(self, host) -> Dict:
        """Get SSH configuration for a specific host"""
        # Handle both old format (list of IPs) and new format (list of host objects)
        if isinstance(host, str):
            # Old format - use global settings
            return {
                "ip": host,
                "ssh_user": self.config.get("ssh_user", "root"),
                "ssh_key": self.config.get("ssh_key", "~/.ssh/id_rsa"),
                "name": host.replace(".", "-"),
                "remote_path": self.config.get("remote_path", "/opt/peakpause")
            }
        elif isinstance(host, dict):
            # New format - host-specific settings
            return {
                "ip": host["ip"],
                "ssh_user": host.get("ssh_user", self.config.get("ssh_user", "root")),
                "ssh_key": host.get("ssh_key", self.config.get("ssh_key", "~/.ssh/id_rsa")),
                "name": host.get("name", host["ip"].replace(".", "-")),
                "remote_path": host.get("remote_path", self.config.get("remote_path", "/opt/peakpause"))
            }
        else:
            raise ValueError(f"Invalid host format: {host}")
    
    def get_all_host_ips(self) -> List[str]:
        """Get list of all host IPs from configuration"""
        ips = []
        for host in self.config["hosts"]:
            if isinstance(host, str):
                ips.append(host)
            elif isinstance(host, dict):
                ips.append(host["ip"])
        return ips
    
    def discover_hosts(self, network: str = None) -> List[str]:
        """Discover hosts on the network that respond to SSH"""
        if not network:
            # Auto-detect network from local IP
            local_net = ipaddress.IPv4Network(f"{self.local_ip}/24", strict=False)
            network = str(local_net)
        
        self.logger.info(f"Scanning network {network} for SSH hosts...")
        active_hosts = []
        
        try:
            network_obj = ipaddress.IPv4Network(network, strict=False)
            
            def check_host(ip_str):
                """Check if host has SSH open"""
                try:
                    result = subprocess.run(
                        ['nmap', '-p', '22', '--open', ip_str],
                        capture_output=True, text=True, timeout=5
                    )
                    if 'open' in result.stdout.lower():
                        active_hosts.append(ip_str)
                        self.logger.info(f"Found SSH host: {ip_str}")
                except Exception:
                    pass
            
            # Use threading for faster scanning
            threads = []
            for ip in network_obj.hosts():
                ip_str = str(ip)
                if ip_str != self.local_ip:  # Skip our own IP
                    thread = threading.Thread(target=check_host, args=(ip_str,))
                    threads.append(thread)
                    thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
                
        except Exception as e:
            self.logger.error(f"Network discovery failed: {e}")
        
        return sorted(active_hosts)
    
    def test_ssh_connection(self, host) -> bool:
        """Test SSH connection to host"""
        host_config = self.get_host_ssh_config(host)
        ssh_key = os.path.expanduser(host_config["ssh_key"])
        ssh_user = host_config["ssh_user"]
        host_ip = host_config["ip"]
        
        try:
            result = subprocess.run([
                'ssh', '-i', ssh_key, '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=no',
                f'{ssh_user}@{host_ip}', 'echo "SSH OK"'
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"SSH test failed for {host_ip}: {e}")
            return False
    
    def setup_ssh_key(self, host) -> bool:
        """Setup SSH key for passwordless access to host"""
        host_config = self.get_host_ssh_config(host)
        ssh_key = os.path.expanduser(host_config["ssh_key"])
        ssh_user = host_config["ssh_user"]
        host_ip = host_config["ip"]
        
        self.logger.info(f"Setting up SSH key for {ssh_user}@{host_ip}...")
        
        try:
            # First, ensure we have an SSH key
            if not os.path.exists(ssh_key):
                self.logger.info("SSH key not found, generating new key...")
                key_dir = os.path.dirname(ssh_key)
                os.makedirs(key_dir, exist_ok=True)
                
                result = subprocess.run([
                    'ssh-keygen', '-t', 'rsa', '-b', '4096',
                    '-f', ssh_key, '-N', '', '-C', 'peakpause-farm'
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.logger.error(f"Failed to generate SSH key: {result.stderr}")
                    return False
                
                self.logger.info(f"Generated new SSH key: {ssh_key}")
            
            # Copy SSH key to remote host
            self.logger.info(f"Copying SSH key to {ssh_user}@{host_ip}...")
            
            result = subprocess.run([
                'ssh-copy-id', '-i', f'{ssh_key}.pub', f'{ssh_user}@{host_ip}'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info(f"✓ SSH key successfully installed on {host_ip}")
                return True
            else:
                self.logger.error(f"✗ Failed to copy SSH key to {host_ip}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"SSH key setup failed for {host_ip}: {e}")
            return False
    
    def interactive_ssh_setup(self, host, ssh_user: str = None) -> bool:
        """Interactive SSH key setup with user prompts"""
        if isinstance(host, str):
            host_ip = host
            if ssh_user is None:
                ssh_user = self.config.get("ssh_user", "root")
        else:
            host_config = self.get_host_ssh_config(host)
            host_ip = host_config["ip"]
            if ssh_user is None:
                ssh_user = host_config["ssh_user"]
        
        print(f"\n⚠️  SSH connection to {ssh_user}@{host_ip} failed!")
        print("This is likely because SSH key authentication is not set up.")
        print()
        
        # Test if host is reachable at all
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '3', host_ip], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print(f"❌ Host {host_ip} is not reachable (ping failed)")
                print("Please check:")
                print("  - Host is powered on")
                print("  - Network connectivity")
                print("  - IP address is correct")
                return False
        except Exception:
            print(f"❌ Cannot reach {host_ip}")
            return False
        
        print(f"✅ Host {host_ip} is reachable")
        
        # Ask for SSH user if not provided
        if ssh_user is None:
            ssh_user = input(f"SSH username for {host_ip} (default: root): ").strip() or "root"
        
        print(f"SSH User: {ssh_user}")
        print()
        
        response = input(f"Would you like to automatically set up SSH key access to {ssh_user}@{host_ip}? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            print(f"🔑 Setting up SSH key access to {ssh_user}@{host_ip}...")
            print(f"You may be prompted for the {ssh_user} password on the remote host.")
            print()
            
            # Create temporary host config for SSH setup
            temp_host = {
                "ip": host_ip,
                "ssh_user": ssh_user,
                "ssh_key": self.config.get("ssh_key", "~/.ssh/id_rsa")
            }
            
            if self.setup_ssh_key(temp_host):
                print(f"✅ SSH key setup successful for {ssh_user}@{host_ip}")
                
                # Test the connection again
                if self.test_ssh_connection(temp_host):
                    print(f"✅ SSH connection to {ssh_user}@{host_ip} verified!")
                    return {"ssh_user": ssh_user, "host_ip": host_ip}
                else:
                    print(f"❌ SSH connection still failing after key setup")
                    return False
            else:
                print(f"❌ SSH key setup failed for {ssh_user}@{host_ip}")
                return False
        else:
            print("SSH key setup skipped. You can set it up manually with:")
            print(f"  ssh-copy-id {ssh_user}@{host_ip}")
            return False
    
    def get_host_info(self, host) -> Dict:
        """Get system information from remote host"""
        host_config = self.get_host_ssh_config(host)
        ssh_key = os.path.expanduser(host_config["ssh_key"])
        ssh_user = host_config["ssh_user"]
        host_ip = host_config["ip"]
        
        try:
            # Get hostname, CPU info, and memory
            cmd = """
            echo "HOSTNAME: $(hostname)"
            echo "CPU_CORES: $(nproc)"
            echo "MEMORY_GB: $(free -g | awk '/^Mem:/{print $2}')"
            echo "ARCH: $(uname -m)"
            echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
            """
            
            result = subprocess.run([
                'ssh', '-i', ssh_key, '-o', 'ConnectTimeout=10',
                f'{ssh_user}@{host_ip}', cmd
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                info = {"ip": host_ip}
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip().lower()] = value.strip()
                return info
        except Exception as e:
            self.logger.error(f"Failed to get info from {host_ip}: {e}")
        
        return {"ip": host_ip, "error": "Connection failed"}
    
    def create_deployment_package(self) -> str:
        """Create deployment package with all necessary files"""
        package_dir = "peakpause_package"
        os.makedirs(package_dir, exist_ok=True)
        
        # Files to include in deployment
        files_to_copy = [
            "peakpause.py",
            "peakpause_config.json", 
            "template_config.json",
            "requirements.txt",
            "xmrig_config.json"
        ]
        
        # Create requirements.txt if it doesn't exist
        if not os.path.exists("requirements.txt"):
            with open("requirements.txt", "w") as f:
                f.write("requests>=2.25.0\n")
        
        # Copy main files
        for file in files_to_copy:
            if os.path.exists(file):
                subprocess.run(['cp', file, package_dir])
        
        # Copy xmrig binary if it exists
        if os.path.exists("xmrig"):
            os.makedirs(f"{package_dir}/xmrig", exist_ok=True)
            subprocess.run(['cp', 'xmrig', f'{package_dir}/xmrig/xmrig'])
            # Make sure it's executable
            os.chmod(f"{package_dir}/xmrig/xmrig", 0o755)
        
        # Create install script - will be customized per host during deployment
        install_script_template = """#!/bin/bash
# PeakPause Installation Script

set -e

INSTALL_DIR="{remote_path}"
USER="{ssh_user}"

echo "Installing PeakPause to $INSTALL_DIR..."

# Create directory (expand ~ if needed)
if [[ "$INSTALL_DIR" == ~* ]]; then
    INSTALL_DIR="${{INSTALL_DIR/#~/$HOME}}"
fi

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Install Python dependencies if needed
if [ "{install_dependencies}" = "true" ]; then
    echo "Installing Python dependencies..."
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3 python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip
    elif command -v apk &> /dev/null; then
        apk add --no-cache python3 py3-pip py3-virtualenv
    fi
    
    # Create virtual environment
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
else
    echo "Skipping dependency installation (disabled for this host)"
    # Check if Python 3 is available
    if command -v python3 &> /dev/null; then
        echo "Python 3 found: $(python3 --version)"
        # Try to create virtual environment anyway
        if python3 -m venv venv 2>/dev/null; then
            echo "Virtual environment created successfully"
            ./venv/bin/pip install -r requirements.txt 2>/dev/null || echo "Warning: Could not install Python packages"
        else
            echo "Warning: Could not create virtual environment"
            echo "Will try to use system Python"
        fi
    else
        echo "Warning: Python 3 not found"
    fi
fi

# Make xmrig executable
if [ -f "xmrig/xmrig" ]; then
    chmod +x xmrig/xmrig
fi

# Make main script executable
chmod +x peakpause.py

# Setup cron if requested
if [ "{setup_cron}" = "true" ]; then
    echo "Setting up cron job..."
    # Remove existing cron job
    crontab -l 2>/dev/null | grep -v "peakpause.py\|run_peakpause.sh" | crontab - || true
    
    # Add new cron job (every 5 minutes) using the flexible run script
    (crontab -l 2>/dev/null; echo "*/5 * * * * cd \\"$INSTALL_DIR\\" && ./run_peakpause.sh >/dev/null 2>&1") | crontab -
fi

echo "Installation complete!"
echo "Location: $INSTALL_DIR"

# Create run script that handles both venv and system Python
cat > run_peakpause.sh << 'RUNEOF'
#!/bin/bash
cd "$(dirname "$0")"
if [ -d "venv" ] && [ -f "venv/bin/python3" ]; then
    ./venv/bin/python3 peakpause.py "$@"
else
    python3 peakpause.py "$@"
fi
RUNEOF

chmod +x run_peakpause.sh

if [ -d "venv" ]; then
    echo "Test with: cd \\"$INSTALL_DIR\\" && ./venv/bin/python3 peakpause.py --test"
else
    echo "Test with: cd \\"$INSTALL_DIR\\" && python3 peakpause.py --test"
fi
echo "Or use: cd \\"$INSTALL_DIR\\" && ./run_peakpause.sh --test"
"""
        
        with open(f"{package_dir}/install_template.sh", "w") as f:
            f.write(install_script_template)
        
        return package_dir
    
    def create_host_install_script(self, host, remote_path: str) -> str:
        """Create host-specific install script"""
        host_config = self.get_host_ssh_config(host)
        ssh_user = host_config["ssh_user"]
        
        # Expand the tilde in the remote path for the install script
        if remote_path.startswith("~/"):
            expanded_path = f"/home/{ssh_user}" + remote_path[1:] if ssh_user != "root" else f"/root" + remote_path[1:]
        else:
            expanded_path = remote_path
        
        # Get deployment settings for this host
        if isinstance(host, dict) and "deployment" in host:
            deployment = host["deployment"]
        else:
            deployment = self.config.get("deployment", {})
        
        install_deps = deployment.get("install_dependencies", True)
        use_system_python = deployment.get("use_system_python", False)
        setup_cron = deployment.get("setup_cron", True)
        
        install_script = f"""#!/bin/bash
# PeakPause Installation Script

set -e

INSTALL_DIR="{expanded_path}"
USER="{ssh_user}"
USE_SYSTEM_PYTHON="{str(use_system_python).lower()}"
INSTALL_DEPS="{str(install_deps).lower()}"

echo "Installing PeakPause to $INSTALL_DIR..."

# Create directory and go to it
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Install Python dependencies if needed
if [ "$INSTALL_DEPS" = "true" ]; then
    echo "Installing Python dependencies..."
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3 python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip
    fi
fi

# Setup Python environment
if [ "$USE_SYSTEM_PYTHON" = "true" ]; then
    echo "Using system Python..."
    # Try to install requests with system python if possible
    if command -v pip3 &> /dev/null; then
        pip3 install requests --user --break-system-packages 2>/dev/null || pip3 install requests --user 2>/dev/null || echo "Warning: Could not install requests via pip3"
    fi
    # Create run script for system python
    cat > run_peakpause.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
/usr/bin/python3 peakpause.py "$@"
EOF
    chmod +x run_peakpause.sh
else
    echo "Setting up virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
    # Create run script for venv
    cat > run_peakpause.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./venv/bin/python3 peakpause.py "$@"
EOF
    chmod +x run_peakpause.sh
fi

# Make xmrig executable
if [ -f "xmrig/xmrig" ]; then
    chmod +x xmrig/xmrig
fi

# Make main script executable
chmod +x peakpause.py

# Setup cron if requested
if [ "{str(setup_cron).lower()}" = "true" ]; then
    echo "Setting up cron job..."
    # Remove existing cron job
    crontab -l 2>/dev/null | grep -v "peakpause.py\\|run_peakpause.sh" | crontab - || true
    
    # Add new cron job (every 5 minutes) - use absolute path
    (crontab -l 2>/dev/null; echo "*/5 * * * * cd $INSTALL_DIR && ./run_peakpause.sh >/dev/null 2>&1") | crontab -
fi

echo "Installation complete!"
echo "Location: $INSTALL_DIR"
echo "Test with: cd $INSTALL_DIR && ./run_peakpause.sh --test"
"""
        return install_script

    def deploy_to_host(self, host, package_dir: str) -> bool:
        """Deploy package to specific host"""
        host_config = self.get_host_ssh_config(host)
        ssh_key = os.path.expanduser(host_config["ssh_key"])
        ssh_user = host_config["ssh_user"]
        host_ip = host_config["ip"]
        host_name = host_config["name"]
        remote_path = host_config.get("remote_path", self.config.get("remote_path", "~/mining"))
        
        self.logger.info(f"Deploying to {host_name} ({host_ip})...")
        
        try:
            # Create remote directory
            subprocess.run([
                'ssh', '-i', ssh_key, f'{ssh_user}@{host_ip}',
                f'mkdir -p {remote_path}'
            ], check=True)
            
            # Create host-specific install script locally
            install_script_content = self.create_host_install_script(host, remote_path)
            
            # Write install script to package directory
            with open(f"{package_dir}/install.sh", "w") as f:
                f.write(install_script_content)
            
            # Make install script executable
            os.chmod(f"{package_dir}/install.sh", 0o755)
            
            # Copy package files (including the new install script)
            subprocess.run([
                'rsync', '-avz', '-e', f'ssh -i {ssh_key}',
                f'{package_dir}/', f'{ssh_user}@{host_ip}:{remote_path}/'
            ], check=True)
            
            # Create host-specific config
            host_info = self.get_host_info(host)
            hostname = host_info.get('hostname', host_name)
            
            config_content = self.create_host_config(host_ip, hostname, host_info)
            
            # Write config to remote host
            config_json = json.dumps(config_content, indent=2)
            subprocess.run([
                'ssh', '-i', ssh_key, f'{ssh_user}@{host_ip}',
                f'cat > {remote_path}/peakpause_config.json << EOF\n{config_json}\nEOF'
            ], check=True)
            
            # Run installation script
            subprocess.run([
                'ssh', '-i', ssh_key, f'{ssh_user}@{host_ip}',
                f'cd {remote_path} && ./install.sh'
            ], check=True)
            
            self.logger.info(f"✓ Successfully deployed to {host_name} ({host_ip})")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Deployment failed for {host_name} ({host_ip}): {e}")
            return False
    
    def create_host_config(self, host_ip: str, hostname: str, host_info: Dict) -> Dict:
        """Create host-specific configuration"""
        # Load base config
        with open("peakpause_config.json", "r") as f:
            base_config = json.load(f)
        
        # Customize for this host
        host_config = base_config.copy()
        
        # Set worker name to hostname
        if "pool_config" in host_config:
            host_config["pool_config"]["worker"] = hostname
        
        # Fix mining paths to be relative to deployment directory
        if "mining" in host_config:
            host_config["mining"]["executable"] = "./xmrig/xmrig"
            host_config["mining"]["config_file"] = "./xmrig_config.json"
            host_config["mining"]["log_file"] = "./xmrig.log"
        
        # Ensure log file is relative path for remote hosts
        if "logging" in host_config:
            host_config["logging"]["file"] = "peakpause.log"
        
        # Update temperature server URL if needed
        if "temperature" in host_config:
            temp_server = self.config["mining_config"]["temperature_server"]
            if host_config["temperature"]["source"] == "http":
                host_config["temperature"]["http_url"] = f"http://{temp_server}/api/temperature/latest"
        
        # Adjust CPU settings based on host specs
        cpu_cores = int(host_info.get('cpu_cores', 4))
        if "cpu_allocation" in host_config:
            # Scale thread counts based on available cores
            host_config["cpu_allocation"]["max_threads"] = min(32, cpu_cores)
            host_config["cpu_allocation"]["vm_active_threads"] = min(16, cpu_cores // 2)
        
        return host_config
    
    def status_all_hosts(self) -> Dict:
        """Get status from all configured hosts"""
        results = {}
        
        for host in self.config["hosts"]:
            host_config = self.get_host_ssh_config(host)
            host_ip = host_config["ip"]
            ssh_key = os.path.expanduser(host_config["ssh_key"])
            ssh_user = host_config["ssh_user"]
            remote_path = host_config.get("remote_path", self.config.get("remote_path", "~/mining"))
            
            try:
                # Check if mining is running and get status using the flexible run script
                cmd = f"""cd {remote_path} && ./run_peakpause.sh --test 2>/dev/null | tail -10"""
                
                result = subprocess.run([
                    'ssh', '-i', ssh_key, '-o', 'ConnectTimeout=5',
                    f'{ssh_user}@{host_ip}', cmd
                ], capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    results[host_ip] = {
                        "status": "online",
                        "output": result.stdout.strip()
                    }
                else:
                    results[host_ip] = {
                        "status": "error", 
                        "error": result.stderr.strip()
                    }
                    
            except Exception as e:
                results[host_ip] = {
                    "status": "unreachable",
                    "error": str(e)
                }
        
        return results
    
    def update_all_hosts(self) -> Dict:
        """Update PeakPause on all hosts"""
        package_dir = self.create_deployment_package()
        results = {}
        
        for host in self.config["hosts"]:
            host_config = self.get_host_ssh_config(host)
            host_ip = host_config["ip"]
            host_name = host_config["name"]
            
            success = self.deploy_to_host(host, package_dir)
            results[f"{host_name} ({host_ip})"] = "success" if success else "failed"
        
        return results

def main():
    parser = argparse.ArgumentParser(description="PeakPause Farm Management")
    parser.add_argument("--discover", action="store_true", help="Discover hosts on network")
    parser.add_argument("--deploy", action="store_true", help="Deploy to all configured hosts")
    parser.add_argument("--status", action="store_true", help="Get status from all hosts")
    parser.add_argument("--update", action="store_true", help="Update all hosts")
    parser.add_argument("--add-host", help="Add host to configuration (IP or IP:user)")
    parser.add_argument("--network", help="Network to scan (e.g., 192.168.1.0/24)")
    parser.add_argument("--fix-ssh", help="Fix SSH connection for specific host")
    parser.add_argument("--test-host", help="Test connection and get info for specific host")
    parser.add_argument("--ssh-user", help="SSH username for operations (overrides default)")
    
    args = parser.parse_args()
    
    farm = FarmManager()
    
    if args.discover:
        print(f"Local IP: {farm.local_ip}")
        hosts = farm.discover_hosts(args.network)
        print(f"\nFound {len(hosts)} hosts with SSH:")
        
        for host in hosts:
            print(f"\nTesting {host}...")
            if farm.test_ssh_connection(host):
                info = farm.get_host_info(host)
                print(f"✓ {host}: {info.get('hostname', 'unknown')} - {info.get('cpu_cores', '?')} cores, {info.get('memory_gb', '?')}GB RAM")
            else:
                print(f"✗ {host}: SSH connection failed")
    
    elif args.add_host:
        host_spec = args.add_host
        ssh_user = args.ssh_user
        
        # Parse host specification (IP or IP:user)
        if ':' in host_spec and '@' not in host_spec:
            host_ip, ssh_user = host_spec.split(':', 1)
        else:
            host_ip = host_spec
            
        print(f"Testing SSH connection to {host_ip}...")
        
        # Create temporary host config for testing
        temp_host = {
            "ip": host_ip,
            "ssh_user": ssh_user or farm.config.get("ssh_user", "root"),
            "ssh_key": farm.config.get("ssh_key", "~/.ssh/id_rsa")
        }
        
        if farm.test_ssh_connection(temp_host):
            # SSH works, get host info and add to farm
            info = farm.get_host_info(temp_host)
            hostname = info.get('hostname', host_ip.replace('.', '-'))
            
            # Check if host already exists
            existing_ips = farm.get_all_host_ips()
            if host_ip not in existing_ips:
                # Add new host configuration
                new_host = {
                    "ip": host_ip,
                    "ssh_user": temp_host["ssh_user"],
                    "ssh_key": temp_host["ssh_key"],
                    "name": hostname
                }
                
                farm.config["hosts"].append(new_host)
                farm.save_config(farm.config)
                print(f"✓ Added {host_ip} to farm configuration")
                
                # Display host info
                if 'hostname' in info:
                    print(f"  Hostname: {info.get('hostname', 'unknown')}")
                    print(f"  SSH User: {temp_host['ssh_user']}")
                    print(f"  CPU Cores: {info.get('cpu_cores', '?')}")
                    print(f"  Memory: {info.get('memory_gb', '?')}GB")
                    print(f"  Architecture: {info.get('arch', 'unknown')}")
            else:
                print(f"Host {host_ip} already in configuration")
        else:
            # SSH failed, offer to set it up
            result = farm.interactive_ssh_setup(host_ip, ssh_user)
            if result and isinstance(result, dict):
                # SSH setup successful, add to farm
                info = farm.get_host_info({
                    "ip": result["host_ip"],
                    "ssh_user": result["ssh_user"],
                    "ssh_key": farm.config.get("ssh_key", "~/.ssh/id_rsa")
                })
                hostname = info.get('hostname', result["host_ip"].replace('.', '-'))
                
                existing_ips = farm.get_all_host_ips()
                if result["host_ip"] not in existing_ips:
                    new_host = {
                        "ip": result["host_ip"],
                        "ssh_user": result["ssh_user"],
                        "ssh_key": farm.config.get("ssh_key", "~/.ssh/id_rsa"),
                        "name": hostname
                    }
                    
                    farm.config["hosts"].append(new_host)
                    farm.save_config(farm.config)
                    print(f"✓ Added {result['host_ip']} to farm configuration")
                    
                    # Display host info
                    if 'hostname' in info:
                        print(f"  Hostname: {info.get('hostname', 'unknown')}")
                        print(f"  SSH User: {result['ssh_user']}")
                        print(f"  CPU Cores: {info.get('cpu_cores', '?')}")
                        print(f"  Memory: {info.get('memory_gb', '?')}GB")
                        print(f"  Architecture: {info.get('arch', 'unknown')}")
                else:
                    print(f"Host {result['host_ip']} already in configuration")
            else:
                print(f"✗ Cannot add {host_ip} - SSH setup required")
    
    elif args.deploy:
        if not farm.config["hosts"]:
            print("No hosts configured. Use --add-host or --discover first.")
            return
        
        package_dir = farm.create_deployment_package()
        print(f"Created deployment package: {package_dir}")
        
        for host in farm.config["hosts"]:
            farm.deploy_to_host(host, package_dir)
    
    elif args.status:
        if not farm.config["hosts"]:
            print("No hosts configured.")
            return
        
        print("Getting status from all hosts...\n")
        results = farm.status_all_hosts()
        
        for host, result in results.items():
            print(f"=== {host} ===")
            if result["status"] == "online":
                print(result["output"])
            else:
                print(f"Status: {result['status']}")
                if "error" in result:
                    print(f"Error: {result['error']}")
            print()
    
    elif args.update:
        if not farm.config["hosts"]:
            print("No hosts configured.")
            return
        
        print("Updating all hosts...")
        results = farm.update_all_hosts()
        
        print("\nUpdate Results:")
        for host, status in results.items():
            print(f"{host}: {status}")
    
    elif args.fix_ssh:
        host = args.fix_ssh
        print(f"Attempting to fix SSH connection to {host}...")
        
        if farm.interactive_ssh_setup(host):
            print(f"✅ SSH connection to {host} should now work")
            
            # Test the connection
            if farm.test_ssh_connection(host):
                print(f"✅ SSH connection verified!")
                
                # Add to farm if not already there
                if host not in farm.config["hosts"]:
                    response = input(f"Add {host} to farm configuration? (y/n): ").lower().strip()
                    if response in ['y', 'yes']:
                        farm.config["hosts"].append(host)
                        farm.save_config(farm.config)
                        print(f"✓ Added {host} to farm configuration")
            else:
                print(f"❌ SSH connection still not working")
        else:
            print(f"❌ Could not fix SSH connection to {host}")
    
    elif args.test_host:
        host = args.test_host
        print(f"Testing connection to {host}...")
        
        # Test ping first
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '3', host], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Host {host} is reachable (ping successful)")
            else:
                print(f"❌ Host {host} is not reachable (ping failed)")
                return
        except Exception:
            print(f"❌ Cannot ping {host}")
            return
        
        # Test SSH
        if farm.test_ssh_connection(host):
            print(f"✅ SSH connection successful")
            
            # Get detailed info
            info = farm.get_host_info(host)
            print(f"\nHost Information:")
            for key, value in info.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
        else:
            print(f"❌ SSH connection failed")
            print(f"To fix this, run: ./farm_manager.py --fix-ssh {host}")
    
    else:
        print("PeakPause Farm Manager")
        print("Use --help for available commands")
        print(f"Current configuration: {len(farm.config['hosts'])} hosts")
        print(f"Local IP: {farm.local_ip}")
        
        if farm.config["hosts"]:
            print("\nConfigured hosts:")
            for host in farm.config["hosts"]:
                host_config = farm.get_host_ssh_config(host)
                host_ip = host_config["ip"]
                ssh_user = host_config["ssh_user"]
                host_name = host_config["name"]
                
                status = "✅ online" if farm.test_ssh_connection(host) else "❌ offline/error"
                print(f"  {host_ip} ({host_name}) - {ssh_user}@{host_ip}: {status}")
        
        print(f"\nUsage examples:")
        print(f"  Add host:           ./farm_manager.py --add-host 192.168.1.100")
        print(f"  Add with SSH user:  ./farm_manager.py --add-host 192.168.1.100:ubuntu")
        print(f"  Fix SSH:            ./farm_manager.py --fix-ssh 192.168.1.100")
        print(f"  Deploy:             ./farm_manager.py --deploy")

if __name__ == "__main__":
    main()
