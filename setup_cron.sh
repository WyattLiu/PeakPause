#!/bin/bash
# Automatic cron job setup for PeakPause
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_SCRIPT="$SCRIPT_DIR/peakpause_cron.py"
CRON_LOG="$SCRIPT_DIR/cron.log"

echo "⏰ Setting up PeakPause cron job automatically"
echo "============================================="

# Check if script exists
if [ ! -f "$CRON_SCRIPT" ]; then
    echo "❌ peakpause_cron.py not found in $SCRIPT_DIR"
    exit 1
fi

# Make sure cron script is executable
chmod +x "$CRON_SCRIPT"

# Check if crontab exists and backup
BACKUP_FILE="$SCRIPT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S)"
if crontab -l >/dev/null 2>&1; then
    echo "💾 Backing up existing crontab to $BACKUP_FILE"
    crontab -l > "$BACKUP_FILE"
    EXISTING_CRON=$(crontab -l)
else
    echo "📝 No existing crontab found"
    EXISTING_CRON=""
fi

# Check if PeakPause cron job already exists
if echo "$EXISTING_CRON" | grep -q "peakpause_cron.py"; then
    echo "⚠️  PeakPause cron job already exists!"
    echo "Current entry:"
    echo "$EXISTING_CRON" | grep "peakpause_cron.py"
    echo ""
    echo "Options:"
    echo "1. Replace existing entry"
    echo "2. Keep existing entry"
    echo "3. Exit without changes"
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo "🔄 Replacing existing PeakPause cron job..."
            # Remove existing PeakPause entries
            NEW_CRON=$(echo "$EXISTING_CRON" | grep -v "peakpause_cron.py")
            ;;
        2)
            echo "✅ Keeping existing cron job"
            exit 0
            ;;
        3)
            echo "🚫 Exiting without changes"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice"
            exit 1
            ;;
    esac
else
    NEW_CRON="$EXISTING_CRON"
fi

# Add PeakPause cron job (runs every 5 minutes)
CRON_ENTRY="*/5 * * * * $CRON_SCRIPT >> $CRON_LOG 2>&1"

if [ -n "$NEW_CRON" ]; then
    # Add to existing crontab
    echo -e "$NEW_CRON\n$CRON_ENTRY" | crontab -
else
    # Create new crontab
    echo "$CRON_ENTRY" | crontab -
fi

echo "✅ PeakPause cron job installed successfully!"
echo ""
echo "📋 Cron job details:"
echo "   Schedule: Every 5 minutes"
echo "   Script: $CRON_SCRIPT"
echo "   Log file: $CRON_LOG"
echo ""
echo "🔍 Verify installation:"
echo "   crontab -l | grep peakpause"
echo ""
echo "📊 Monitor activity:"
echo "   tail -f $CRON_LOG"
echo ""

# Verify the installation
echo "🧪 Testing cron job manually..."
if "$CRON_SCRIPT" >> "$CRON_LOG" 2>&1; then
    echo "✅ Manual test successful"
else
    echo "⚠️  Manual test had warnings (check $CRON_LOG)"
fi

# Show current crontab
echo ""
echo "📅 Current crontab:"
crontab -l | grep -E "(peakpause|#|^$)" || crontab -l

# Check cron service status
echo ""
echo "🔍 Checking cron service status..."
if systemctl is-active --quiet cron 2>/dev/null; then
    echo "✅ Cron service is running"
elif systemctl is-active --quiet crond 2>/dev/null; then
    echo "✅ Crond service is running"
elif service cron status >/dev/null 2>&1; then
    echo "✅ Cron service is running (SysV)"
else
    echo "⚠️  Cron service status unknown - please verify manually:"
    echo "   systemctl status cron"
    echo "   or: service cron status"
fi

echo ""
echo "🎉 Cron setup complete!"
echo "💡 The system will now check every 5 minutes and start/stop mining based on:"
echo "   - ULO electricity rates (2.8¢ to 28.4¢/kWh)"
echo "   - Temperature thresholds"
echo "   - Mining profitability policies"
