# Legacy Perl Scripts Archive

This directory contains the original Perl implementation of PeakPause for historical reference and backup purposes.

## Original Files

- **`run.pl`** - Original continuous monitoring script
- **`cron_run.pl`** - Original cron-based execution script  
- **`gen_config_first_name.pl`** - Original configuration generator
- **`template_config.json`** - Original XMRig config template
- **`randomx_boost.sh`** - CPU optimization script (still usable)

## Migration Status

These files have been **replaced** by the modern Python implementation:

| Perl File | Python Replacement | Status |
|-----------|-------------------|---------|
| `run.pl` | `peakpause.py` | ✅ Replaced |
| `cron_run.pl` | `peakpause_cron.py` | ✅ Replaced |
| `gen_config_first_name.pl` | `setup_config.py` | ✅ Replaced |
| `template_config.json` | Auto-generated configs | ✅ Replaced |
| `randomx_boost.sh` | `legacy_perl/randomx_boost.sh` | 🔄 Still usable |

## Still Usable

### RandomX Boost Script
The `randomx_boost.sh` script is still useful for CPU optimization:

```bash
# Copy to main directory if needed
cp legacy_perl/randomx_boost.sh .
sudo ./randomx_boost.sh
```

This script optimizes CPU MSR registers for better RandomX performance on AMD and Intel processors.

## Rollback Instructions

If you need to rollback to the Perl version:

```bash
# 1. Copy files back to main directory
cp legacy_perl/*.pl .
cp legacy_perl/template_config.json .
cp legacy_perl/randomx_boost.sh .

# 2. Update cron job
sudo crontab -e
# Replace Python line with:
# */5 * * * * /path/to/PeakPause/cron_run.pl > /path/to/PeakPause/cron_run.log

# 3. Stop Python version (if running)
pkill -f peakpause.py
```

## Key Differences

### Rate Periods
- **Perl**: Simple on/off-peak (outdated rates)
- **Python**: 4 accurate ULO rate periods (2024-2025)

### Temperature Monitoring  
- **Perl**: Socket server only
- **Python**: Multiple sources (HomeKit, HTTP, system, socket)

### Configuration
- **Perl**: Hardcoded values in scripts
- **Python**: JSON configuration files

### Logging
- **Perl**: Basic print statements
- **Python**: Rotating logs with levels

## Historical Value

These scripts demonstrate:
- Original mining automation concepts
- Time-of-use electricity optimization
- Temperature-based safety controls
- Process management techniques

Keep for reference and potential feature inspiration!
