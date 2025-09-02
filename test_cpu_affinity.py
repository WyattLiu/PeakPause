#!/usr/bin/env python3
"""
Test CPU affinity logic under different conditions
"""

import subprocess
import os
from unittest.mock import patch

# Import our mining controller
import sys
sys.path.append('/root/proj/PeakPause')
from peakpause import MiningController

def test_cpu_affinity_scenarios():
    """Test CPU affinity under different system conditions"""
    
    controller = MiningController({
        'executable': './xmrig', 
        'config_file': 'xmrig_config.json', 
        'log_file': 'xmrig.log'
    })
    
    print("🧪 Testing CPU Affinity Logic")
    print("=" * 50)
    
    # Test 1: Current real conditions
    print("📊 Current Real Conditions:")
    cores = controller.get_optimal_cpu_affinity()
    print(f"   Assigned cores: {cores}")
    
    print("\n🔬 Simulated Scenarios:")
    
    # Test 2: Simulate low load, no VMs
    print("💤 Scenario: Low load, no VMs detected")
    with patch('builtins.open') as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "0.5 0.3 0.2 1/800 12345"
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "root     12345  0.1  0.0  bash\nroot     12346  0.0  0.0  ssh"
            
            cores = controller.get_optimal_cpu_affinity()
            print(f"   Assigned cores: {cores}")
    
    # Test 3: Simulate high load, no VMs
    print("🔥 Scenario: High load, no VMs detected")
    with patch('builtins.open') as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "20.5 18.3 15.2 50/800 12345"
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "root     12345  0.1  0.0  bash\nroot     12346  0.0  0.0  ssh"
            
            cores = controller.get_optimal_cpu_affinity()
            print(f"   Assigned cores: {cores}")
    
    print("\n🎯 Summary:")
    print("   • VMs active: Conservative (cores 8-31)")
    print("   • VMs idle + low load: Aggressive (cores 1-31)")  
    print("   • High load: Conservative (cores 8-31)")
    print("   • Core 0: Always reserved for kernel/interrupts")

if __name__ == "__main__":
    test_cpu_affinity_scenarios()
