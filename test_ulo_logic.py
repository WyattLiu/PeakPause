#!/usr/bin/env python3
"""
Test ULO period logic and temperature handling
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the script directory to path
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

from peakpause import PeakPause, RatePeriod

def test_periods_without_temperature():
    """Test mining decisions during different periods without temperature sensor"""
    print("🧪 Testing ULO Period Logic (No Temperature Sensor)")
    print("=" * 60)
    
    controller = PeakPause()
    
    # Test different time periods
    test_times = [
        ("Monday 2:00 AM", datetime(2025, 9, 2, 2, 0)),    # Ultra-low overnight
        ("Monday 8:00 AM", datetime(2025, 9, 2, 8, 0)),    # Mid-peak weekday
        ("Monday 6:00 PM", datetime(2025, 9, 2, 18, 0)),   # On-peak weekday
        ("Monday 10:00 PM", datetime(2025, 9, 2, 22, 0)),  # Mid-peak evening
        ("Saturday 10:00 AM", datetime(2025, 9, 6, 10, 0)), # Weekend off-peak
        ("Saturday 11:30 PM", datetime(2025, 9, 6, 23, 30)), # Ultra-low weekend
    ]
    
    for time_desc, test_time in test_times:
        period = controller.scheduler.get_current_period(test_time)
        rate = controller.scheduler.get_rate(period)
        should_run, reason = controller.should_mine(test_time)
        
        status_icon = "✅" if should_run else "❌"
        print(f"{status_icon} {time_desc:20} | {period.value:18} | {rate:5.1f}¢/kWh | {reason}")

def test_ultra_low_preference():
    """Test that ultra-low periods are always preferred without temperature"""
    print("\n🌙 Ultra-Low Period Preference Test")
    print("=" * 50)
    
    controller = PeakPause()
    
    # Test ultra-low periods (11 PM - 7 AM)
    ultra_low_times = [
        datetime(2025, 9, 2, 23, 0),   # 11 PM
        datetime(2025, 9, 2, 1, 0),    # 1 AM  
        datetime(2025, 9, 2, 3, 30),   # 3:30 AM
        datetime(2025, 9, 2, 6, 45),   # 6:45 AM
    ]
    
    all_approved = True
    for test_time in ultra_low_times:
        should_run, reason = controller.should_mine(test_time)
        if not should_run:
            all_approved = False
        
        status_icon = "✅" if should_run else "❌"
        time_str = test_time.strftime("%I:%M %p")
        print(f"{status_icon} {time_str:8} | {reason}")
    
    if all_approved:
        print("\n🎉 All ultra-low periods approved for mining (as expected)")
    else:
        print("\n⚠️  Some ultra-low periods were not approved")

def test_weekend_preference():
    """Test weekend behavior without temperature (should be blocked now)"""
    print("\n🏖️  Weekend Behavior Test (No Temperature)")
    print("=" * 50)
    
    controller = PeakPause()
    
    # Test weekend day times (7 AM - 11 PM) - should now be blocked
    weekend_times = [
        datetime(2025, 9, 6, 8, 0),    # Saturday 8 AM
        datetime(2025, 9, 6, 12, 0),   # Saturday 12 PM
        datetime(2025, 9, 6, 16, 0),   # Saturday 4 PM
        datetime(2025, 9, 6, 20, 0),   # Saturday 8 PM
        datetime(2025, 9, 7, 10, 0),   # Sunday 10 AM
        datetime(2025, 9, 7, 15, 0),   # Sunday 3 PM
    ]
    
    all_blocked = True
    for test_time in weekend_times:
        should_run, reason = controller.should_mine(test_time)
        if should_run:
            all_blocked = False
        
        status_icon = "✅" if should_run else "❌"
        day_time = test_time.strftime("%A %I:%M %p")
        print(f"{status_icon} {day_time:18} | {reason}")
    
    if all_blocked:
        print("\n✅ All weekend periods correctly blocked without temperature (ULO only policy)")
    else:
        print("\n⚠️  Some weekend periods were not blocked")

def main():
    """Run all tests"""
    print("🔋 PeakPause ULO Logic Test Suite")
    print("Testing mining decisions without temperature sensor")
    print("")
    
    try:
        test_periods_without_temperature()
        test_ultra_low_preference()
        test_weekend_preference()
        
        print("\n" + "=" * 60)
        print("💡 Key Logic:")
        print("   ✅ Ultra-low (11 PM - 7 AM): Always mine at 2.8¢/kWh")
        print("   ❌ All other periods: Blocked without temperature sensor") 
        print("   🛡️  Conservative approach: Only ULO when no temp available")
        print("   🌡️  With temperature: Normal rate-based thresholds apply")
        print("\n🎯 This ensures safe operation and maximum savings during cheapest period!")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
