# 🔧 Cron Script Troubleshooting Guide

## ❌ **Problem: `./peakpause_cron.py` Gets Stuck**

### **Root Cause**
The original cron script was getting stuck in an infinite loop when trying to re-execute itself with the virtual environment Python.

### ✅ **Solutions Provided**

#### **Option 1: Fixed Smart Cron Script**
- **File**: `peakpause_cron.py` (now fixed)
- **Features**: Auto-detects virtual environment
- **Protection**: Prevents infinite loops with `--no-venv` flag
- **Usage**: `./peakpause_cron.py`

#### **Option 2: Simple Cron Script**  
- **File**: `peakpause_cron_simple.py`
- **Features**: Direct execution, no auto-switching
- **Usage**: `./venv/bin/python3 peakpause_cron_simple.py`

## 🔍 **Testing Cron Scripts**

### **Test the Fixed Smart Script**
```bash
# Should work without hanging
timeout 10 ./peakpause_cron.py
```

### **Test the Simple Script**
```bash
# Direct venv execution
./venv/bin/python3 peakpause_cron_simple.py
```

### **Expected Output**
Both should show:
```
2025-08-31 22:48:59,841 - INFO - PeakPause initialized
2025-08-31 22:48:59,841 - WARNING - Socket temperature failed: [Errno 111] Connection refused
2025-08-31 22:48:59,879 - INFO - Check: Mining approved: weekend_off_peak at 7.6¢/kWh (no temp sensor, weekend off-peak)
2025-08-31 22:48:59,879 - INFO - Starting mining
```

## ⚙️ **Cron Setup Options**

### **Updated `setup_cron.sh`**
Now offers two options:

```bash
./setup_cron.sh
📋 Choose cron script version:
1. Smart cron (auto-detects virtual environment)
2. Simple cron (requires explicit venv path)
Choose version (1-2, default: 1):
```

### **Option 1: Smart Cron**
```bash
# Crontab entry
*/5 * * * * /path/to/PeakPause/peakpause_cron.py >> /path/to/PeakPause/cron.log 2>&1
```

### **Option 2: Simple Cron** 
```bash
# Crontab entry  
*/5 * * * * /path/to/PeakPause/venv/bin/python3 /path/to/PeakPause/peakpause_cron_simple.py >> /path/to/PeakPause/cron.log 2>&1
```

## 🛠️ **Manual Cron Setup**

### **If Automatic Setup Fails**
```bash
# Edit crontab manually
sudo crontab -e

# Add one of these lines:
# Option 1 (Smart):
*/5 * * * * /full/path/to/PeakPause/peakpause_cron.py >> /full/path/to/PeakPause/cron.log 2>&1

# Option 2 (Simple):  
*/5 * * * * /full/path/to/PeakPause/venv/bin/python3 /full/path/to/PeakPause/peakpause_cron_simple.py >> /full/path/to/PeakPause/cron.log 2>&1
```

## 🔍 **Debugging Steps**

### **1. Check if Cron Job is Installed**
```bash
crontab -l | grep peakpause
```

### **2. Monitor Cron Activity**
```bash
# Watch cron log in real-time
tail -f cron.log

# Check recent cron logs
tail -20 cron.log
```

### **3. Check Cron Service**
```bash
# Debian/Ubuntu
systemctl status cron

# RHEL/CentOS
systemctl status crond

# Or generic
service cron status
```

### **4. Manual Test**
```bash
# Test the exact cron command manually
/path/to/PeakPause/peakpause_cron.py >> /path/to/PeakPause/cron.log 2>&1
```

### **5. Check Dependencies**
```bash
# Activate venv and test
source venv/bin/activate
python3 -c "from peakpause import PeakPause; print('OK')"
```

## 🚨 **Common Issues & Fixes**

### **Issue: ImportError in Cron**
```bash
# Fix: Use full venv path
*/5 * * * * /full/path/to/venv/bin/python3 /full/path/to/script.py
```

### **Issue: Permission Denied**
```bash
# Fix: Make scripts executable
chmod +x peakpause_cron.py
chmod +x peakpause_cron_simple.py
```

### **Issue: Config File Not Found**
```bash
# Fix: Check paths in cron environment
# Use absolute paths in crontab
```

### **Issue: Path Issues in Cron**
```bash
# Fix: Set PATH in crontab
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
*/5 * * * * /path/to/script.py
```

## ✅ **Verification**

### **Working Cron Job Should Show**
```bash
# In cron.log every 5 minutes:
2025-08-31 22:50:01,123 - INFO - PeakPause initialized
2025-08-31 22:50:01,124 - INFO - Check: Mining approved: ...
2025-08-31 22:50:01,125 - INFO - Mining continues (or Starting mining)
```

### **Successful Mining Process**
```bash
# Check if XMRig is running
ps aux | grep xmrig | grep -v grep
```

## 💡 **Recommendations**

1. **Use Option 2 (Simple Cron)** for production - more reliable
2. **Always use absolute paths** in crontab entries  
3. **Monitor cron.log** for the first few cycles
4. **Test manually first** before relying on cron
5. **Keep backup** of working crontab with `crontab -l > backup.cron`

## 🎯 **Quick Fix Command**

If you just want it working immediately:
```bash
# Remove any existing peakpause cron entries
crontab -l | grep -v peakpause | crontab -

# Add simple reliable version
(crontab -l 2>/dev/null; echo "*/5 * * * * $(pwd)/venv/bin/python3 $(pwd)/peakpause_cron_simple.py >> $(pwd)/cron.log 2>&1") | crontab -
```
