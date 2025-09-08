# PeakPause Farm Deployment Guide

## Quick Start

### 1. Initial Setup
```bash
# Make sure SSH key is set up for passwordless access
ssh-keygen -t rsa -b 4096 -C "peakpause-farm"
ssh-copy-id root@<target-host>

# Install required tools on control machine
apt-get install nmap rsync
```

### 2. Discover Hosts
```bash
# Auto-discover hosts on your network
./farm_manager.py --discover

# Or scan specific network
./farm_manager.py --discover --network 192.168.1.0/24
```

### 3. Add Hosts to Farm
```bash
# Add individual hosts
./farm_manager.py --add-host 192.168.1.100
./farm_manager.py --add-host 192.168.1.101
./farm_manager.py --add-host 192.168.1.102
```

### 4. Deploy to All Hosts
```bash
# Deploy PeakPause to all configured hosts
./farm_manager.py --deploy
```

### 5. Monitor Farm Status
```bash
# Check status of all hosts
./farm_manager.py --status
```

### 6. Update Farm
```bash
# Update all hosts with latest code
./farm_manager.py --update
```

## Configuration

Edit `farm_config.json` to customize:

- **ssh_user**: SSH username (default: root)
- **ssh_key**: Path to SSH private key
- **remote_path**: Installation directory on remote hosts (default: ~/mining)
- **mining_config**: Pool address and temperature server
- **deployment**: Control what gets installed

## Host-Specific Features

Each deployed host gets:
- Unique worker name based on hostname
- CPU allocation scaled to available cores
- Automatic cron job setup
- Virtual environment with dependencies
- Host-specific configuration

## Farm Management Commands

### Discover Network Hosts
```bash
./farm_manager.py --discover
```
Shows all hosts with SSH access, CPU/memory info

### Add Host to Farm
```bash
./farm_manager.py --add-host 192.168.1.50
```
Tests connection and adds to farm config

### Deploy Everything
```bash
./farm_manager.py --deploy
```
- Creates deployment package
- Copies all files via rsync
- Installs dependencies
- Sets up cron jobs
- Configures each host

### Check Farm Status
```bash
./farm_manager.py --status
```
Shows mining status from all hosts

### Update All Hosts
```bash
./farm_manager.py --update
```
Pushes latest code to all hosts

## Example Workflow

```bash
# 1. Discover hosts on network
./farm_manager.py --discover --network 192.168.1.0/24

# 2. Add the good ones
./farm_manager.py --add-host 192.168.1.100
./farm_manager.py --add-host 192.168.1.101
./farm_manager.py --add-host 192.168.1.102

# 3. Deploy to all
./farm_manager.py --deploy

# 4. Check everything is working
./farm_manager.py --status

# 5. Later, update all hosts
./farm_manager.py --update
```

## Troubleshooting

### SSH Connection Issues
- Ensure SSH key is properly installed: `ssh-copy-id root@host`
- Test manual connection: `ssh root@host`
- Check SSH key path in farm_config.json

### Deployment Failures
- Check network connectivity
- Verify remote host has Python 3
- Ensure sufficient disk space on remote hosts
- Check SSH user has appropriate permissions

### Mining Not Starting
- Check temperature server accessibility from remote hosts
- Verify pool address is reachable
- Check cron job setup: `ssh root@host crontab -l`
- Test manually: `ssh root@host "cd ~/mining && ./venv/bin/python3 peakpause.py --test"`

## File Structure After Deployment

On each remote host:
```
~/mining/
├── peakpause.py           # Main mining script
├── peakpause_config.json  # Host-specific config
├── requirements.txt       # Python dependencies
├── xmrig/                 # Mining binary
├── venv/                  # Python virtual environment
├── install.sh             # Installation script
└── farm_deploy.log        # Deployment log
```
