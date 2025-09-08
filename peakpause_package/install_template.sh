#!/bin/bash
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
    (crontab -l 2>/dev/null; echo "*/5 * * * * cd \"$INSTALL_DIR\" && ./run_peakpause.sh >/dev/null 2>&1") | crontab -
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
    echo "Test with: cd \"$INSTALL_DIR\" && ./venv/bin/python3 peakpause.py --test"
else
    echo "Test with: cd \"$INSTALL_DIR\" && python3 peakpause.py --test"
fi
echo "Or use: cd \"$INSTALL_DIR\" && ./run_peakpause.sh --test"
