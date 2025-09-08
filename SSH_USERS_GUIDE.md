# Multi-User SSH Configuration Guide

## Overview

The PeakPause Farm Manager now supports different SSH users for different hosts, making it flexible for environments with mixed operating systems and user configurations.

## Configuration Formats

### Global Default Settings
```json
{
  "ssh_user": "root",
  "ssh_key": "~/.ssh/id_rsa",
  "hosts": [...]
}
```

### Per-Host Configuration
```json
{
  "hosts": [
    {
      "ip": "192.168.1.100",
      "ssh_user": "root",
      "ssh_key": "~/.ssh/id_rsa",
      "name": "server-01"
    },
    {
      "ip": "192.168.1.101", 
      "ssh_user": "ubuntu",
      "ssh_key": "~/.ssh/ubuntu_key",
      "name": "ubuntu-miner"
    },
    {
      "ip": "192.168.1.102",
      "ssh_user": "admin",
      "ssh_key": "~/.ssh/id_rsa",
      "name": "nas-server"
    }
  ]
}
```

## Adding Hosts with Different Users

### Method 1: Specify User in Command
```bash
# Add host with specific SSH user
./farm_manager.py --add-host 192.168.1.100:ubuntu
./farm_manager.py --add-host 192.168.1.101:admin
./farm_manager.py --add-host 192.168.1.102:root
```

### Method 2: Use SSH User Flag
```bash
# Override default SSH user for operation
./farm_manager.py --add-host 192.168.1.100 --ssh-user ubuntu
./farm_manager.py --add-host 192.168.1.101 --ssh-user admin
```

### Method 3: Interactive Setup
```bash
# Let the system prompt for SSH user during setup
./farm_manager.py --add-host 192.168.1.100
# System will ask for SSH user if connection fails
```

## Common SSH Users by OS

| Operating System | Common SSH Users |
|------------------|------------------|
| Ubuntu/Debian | `ubuntu`, `debian`, `root` |
| CentOS/RHEL | `centos`, `ec2-user`, `root` |
| Rocky Linux | `rocky`, `root` |
| Alpine Linux | `alpine`, `root` |
| TrueNAS | `root`, `truenas` |
| Proxmox | `root` |
| OpenWrt | `root` |

## SSH Key Management

### Single Key for All Hosts
```json
{
  "ssh_user": "root",
  "ssh_key": "~/.ssh/id_rsa",
  "hosts": [
    {"ip": "192.168.1.100", "ssh_user": "root"},
    {"ip": "192.168.1.101", "ssh_user": "ubuntu"},
    {"ip": "192.168.1.102", "ssh_user": "admin"}
  ]
}
```

### Different Keys per Host
```json
{
  "hosts": [
    {
      "ip": "192.168.1.100",
      "ssh_user": "root", 
      "ssh_key": "~/.ssh/server_key"
    },
    {
      "ip": "192.168.1.101",
      "ssh_user": "ubuntu",
      "ssh_key": "~/.ssh/ubuntu_key"
    }
  ]
}
```

## Troubleshooting SSH Issues

### Test Host Connection
```bash
# Test specific host with detailed info
./farm_manager.py --test-host 192.168.1.100

# Fix SSH issues interactively
./farm_manager.py --fix-ssh 192.168.1.100
```

### Manual SSH Key Setup
```bash
# Generate key if needed
ssh-keygen -t rsa -b 4096 -f ~/.ssh/farm_key

# Copy to different users
ssh-copy-id root@192.168.1.100
ssh-copy-id ubuntu@192.168.1.101
ssh-copy-id admin@192.168.1.102
```

### Common Issues and Solutions

**Permission Denied**
- Wrong SSH user
- SSH key not installed
- SSH service not running

```bash
# Fix with interactive setup
./farm_manager.py --fix-ssh 192.168.1.100
```

**Connection Refused**
- SSH service not running
- Firewall blocking port 22
- Wrong IP address

```bash
# Test connectivity
ping 192.168.1.100
nmap -p 22 192.168.1.100
```

**Host Key Verification Failed**
- Host key changed
- First connection

```bash
# Remove old host key
ssh-keygen -R 192.168.1.100

# Or disable strict checking (less secure)
ssh -o StrictHostKeyChecking=no user@host
```

## Example Workflows

### Mixed Environment Setup
```bash
# Ubuntu server
./farm_manager.py --add-host 192.168.1.100:ubuntu

# CentOS server  
./farm_manager.py --add-host 192.168.1.101:centos

# TrueNAS server
./farm_manager.py --add-host 192.168.1.102:root

# Deploy to all
./farm_manager.py --deploy
```

### Bulk Host Addition
```bash
# Add multiple hosts with different users
./farm_manager.py --add-host 192.168.1.10:root
./farm_manager.py --add-host 192.168.1.11:ubuntu  
./farm_manager.py --add-host 192.168.1.12:admin
./farm_manager.py --add-host 192.168.1.13:pi

# Check all connections
./farm_manager.py
```

### SSH Key Distribution
```bash
# Setup SSH keys for all hosts
for host in 192.168.1.{10..20}; do
    ./farm_manager.py --fix-ssh $host
done
```

## Security Best Practices

1. **Use Dedicated SSH Keys**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/peakpause_farm
   ```

2. **Limit SSH Access**
   - Use SSH config to restrict commands
   - Consider SSH certificates for large deployments

3. **User Permissions**
   - Create dedicated mining user where possible
   - Use sudo for privileged operations only

4. **Network Security**
   - Use VPN or private networks
   - Firewall SSH access to control host only

## Configuration Migration

### From Old Format (List of IPs)
```json
{
  "hosts": ["192.168.1.100", "192.168.1.101"]
}
```

### To New Format (Host Objects)
```json
{
  "hosts": [
    {
      "ip": "192.168.1.100",
      "ssh_user": "root", 
      "ssh_key": "~/.ssh/id_rsa",
      "name": "miner-01"
    },
    {
      "ip": "192.168.1.101",
      "ssh_user": "ubuntu",
      "ssh_key": "~/.ssh/id_rsa", 
      "name": "miner-02"
    }
  ]
}
```

The system automatically handles both formats for backward compatibility.
