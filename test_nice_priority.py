#!/usr/bin/env python3
"""
Test script to verify XMRig starts with correct nice priority
"""

import subprocess
import time
import os
import signal
import sys

def test_nice_priority():
    """Test that XMRig process starts with nice priority 19"""
    
    print("🔧 Testing XMRig nice priority...")
    
    # Start XMRig with nice priority (will fail quickly without valid config, but that's OK)
    try:
        process = subprocess.Popen([
            'nice', '-n', '19', './xmrig', '--help'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Get the process PID while it's running
        pid = process.pid
        print(f"✅ XMRig started with PID: {pid}")
        
        # Check the nice value of the process
        result = subprocess.run(['ps', '-o', 'pid,ni,comm', '-p', str(pid)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                header = lines[0]
                process_info = lines[1]
                print(f"📊 Process info: {process_info}")
                
                # Extract nice value (second column after PID)
                parts = process_info.split()
                if len(parts) >= 2:
                    nice_value = parts[1]
                    print(f"🎯 Nice value: {nice_value}")
                    
                    if nice_value == '19':
                        print("✅ SUCCESS: XMRig running with nice priority 19 (lowest priority)")
                        return True
                    else:
                        print(f"❌ FAIL: Expected nice 19, got {nice_value}")
                        return False
        
        # Clean up
        process.terminate()
        process.wait()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return False

if __name__ == "__main__":
    success = test_nice_priority()
    print(f"\n{'🎉 Test PASSED' if success else '💥 Test FAILED'}")
    sys.exit(0 if success else 1)
