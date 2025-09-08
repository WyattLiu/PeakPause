#!/bin/bash
# PeakPause Installation Script

set -e

INSTALL_DIR="/root/mining"
USER="root"
USE_SYSTEM_PYTHON="true"
INSTALL_DEPS="false"

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
if [ "true" = "true" ]; then
    echo "Setting up cron job..."
    # Remove existing cron job
    crontab -l 2>/dev/null | grep -v "peakpause.py\|run_peakpause.sh" | crontab - || true
    
    # Add new cron job (every 5 minutes) - use absolute path
    (crontab -l 2>/dev/null; echo "*/5 * * * * cd $INSTALL_DIR && ./run_peakpause.sh >/dev/null 2>&1") | crontab -
fi

echo "Installation complete!"
echo "Location: $INSTALL_DIR"
echo "Test with: cd $INSTALL_DIR && ./run_peakpause.sh --test"
