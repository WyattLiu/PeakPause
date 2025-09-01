#!/bin/bash
# PeakPause Quick Setup Script
# This script sets up the complete PeakPause environment

set -e

echo "🚀 PeakPause Quick Setup"
echo "======================="

# Check if we're in the right directory
if [ ! -f "peakpause.py" ]; then
    echo "❌ Please run this script from the PeakPause directory"
    exit 1
fi

# 1. Setup virtual environment
echo ""
echo "📦 Step 1: Setting up Python virtual environment"
./setup_venv.sh

# 2. Generate configuration files
echo ""
echo "⚙️  Step 2: Generating configuration files"
source venv/bin/activate
python3 setup_config.py

# 3. Check for XMRig binary
echo ""
echo "🔍 Step 3: Checking for XMRig binary"
if [ -f "xmrig" ]; then
    echo "✅ XMRig binary found"
    chmod +x xmrig
else
    echo "⚠️  XMRig binary not found"
    echo "📥 Please download XMRig from: https://github.com/xmrig/xmrig/releases"
    echo "   Place the binary as 'xmrig' in this directory"
fi

# 4. Test the system
echo ""
echo "🧪 Step 4: Testing the system"
if python3 peakpause.py --test; then
    echo "✅ System test passed"
else
    echo "⚠️  System test had warnings (check temperature monitoring)"
fi

# 5. Setup instructions
echo ""
echo "📋 Step 5: Configuration summary"
echo ""
echo "✅ Pre-configured settings:"
echo "   💰 Wallet: 3EdDNCU8nDx2bidh1DjJ8fjqgQCpg3WrDZ (NiceHash BTC)"
echo "   🏊 Pool: 192.168.1.149:3333 (local mining proxy)"
echo "   🌡️  Temperature: Socket server at 192.168.1.185:48910"
echo ""
echo "🔧 Optional customizations:"
echo "   nano xmrig_config.json     # Change wallet/pool if needed"
echo "   nano peakpause_config.json # Configure temperature source"
echo ""
echo "🏷️  Worker naming: hostname_cpumodel_corecount"
echo "   (helps identify machines in pool dashboard)"
# 6. Setup cron job automatically
echo ""
echo "⏰ Step 6: Setting up cron job"
read -p "Do you want to automatically setup the cron job? (Y/n): " setup_cron
if [[ "$setup_cron" =~ ^[Nn]$ ]]; then
    echo "⏭️  Skipping automatic cron setup"
    echo "📅 Manual cron setup:"
    echo "   sudo crontab -e"
    echo "   Add this line:"
    echo "   */5 * * * * $(pwd)/peakpause_cron.py >> $(pwd)/cron.log 2>&1"
else
    echo "🔧 Setting up cron job automatically..."
    if ./setup_cron.sh; then
        echo "✅ Cron job setup successful"
    else
        echo "⚠️  Cron job setup had issues, check output above"
    fi
fi
echo ""
echo "🔬 Helper tools:"
echo "   ./homekit_helper.py  - HomeKit/Home Assistant setup helper"
echo ""
echo "✅ Setup complete! Edit configs and add cron job to finish."

deactivate 2>/dev/null || true
