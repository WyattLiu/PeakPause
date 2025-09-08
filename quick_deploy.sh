#!/bin/bash
"""
Quick deployment script for PeakPause farm
"""

set -e

echo "PeakPause Farm Quick Deploy"
echo "=========================="

# Check if we have the farm manager
if [ ! -f "farm_manager.py" ]; then
    echo "Error: farm_manager.py not found"
    exit 1
fi

# Make sure it's executable
chmod +x farm_manager.py

echo "Step 1: Discovering hosts on network..."
./farm_manager.py --discover

echo ""
echo "Step 2: Add hosts to farm (manual step)"
echo "Run: ./farm_manager.py --add-host <IP> for each host you want to add"
echo ""
echo "Step 3: Deploy to all hosts"
echo "Run: ./farm_manager.py --deploy"
echo ""
echo "Step 4: Check status"
echo "Run: ./farm_manager.py --status"
echo ""
echo "Current farm configuration:"
./farm_manager.py

echo ""
echo "Quick commands:"
echo "  Add host:    ./farm_manager.py --add-host <IP>"
echo "  Deploy all:  ./farm_manager.py --deploy"
echo "  Check status: ./farm_manager.py --status"
echo "  Update all:  ./farm_manager.py --update"
