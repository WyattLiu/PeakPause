#!/usr/bin/env python3
"""
Test dynamic thread allocation under different VM scenarios
"""

import subprocess
from unittest.mock import patch

# Import our mining controller
import sys
sys.path.append('/root/proj/PeakPause')
from peakpause import MiningController

def test_thread_allocation():
    """Test thread allocation under different system conditions"""
    
    controller = MiningController({
        'executable': './xmrig', 
        'config_file': 'xmrig_config.json', 
        'log_file': 'xmrig.log'
    })
    
    print("🧮 Testing Dynamic Thread Allocation")
    print("=" * 50)
    
    # Test 1: Current real conditions
    print("📊 Current Real Conditions:")
    cores, threads = controller.get_optimal_cpu_settings()
    print(f"   Cores: {cores}")
    print(f"   Threads: {threads}")
    
    print("\n🔬 Simulated Scenarios:")
    
    # Test 2: Simulate low load, no VMs (maximum performance)
    print("🚀 Scenario: VMs idle, low system load")
    with patch('builtins.open') as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "0.5 0.3 0.2 1/800 12345"
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "root     12345  0.1  0.0  bash\nroot     12346  0.0  0.0  ssh"
            
            cores, threads = controller.get_optimal_cpu_settings()
            print(f"   Cores: {cores}")
            print(f"   Threads: {threads}")
    
    # Test 3: Simulate high load (conservative)
    print("🔥 Scenario: High system load (regardless of VMs)")
    with patch('builtins.open') as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "20.5 18.3 15.2 50/800 12345"
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "root     12345  0.1  0.0  bash\nroot     12346  0.0  0.0  ssh"
            
            cores, threads = controller.get_optimal_cpu_settings()
            print(f"   Cores: {cores}")
            print(f"   Threads: {threads}")
    
    print("\n🎯 Thread Allocation Strategy:")
    print("   • VMs active or high load: 16 threads (conservative)")
    print("   • VMs idle + low load: 32 threads (maximum hashrate)")  
    print("   • Always avoid core 0 for kernel/interrupts")
    print("   • Cores 0-7 reserved when VMs detected")

if __name__ == "__main__":
    test_thread_allocation()
