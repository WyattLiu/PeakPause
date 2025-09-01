# PeakPause Migration Guide: Perl → Python

## Summary of Changes

### ✅ Updated ULO Rates (Major Improvement)
**Old Perl version** had hardcoded rates from ~2022:
```perl
my $off_peak_start = 19; # 7pm
my $off_peak_end = 7;    # 7am
```

**New Python version** uses current ULO rates (Nov 2024 - Oct 2025):
- **Ultra-low overnight**: 2.8¢/kWh (11 PM - 7 AM daily)
- **Weekend off-peak**: 7.6¢/kWh (Weekends 7 AM - 11 PM)  
- **Mid-peak**: 12.2¢/kWh (Weekdays 7 AM - 4 PM, 9 PM - 11 PM)
- **On-peak**: 28.4¢/kWh (Weekdays 4 PM - 9 PM)

### 🌡️ Modern Temperature Monitoring
**Old**: Single socket server at hardcoded IP
```perl
PeerAddr => '192.168.1.185',   
PeerPort => '48910',
```

**New**: Multiple modern sources
- **HomeKit/Home Assistant** (recommended)
- **HTTP APIs** for custom sensors
- **System thermal zones** (Linux)
- **Legacy socket server** (backward compatible)

### ⚙️ Smart Mining Logic
**Old**: Simple on/off based on time and temperature
```perl
if ($hour >= $off_peak_end and $hour < $off_peak_start) {
    $run = 0; # Don't run during day
}
```

**New**: Rate-aware temperature thresholds
- Different temperature limits for each rate period
- More restrictive during expensive peak hours
- Configurable mining policies

## Feature Comparison

| Feature | Perl Version | Python Version |
|---------|--------------|----------------|
| ULO Rates | ❌ Outdated (2022) | ✅ Current (2024-2025) |
| Temperature Sources | ❌ Socket only | ✅ Multiple (HomeKit, HTTP, System) |
| Configuration | ❌ Hardcoded | ✅ JSON config files |
| Error Handling | ⚠️ Basic | ✅ Comprehensive |
| Logging | ⚠️ Print statements | ✅ Rotating logs |
| Process Management | ⚠️ Basic fork/kill | ✅ Clean subprocess handling |
| Type Safety | ❌ None | ✅ Type hints |
| Documentation | ⚠️ README only | ✅ Comprehensive docs |

## Migration Steps

### 1. Backup Current Setup
```bash
cp -r PeakPause PeakPause_perl_backup
```

### 2. Install Python Dependencies
```bash
cd PeakPause
pip3 install -r requirements.txt
```

### 3. Generate New Configuration
```bash
python3 setup_config.py
```

### 4. Migrate Your Settings

**Copy wallet address from old config.json:**
```bash
# Find your wallet address
grep -A 5 '"user":' config.json

# Edit the new config
nano xmrig_config.json
# Replace WALLET_ADDRESS_PLACEHOLDER with your address
```

**Configure temperature monitoring:**
```bash
nano peakpause_config.json
# Set up your preferred temperature source
```

### 5. Update Cron Job
**Old cron entry:**
```bash
*/5 * * * * /home/wyatt/PeakPause/cron_run.pl > /home/wyatt/PeakPause/cron_run.log
```

**New cron entry:**
```bash
*/5 * * * * /usr/bin/python3 /home/wyatt/PeakPause/peakpause_cron.py >> /home/wyatt/PeakPause/cron.log 2>&1
```

### 6. Test New System
```bash
# Test configuration
python3 peakpause.py --test

# Manual run
python3 peakpause.py

# Check logs
tail -f peakpause.log
```

## Configuration Migration

### Temperature Settings
**Old Perl hardcoded values:**
```perl
my $on_peak_temp = 20;
my $mid_peak_temp = 25;
my $weekend_off_peak_temp = 26;
my $ulo = 28;
```

**New JSON configuration:**
```json
{
  "temperature": {
    "thresholds": {
      "ultra_low": 30.0,
      "weekend_off_peak": 28.0,
      "mid_peak": 25.0,
      "on_peak": 20.0
    }
  }
}
```

### Mining Pool Settings
**Copy from old config.json to new xmrig_config.json:**
- Pool URL
- Wallet address
- Worker name

## Rate Period Comparison

### Old System (Perl)
- **Off-peak**: 7pm - 7am + weekends
- **On-peak**: 7am - 7pm weekdays
- Only 2 rate periods

### New System (Python)
- **Ultra-low**: 11pm - 7am (2.8¢) - cheapest
- **Weekend off-peak**: Weekend days 7am - 11pm (7.6¢)
- **Mid-peak**: Weekday 7am - 4pm, 9pm - 11pm (12.2¢)
- **On-peak**: Weekday 4pm - 9pm (28.4¢) - most expensive
- 4 distinct rate periods with accurate pricing

## Benefits of Migration

### 💰 Cost Savings
- More accurate rate periods = better cost optimization
- Peak hour avoidance saves ~26¢/kWh vs mid-peak
- Ultra-low overnight period maximizes cheap electricity usage

### 🏠 Modern Smart Home Integration
- HomeKit/Home Assistant support
- IoT temperature sensors
- Better home automation integration

### 🛠️ Maintenance
- JSON configuration (no code changes needed)
- Better error handling and recovery
- Comprehensive logging for troubleshooting
- Type safety reduces bugs

### 📊 Monitoring
- Detailed logging with rotation
- Clear status reporting
- Easy testing and validation

## Backward Compatibility

The new system can still use your existing:
- ✅ XMRig binary
- ✅ Socket-based temperature server
- ✅ Cron scheduling approach
- ✅ Basic mining logic

But adds modern improvements on top!

## Rollback Plan

If needed, you can easily rollback:
```bash
# Stop new system
sudo crontab -e  # Remove Python cron entry

# Restore old system  
sudo crontab -e  # Add back Perl cron entry
*/5 * * * * /home/wyatt/PeakPause_perl_backup/cron_run.pl > /home/wyatt/PeakPause_perl_backup/cron_run.log
```

## Recommended Timeline

1. **Week 1**: Install and test Python version alongside Perl
2. **Week 2**: Run both systems in parallel, compare behavior
3. **Week 3**: Switch to Python version, monitor for issues
4. **Week 4**: Remove Perl version if everything works well

This ensures a smooth transition with minimal mining downtime!
