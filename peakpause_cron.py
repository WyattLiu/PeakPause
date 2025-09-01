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
# But only if we're not already being executed by the venv python
venv_python = script_dir / "venv" / "bin" / "python3"
current_python = Path(sys.executable).resolve()

# Only re-execute if we're not already using venv python and venv exists
if (not os.environ.get('VIRTUAL_ENV') and 
    venv_python.exists() and 
    current_python != venv_python.resolve() and
    '--no-venv' not in sys.argv):
    
    # Re-execute with virtual environment Python, preserving all arguments
    args = [str(venv_python)] + sys.argv + ['--no-venv']
    os.execv(str(venv_python), args)

# Remove the --no-venv flag if present
if '--no-venv' in sys.argv:
    sys.argv.remove('--no-venv')

try:
    from peakpause import PeakPause
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    print("Make sure dependencies are installed:", file=sys.stderr)
    print("  pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

def main():
    """Main entry point for cron"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PeakPause Cron Wrapper")
    parser.add_argument("--force", action="store_true", help="Force mining regardless of conditions")
    parser.add_argument("--no-venv", action="store_true", help="Skip virtual environment check")
    
    args = parser.parse_args()
    
    try:
        config_file = script_dir / "peakpause_config.json"
        if not config_file.exists():
            print(f"Config file not found: {config_file}", file=sys.stderr)
            sys.exit(1)
            
        controller = PeakPause(str(config_file))
        
        if args.force:
            print("🚨 CRON FORCE MODE: Forcing mining to start")
            controller.run_once(force_mining=True)
        else:
            controller.run_once()
            
    except Exception as e:
        print(f"Error in cron execution: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
