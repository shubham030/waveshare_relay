#!/bin/bash

# Official Home Assistant Development Environment Setup
# Following: https://developers.home-assistant.io/docs/development_environment/

set -e

echo "🚀 Setting up Official Home Assistant Development Environment..."
echo "📚 Following: https://developers.home-assistant.io/docs/development_environment/"
echo ""

# Check if Python 3.13 is available (HA requires 3.13+)
if ! command -v python3.13 &> /dev/null; then
    echo "❌ Python 3.13 is required for Home Assistant development!"
    echo "Please install Python 3.13 first:"
    echo "  brew install python@3.13"
    echo ""
    echo "Note: Python 3.11 is not compatible with HA development"
    exit 1
fi

echo "✅ Python 3.13 found: $(python3.13 --version)"

# Create HA dev directory
HA_DEV_DIR="ha_dev"
echo "📁 Creating Home Assistant development directory: $HA_DEV_DIR"

# Create virtual environment with Python 3.13
echo "🐍 Creating Python 3.13 virtual environment..."
python3.13 -m venv "$HA_DEV_DIR/venv"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$HA_DEV_DIR/venv/bin/activate"

# Verify Python version in venv
echo "🔍 Verifying Python version in virtual environment..."
python --version

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Home Assistant development dependencies
echo "📦 Installing Home Assistant development dependencies..."
echo "This will take several minutes as it installs HA core and all dependencies..."
pip install -e "git+https://github.com/home-assistant/core.git@dev#egg=homeassistant[dev]"

# Install additional development tools
echo "🔧 Installing additional development tools..."
pip install pytest pytest-asyncio pytest-mock pytest-cov
pip install black isort mypy pylint
pip install pre-commit

# Create HA configuration directory
echo "⚙️ Setting up HA configuration..."
mkdir -p "$HA_DEV_DIR/config"

# Create development configuration
cat > "$HA_DEV_DIR/config/configuration.yaml" << 'EOF'
# Home Assistant Development Configuration
# Following official development setup

default_config:

# Development logging
logger:
  default: info
  logs:
    custom_components.waveshare_relay: debug
    waveshare_relay: debug
    homeassistant.core: debug
    homeassistant.loader: debug

# Enable development features
frontend:
development:

# Enable API for testing
api:
websocket_api:

# Enable configuration UI
config:

# Custom components directory
custom_components: !include_dir_merge_named custom_components
EOF

# Create custom components directory
echo "🔌 Setting up custom components..."
mkdir -p "$HA_DEV_DIR/config/custom_components"

# Copy our integration
echo "📋 Copying waveshare relay integration..."
cp -r . "$HA_DEV_DIR/config/custom_components/waveshare_relay/"

# Remove unnecessary files from the copy
rm -rf "$HA_DEV_DIR/config/custom_components/waveshare_relay/ha_dev"
rm -rf "$HA_DEV_DIR/config/custom_components/waveshare_relay/local_ha_test"
rm -rf "$HA_DEV_DIR/config/custom_components/waveshare_relay/.git"
rm -rf "$HA_DEV_DIR/config/custom_components/waveshare_relay/tests"
rm -rf "$HA_DEV_DIR/config/custom_components/waveshare_relay/pytest.ini"
rm -rf "$HA_DEV_DIR/config/custom_components/waveshare_relay/requirements-test.txt"
rm -rf "$HA_DEV_DIR/config/custom_components/waveshare_relay/run_tests_py311.sh"

# Create development configuration for waveshare relay
cat > "$HA_DEV_DIR/config/custom_components/waveshare_relay/configuration.yaml" << 'EOF'
# Waveshare Relay Development Configuration
waveshare_relay:
  - name: "Common Room Relay Hub"
    host: "192.168.68.200"
    port: 502
    device_address: 2
    timeout: 5
    num_relays: 32
    restore_state: true
    lights:
      - name: "Common Room Light 1"
        address: 1
      - name: "Common Room Light 2"
        address: 2
      - name: "Common Room Light 3"
        address: 3
      - name: "Common Room Light 4"
        address: 4
    switches:
      - name: "Common Room Switch 1"
        address: 5
      - name: "Common Room Switch 2"
        address: 6
      - name: "Common Room Switch 3"
        address: 7
      - name: "Common Room Switch 4"
        address: 8
EOF

# Create start script following official HA dev process
echo "📝 Creating development start script..."
cat > "$HA_DEV_DIR/start_dev.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate

echo "🏠 Starting Home Assistant in Development Mode..."
echo "🔧 Following official HA development process"
echo "🐛 Debug logging enabled"
echo "📱 Open http://localhost:8123 in your browser"
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Start HA following official dev process: hass -c config
hass -c config
EOF

chmod +x "$HA_DEV_DIR/start_dev.sh"

# Create test script
echo "🧪 Creating test script..."
cat > "$HA_DEV_DIR/test_dev.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate

echo "🧪 Testing Home Assistant Development Environment..."
echo "📚 Following official HA development setup"
echo ""

# Test 1: Check HA installation
echo "✅ Test 1: Home Assistant installation..."
python3 -c "
try:
    import homeassistant
    print(f'✅ Home Assistant {homeassistant.__version__} installed')
    print(f'   Python version: {homeassistant.__version__}')
except Exception as e:
    print(f'❌ Home Assistant not available: {e}')
    exit(1)
"

# Test 2: Check our integration
echo "✅ Test 2: Custom integration..."
python3 -c "
import sys
sys.path.insert(0, 'config/custom_components')
try:
    import waveshare_relay
    print('✅ Waveshare relay integration available')
except Exception as e:
    print(f'❌ Integration not available: {e}')
    exit(1)
"

# Test 3: Check development tools
echo "✅ Test 3: Development tools..."
python3 -c "
try:
    import pytest
    print('✅ pytest available')
except ImportError:
    print('❌ pytest not available')

try:
    import black
    print('✅ black (code formatter) available')
except ImportError:
    print('❌ black not available')

try:
    import mypy
    print('✅ mypy (type checker) available')
except ImportError:
    print('❌ mypy not available')
"

echo "🎉 Development environment test complete!"
EOF

chmod +x "$HA_DEV_DIR/test_dev.sh"

# Create development workflow script
echo "📋 Creating development workflow script..."
cat > "$HA_DEV_DIR/dev_workflow.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate

echo "🔄 Home Assistant Development Workflow"
echo "====================================="
echo "📚 Following official HA development process"
echo ""
echo "1. 🧪 Run tests:"
echo "   ./test_dev.sh"
echo ""
echo "2. 🏠 Start HA in development mode:"
echo "   ./start_dev.sh"
echo ""
echo "3. 🔧 Code formatting:"
echo "   black config/custom_components/waveshare_relay/"
echo ""
echo "4. 🔍 Type checking:"
echo "   mypy config/custom_components/waveshare_relay/"
echo ""
echo "5. 🧹 Linting:"
echo "   pylint config/custom_components/waveshare_relay/"
echo ""
echo "6. 🧪 Run pytest:"
echo "   cd .. && python -m pytest tests/"
echo ""
echo "7. 📱 Access Home Assistant:"
echo "   http://localhost:8123"
echo ""
echo "8. 🔌 Test waveshare relay integration:"
echo "   - Check entities are created"
echo "   - Test relay control"
echo "   - Verify state persistence"
echo "   - Check logs for debugging"
echo ""
echo "📚 Official Documentation:"
echo "   https://developers.home-assistant.io/docs/development_environment/"
EOF

chmod +x "$HA_DEV_DIR/dev_workflow.sh"

# Create README for the dev environment
echo "📖 Creating development environment README..."
cat > "$HA_DEV_DIR/README.md" << 'EOF'
# Home Assistant Development Environment

This directory contains a proper Home Assistant development environment following the [official development setup guide](https://developers.home-assistant.io/docs/development_environment/).

## 🏗️ Setup

This environment has been set up following the official Home Assistant development process:
- Python 3.13 virtual environment (required for HA dev)
- Home Assistant core installed from source
- Development dependencies and tools
- Custom components support

## 📁 Directory Structure

```
ha_dev/
├── venv/                           # Python 3.13 virtual environment
├── config/                         # HA configuration
│   ├── configuration.yaml          # Main dev config
│   └── custom_components/          # Custom integrations
│       └── waveshare_relay/        # Our integration
├── start_dev.sh                    # Start HA in dev mode
├── test_dev.sh                     # Test dev environment
├── dev_workflow.sh                 # Development workflow guide
└── README.md                       # This file
```

## 🚀 Development Workflow

### 1. Activate Environment
```bash
cd ha_dev
source venv/bin/activate
```

### 2. Test Environment
```bash
./test_dev.sh
```

### 3. Start Home Assistant
```bash
./start_dev.sh
```

### 4. Access Home Assistant
Open http://localhost:8123 in your browser

## 🔧 Key Features

- ✅ **Official HA Development Setup** - Following official documentation
- ✅ **Python 3.13** - Required for Home Assistant development
- ✅ **Source Installation** - HA core installed from git repository
- ✅ **Development Mode** - Full development features enabled
- ✅ **Debug Logging** - Comprehensive logging for development
- ✅ **Custom Components** - Support for our waveshare relay integration

## 📚 Official Documentation

- [Development Environment Setup](https://developers.home-assistant.io/docs/development_environment/)
- [Building Integrations](https://developers.home-assistant.io/docs/building_integration_index/)
- [Development Workflow](https://developers.home-assistant.io/docs/development_workflow/)

## 🚨 Important Notes

- **Python Version**: Requires Python 3.13+ (not 3.11)
- **Source Installation**: HA is installed from source, not from PyPI
- **Development Mode**: Full development features are enabled
- **Custom Components**: Our integration is properly integrated

## 🔄 Next Steps

1. Test the development environment
2. Start Home Assistant in development mode
3. Test the waveshare relay integration
4. Develop and debug as needed
5. Follow official HA development practices
EOF

echo ""
echo "✅ Official Home Assistant Development Environment setup complete!"
echo ""
echo "📁 Directory structure:"
echo "   $HA_DEV_DIR/"
echo "   ├── venv/                           # Python 3.13 virtual environment"
echo "   ├── config/                         # HA configuration"
echo "   │   ├── configuration.yaml          # Main dev config"
echo "   │   └── custom_components/          # Custom integrations"
echo "   │       └── waveshare_relay/        # Our integration"
echo "   ├── start_dev.sh                    # Start HA in dev mode"
echo "   ├── test_dev.sh                     # Test dev environment"
echo "   ├── dev_workflow.sh                 # Development workflow guide"
echo "   └── README.md                       # Development documentation"
echo ""
echo "🚀 To start development:"
echo "   cd $HA_DEV_DIR"
echo "   ./test_dev.sh          # Test the environment"
echo "   ./start_dev.sh         # Start HA in dev mode"
echo "   ./dev_workflow.sh      # Show development workflow"
echo ""
echo "🔧 Key differences from basic setup:"
echo "   ✅ Python 3.13 (required for HA dev)"
echo "   ✅ HA core installed from source"
echo "   ✅ Following official development process"
echo "   ✅ Full development features enabled"
echo ""
echo "📱 Once started, open http://localhost:8123 in your browser"
echo "🔌 Your waveshare relay integration will be available for testing"
echo ""
echo "⚠️  Note: Make sure your relay device is accessible at 192.168.68.200:502"
echo ""
echo "📚 Official Documentation:"
echo "   https://developers.home-assistant.io/docs/development_environment/" 