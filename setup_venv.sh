#!/bin/bash
set -e

echo "🐍 Setting up PeakPause Python Environment"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📍 Found Python $PYTHON_VERSION"

# Check minimum Python version (3.7+)
if python3 -c 'import sys; exit(0 if sys.version_info >= (3,7) else 1)'; then
    echo "✅ Python version is compatible"
else
    echo "❌ Python 3.7+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Remove it? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf venv
    else
        echo "📦 Using existing virtual environment"
    fi
fi

if [ ! -d "venv" ]; then
    if python3 -m venv venv 2>/dev/null; then
        echo "✅ Created virtual environment"
    else
        echo "❌ Failed to create virtual environment"
        echo "💡 On Debian/Ubuntu, install: sudo apt install python3-venv"
        echo "💡 On RHEL/CentOS, install: sudo yum install python3-venv"
        echo "💡 Or use system Python: export USE_SYSTEM_PYTHON=1"
        
        if [ "$USE_SYSTEM_PYTHON" = "1" ]; then
            echo "📦 Using system Python (no virtual environment)"
            mkdir -p venv/bin
            ln -sf $(which python3) venv/bin/python3
            echo "✅ System Python symlink created"
        else
            exit 1
        fi
    fi
fi

# Activate virtual environment
echo "🚀 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/bin/python3" ]; then
    # System Python mode
    export PATH="$(pwd)/venv/bin:$PATH"
    echo "📦 Using system Python"
else
    echo "❌ Virtual environment setup failed"
    exit 1
fi

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found, installing basic dependencies..."
    pip install requests
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Generate configuration: python3 setup_config.py"
echo "3. Edit mining configuration: nano xmrig_config.json"
echo "4. Test the system: python3 peakpause.py --test"
echo ""
echo "💡 To deactivate virtual environment later: deactivate"
echo ""
echo "🔄 To run without activating manually, use:"
echo "   ./venv/bin/python3 peakpause.py --test"
