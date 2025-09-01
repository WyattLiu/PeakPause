#!/usr/bin/env python3
"""
Cron wrapper for PeakPause
Lightweight script for cron execution with virtual environment support
"""

import sys
import os
from pathlib import Path

# Add the script directory to path
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

# Check if we're in virtual environment, if not try to use it
venv_python = script_dir / "venv" / "bin" / "python3"
if not os.environ.get('VIRTUAL_ENV') and venv_python.exists():
    # Re-execute with virtual environment Python
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)

from peakpause import PeakPause

def main():
    """Main entry point for cron"""
    try:
        config_file = script_dir / "peakpause_config.json"
        controller = PeakPause(str(config_file))
        controller.run_once()
    except Exception as e:
        print(f"Error in cron execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
