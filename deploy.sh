#!/bin/bash
# Multi-machine deployment script for PeakPause
# This script can be run on multiple machines to deploy PeakPause consistently

set -e

REPO_URL="https://github.com/WyattLiu/PeakPause.git"
INSTALL_DIR="$HOME/PeakPause"

echo "🚀 PeakPause Multi-Machine Deployment"
echo "===================================="

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "📂 PeakPause directory exists, updating..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "📥 Cloning PeakPause repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Run quick setup
echo ""
echo "🔧 Running automated setup..."
./quick_setup.sh

# Display machine-specific information
echo ""
echo "🖥️  Machine Information:"
echo "   Hostname: $(hostname)"
echo "   CPU Info: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)"
echo "   Core Count: $(nproc)"
echo "   IP Address: $(hostname -I | awk '{print $1}')"
echo ""

# Check if XMRig binary exists
if [ ! -f "xmrig" ]; then
    echo "⚠️  XMRig binary not found!"
    echo "📥 Download options:"
    echo "   1. Download from: https://github.com/xmrig/xmrig/releases"
    echo "   2. Or copy from another machine: scp user@other-machine:$INSTALL_DIR/xmrig ."
    echo ""
fi

# Show the generated worker name
HOSTNAME=$(hostname)
CPU_MODEL=$(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | sed 's/.*:\s*//;s/\s*(CPU|Processor|\(.*\)|@.*|with.*)//gI;s/\s\+/_/g;s/[^\w\-]//g' | cut -c1-20)
CPU_COUNT=$(nproc)
WORKER_NAME="${HOSTNAME}_${CPU_MODEL}_${CPU_COUNT}c"

echo "🏷️  Generated worker name: $WORKER_NAME"
echo ""

# Setup instructions
echo "📋 Final steps:"
echo "1. Copy XMRig binary if needed"
echo "2. Test the system: cd $INSTALL_DIR && python3 peakpause.py --test"
echo "3. Setup cron job: cd $INSTALL_DIR && ./setup_cron.sh"
echo ""
echo "🔧 Optional: Enable CPU optimization"
echo "   sudo $INSTALL_DIR/legacy_perl/randomx_boost.sh"
echo ""

# Ask about cron setup
read -p "Do you want to setup the cron job now? (Y/n): " setup_cron
if [[ ! "$setup_cron" =~ ^[Nn]$ ]]; then
    echo "⏰ Setting up cron job..."
    if ./setup_cron.sh; then
        echo "✅ Cron job configured successfully"
    else
        echo "⚠️  Cron setup had issues"
    fi
fi

echo ""
echo "✅ Deployment complete for $(hostname)!"

# Create a simple deployment verification script
cat > deploy_verify.sh << 'EOF'
#!/bin/bash
# Verify PeakPause deployment

echo "🔍 PeakPause Deployment Verification"
echo "==================================="

# Check Python virtual environment
if [ -d "venv" ]; then
    echo "✅ Virtual environment: OK"
else
    echo "❌ Virtual environment: Missing"
fi

# Check configuration files
if [ -f "peakpause_config.json" ] && [ -f "xmrig_config.json" ]; then
    echo "✅ Configuration files: OK"
else
    echo "❌ Configuration files: Missing"
fi

# Check XMRig binary
if [ -f "xmrig" ] && [ -x "xmrig" ]; then
    echo "✅ XMRig binary: OK"
else
    echo "❌ XMRig binary: Missing or not executable"
fi

# Test the system
echo ""
echo "🧪 System Test:"
if source venv/bin/activate && python3 peakpause.py --test; then
    echo "✅ System test: PASSED"
else
    echo "❌ System test: FAILED"
fi

# Check cron job
if crontab -l 2>/dev/null | grep -q "peakpause_cron.py"; then
    echo "✅ Cron job: Configured"
else
    echo "⚠️  Cron job: Not configured"
fi

echo ""
echo "📊 Current worker name:"
HOSTNAME=$(hostname)
CPU_MODEL=$(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | sed 's/.*:\s*//;s/\s*(CPU|Processor|\(.*\)|@.*|with.*)//gI;s/\s\+/_/g;s/[^\w\-]//g' | cut -c1-20)
CPU_COUNT=$(nproc)
echo "   ${HOSTNAME}_${CPU_MODEL}_${CPU_COUNT}c"
EOF

chmod +x deploy_verify.sh
echo "💡 Created deploy_verify.sh - run this to check deployment status"
