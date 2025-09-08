# PeakPause Mining Farm Management System

Complete automated deployment and management system for cryptocurrency mining across multiple hosts.

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Install required tools
apt-get update
apt-get install nmap rsync openssh-client

# Setup SSH keys for passwordless access
ssh-keygen -t rsa -b 4096 -C "peakpause-farm"

# Copy SSH key to target hosts
ssh-copy-id root@192.168.1.100
ssh-copy-id root@192.168.1.101
# ... repeat for all hosts
```

### 2. Farm Discovery & Setup
```bash
# Discover hosts on your network
./farm_manager.py --discover

# Add hosts to your farm
./farm_manager.py --add-host 192.168.1.100
./farm_manager.py --add-host 192.168.1.101
./farm_manager.py --add-host 192.168.1.102

# Deploy to all hosts
./farm_manager.py --deploy
```

### 3. Monitor Your Farm
```bash
# Real-time dashboard
./dashboard.py --interactive

# Static status report
./dashboard.py --report

# Command-line status
./farm_manager.py --status
```

## 📊 Farm Management Tools

### Core Tools

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `farm_manager.py` | Core deployment & management | Host discovery, deployment, status monitoring |
| `dashboard.py` | Real-time monitoring interface | Interactive dashboard, auto-refresh, emergency controls |
| `config_manager.py` | Configuration management | Bulk config updates, emergency stop/start |
| `quick_deploy.sh` | Simplified deployment | One-command setup guide |

### Farm Manager Commands

```bash
# Host Discovery
./farm_manager.py --discover                    # Auto-discover network hosts
./farm_manager.py --discover --network 10.0.0.0/24  # Scan specific network

# Host Management  
./farm_manager.py --add-host 192.168.1.100     # Add host to farm
./farm_manager.py --deploy                      # Deploy to all hosts
./farm_manager.py --status                      # Get status from all hosts
./farm_manager.py --update                      # Update all hosts
```

### Configuration Manager Commands

```bash
# Update mining settings across all hosts
./config_manager.py --pool 192.168.1.149:3333  # Change pool address
./config_manager.py --temp-server 192.168.1.149:3000  # Change temp server
./config_manager.py --max-temp 75               # Set temperature limit
./config_manager.py --max-threads 32            # Set thread limit

# Emergency controls
./config_manager.py --emergency-stop            # Stop all mining immediately
./config_manager.py --emergency-start           # Start all mining immediately

# Farm overview
./config_manager.py --summary                   # Show farm configuration
```

### Dashboard Commands

```bash
# Interactive real-time dashboard
./dashboard.py --interactive

# Static status report
./dashboard.py --report
```

## 🏗️ Architecture

### Deployment Package Contents

Each host receives:
```
/opt/peakpause/
├── peakpause.py              # Main mining controller
├── peakpause_config.json     # Host-specific configuration
├── requirements.txt          # Python dependencies
├── xmrig/                    # Mining binary directory
├── venv/                     # Isolated Python environment
├── install.sh                # Installation script
└── farm_deploy.log           # Deployment log
```

### Host-Specific Customization

Automatic per-host configuration:
- **Worker Names**: Based on hostname (e.g., `miner-001`, `server-rack-2`)
- **CPU Allocation**: Scaled to available cores (max 32 threads, VM-aware scaling)
- **Temperature Server**: Points to central monitoring server
- **Pool Configuration**: Shared across farm with unique worker IDs

### Network Architecture

```
Control Host (192.168.1.247)
├── Temperature Server (192.168.1.149:3000)
├── Mining Pool Proxy (192.168.1.149:3333)
└── Mining Hosts
    ├── 192.168.1.100 (miner-001)
    ├── 192.168.1.101 (miner-002)
    └── 192.168.1.102 (miner-003)
```

## ⚙️ Configuration

### Farm Configuration (`farm_config.json`)

```json
{
  "ssh_user": "root",
  "ssh_key": "~/.ssh/id_rsa",
  "remote_path": "/opt/peakpause",
  "hosts": ["192.168.1.100", "192.168.1.101"],
  "deployment": {
    "install_dependencies": true,
    "setup_cron": true,
    "start_mining": false
  },
  "mining_config": {
    "pool_address": "192.168.1.149:3333",
    "temperature_server": "192.168.1.149:3000"
  }
}
```

### Per-Host Mining Config

Automatically generated for each host:
```json
{
  "pool_config": {
    "address": "192.168.1.149:3333",
    "worker": "miner-001"
  },
  "cpu_allocation": {
    "max_threads": 32,
    "vm_active_threads": 16,
    "nice_priority": 19
  },
  "temperature": {
    "source": "http",
    "http_url": "http://192.168.1.149:3000/api/temperature/latest",
    "max_temp": 75
  }
}
```

## 🔧 Advanced Features

### Intelligent Resource Management
- **VM Detection**: Automatically reduces thread count when VMs are active
- **CPU Affinity**: Uses taskset for core isolation
- **Nice Priority**: Low-priority mining (nice 19)
- **Memory Monitoring**: Tracks system load

### Temperature Integration
- **Multiple Sensors**: Supports multiple temperature readings (uses minimum for safety)
- **HTTP API**: Integrates with Govee/other temperature APIs
- **Conservative Approach**: Always uses coolest reading for thermal safety

### Smart Deployment
- **Automatic Discovery**: Scans network for SSH-accessible hosts
- **Dependency Management**: Installs Python, creates virtual environments
- **Cron Integration**: Automatic scheduled mining
- **Rollback Capable**: Can update or rollback configurations

### Monitoring & Control
- **Real-time Dashboard**: Live status monitoring with auto-refresh
- **Emergency Controls**: Instant stop/start across entire farm
- **Bulk Configuration**: Update settings across all hosts simultaneously
- **Health Monitoring**: Track online status, mining status, temperatures

## 🛠️ Troubleshooting

### Common Issues

**SSH Connection Problems**
```bash
# Test SSH connection manually
ssh root@192.168.1.100

# Verify SSH key is installed
ssh-copy-id root@192.168.1.100

# Check SSH agent
ssh-add ~/.ssh/id_rsa
```

**Deployment Failures**
```bash
# Check host connectivity
./farm_manager.py --discover

# Test individual host
ssh root@192.168.1.100 "python3 --version"

# Check disk space
ssh root@192.168.1.100 "df -h"
```

**Mining Not Starting**
```bash
# Check remote status
ssh root@192.168.1.100 "cd /opt/peakpause && ./venv/bin/python3 peakpause.py --test"

# Check cron job
ssh root@192.168.1.100 "crontab -l"

# Check logs
ssh root@192.168.1.100 "cd /opt/peakpause && tail -f *.log"
```

### Log Locations

| Component | Log Location |
|-----------|--------------|
| Farm Manager | `./farm_deploy.log` |
| Remote Mining | `/opt/peakpause/peakpause.log` |
| Remote Cron | `/var/log/cron` |
| SSH Errors | `/var/log/auth.log` |

## 📈 Scaling

### Adding New Hosts
```bash
# Discovery and add
./farm_manager.py --discover
./farm_manager.py --add-host <NEW_IP>
./farm_manager.py --deploy
```

### Bulk Configuration Changes
```bash
# Update all hosts with new pool
./config_manager.py --pool new-pool.example.com:4444

# Update temperature limits
./config_manager.py --max-temp 70

# Update thread allocation
./config_manager.py --max-threads 24
```

### Farm Expansion

1. **Network Preparation**: Ensure SSH access to new hosts
2. **Discovery**: Use `--discover` to find new hosts
3. **Addition**: Add hosts with `--add-host`
4. **Deployment**: Deploy with `--deploy`
5. **Verification**: Monitor with dashboard

## 🔒 Security Considerations

- **SSH Key Management**: Use dedicated SSH keys for farm management
- **Network Isolation**: Consider VLANs for mining network
- **Firewall Rules**: Restrict SSH access to control host
- **User Permissions**: Use dedicated user accounts where possible
- **Regular Updates**: Keep SSH and system packages updated

## 📝 Example Workflows

### Daily Operations
```bash
# Morning status check
./dashboard.py --report

# Configuration update
./config_manager.py --max-temp 70

# Emergency stop (if needed)
./config_manager.py --emergency-stop
```

### New Farm Setup
```bash
# 1. Setup SSH keys
ssh-keygen -t rsa -b 4096
ssh-copy-id root@192.168.1.100
ssh-copy-id root@192.168.1.101

# 2. Discover and configure
./farm_manager.py --discover
./farm_manager.py --add-host 192.168.1.100
./farm_manager.py --add-host 192.168.1.101

# 3. Deploy
./farm_manager.py --deploy

# 4. Monitor
./dashboard.py --interactive
```

The PeakPause Farm Management System provides complete automation for deploying, monitoring, and managing cryptocurrency mining across multiple hosts with intelligent resource allocation and safety features.
