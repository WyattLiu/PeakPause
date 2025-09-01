#!/usr/bin/env python3
"""
Simple cron wrapper for PeakPause
Direct execution without virtual environment switching
"""

import sys
import os
from pathlib import Path

# Add the script directory to path
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

def main():
    """Main entry point for cron"""
    try:
        # Import here to catch import errors
        from peakpause import PeakPause
        
        config_file = script_dir / "peakpause_config.json"
        if not config_file.exists():
            print(f"Config file not found: {config_file}", file=sys.stderr)
            return 1
            
        controller = PeakPause(str(config_file))
        controller.run_once()
        return 0
        
    except ImportError as e:
        print(f"Import error: {e}", file=sys.stderr)
        print("Try running with venv: ./venv/bin/python3 peakpause_cron_simple.py", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error in cron execution: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
