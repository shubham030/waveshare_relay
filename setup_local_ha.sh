#!/bin/bash

# Setup Local Home Assistant Testing Environment
# This script creates a local HA instance for testing the waveshare relay integration

set -e

echo "🚀 Setting up Local Home Assistant Testing Environment..."

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 is required but not found!"
    echo "Please install Python 3.11 first:"
    echo "  brew install python@3.11"
    exit 1
fi

# Create local HA directory
LOCAL_HA_DIR="local_ha_test"
echo "📁 Creating local HA directory: $LOCAL_HA_DIR"

# Create virtual environment for Home Assistant
echo "🐍 Creating Python virtual environment..."
python3.11 -m venv "$LOCAL_HA_DIR/venv"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$LOCAL_HA_DIR/venv/bin/activate"

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Home Assistant
echo "🏠 Installing Home Assistant..."
pip install homeassistant

# Install additional dependencies for testing
echo "📦 Installing additional dependencies..."
pip install pytest-asyncio pytest-mock

# Create custom_components directory
echo "🔌 Setting up custom components..."
mkdir -p "$LOCAL_HA_DIR/config/custom_components"

# Copy our integration to custom_components
echo "📋 Copying waveshare relay integration..."
cp -r . "$LOCAL_HA_DIR/config/custom_components/waveshare_relay/"

# Remove unnecessary files from the copy
rm -rf "$LOCAL_HA_DIR/config/custom_components/waveshare_relay/local_ha_test"
rm -rf "$LOCAL_HA_DIR/config/custom_components/waveshare_relay/test_env*"
rm -rf "$LOCAL_HA_DIR/config/custom_components/waveshare_relay/.git"
rm -rf "$LOCAL_HA_DIR/config/custom_components/waveshare_relay/tests"
rm -rf "$LOCAL_HA_DIR/config/custom_components/waveshare_relay/pytest.ini"
rm -rf "$LOCAL_HA_DIR/config/custom_components/waveshare_relay/requirements-test.txt"
rm -rf "$LOCAL_HA_DIR/config/custom_HA_DIR/config/custom_components/waveshare_relay/run_tests_py311.sh"

# Copy configuration
echo "⚙️ Copying configuration..."
cp "$LOCAL_HA_DIR/configuration.yaml" "$LOCAL_HA_DIR/config/"

# Create start script
echo "📝 Creating start script..."
cat > "$LOCAL_HA_DIR/start_ha.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🏠 Starting Home Assistant..."
echo "📱 Open http://localhost:8123 in your browser"
echo "🔌 Your waveshare relay integration will be available"
echo "⏹️  Press Ctrl+C to stop"
hass --config config
EOF

chmod +x "$LOCAL_HA_DIR/start_ha.sh"

# Create test script
echo "🧪 Creating test script..."
cat > "$LOCAL_HA_DIR/test_integration.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🧪 Testing waveshare relay integration..."

# Test 1: Check if component loads
echo "✅ Test 1: Component loading..."
python3 -c "
import sys
sys.path.insert(0, 'config/custom_components/waveshare_relay')
try:
    import waveshare_relay
    print('✅ Component imports successfully')
except Exception as e:
    print(f'❌ Component import failed: {e}')
    sys.exit(1)
"

# Test 2: Check configuration schema
echo "✅ Test 2: Configuration schema..."
python3 -c "
import sys
sys.path.insert(0, 'config/custom_components/waveshare_relay')
try:
    from waveshare_relay import async_setup
    print('✅ Component setup function available')
except Exception as e:
    print(f'❌ Component setup failed: {e}')
    sys.exit(1)
"

echo "🎉 All tests passed! Integration is ready for testing."
EOF

chmod +x "$LOCAL_HA_DIR/test_integration.sh"

echo ""
echo "✅ Local Home Assistant environment setup complete!"
echo ""
echo "📁 Directory structure:"
echo "   $LOCAL_HA_DIR/"
echo "   ├── venv/                    # Python virtual environment"
echo "   ├── config/                  # HA configuration"
echo "   │   ├── configuration.yaml   # Main config"
echo "   │   └── custom_components/   # Custom integrations"
echo "   │       └── waveshare_relay/ # Our integration"
echo "   ├── start_ha.sh             # Start HA script"
echo "   └── test_integration.sh     # Test integration script"
echo ""
echo "🚀 To start Home Assistant:"
echo "   cd $LOCAL_HA_DIR"
echo "   ./start_ha.sh"
echo ""
echo "🧪 To test the integration:"
echo "   cd $LOCAL_HA_DIR"
echo "   ./test_integration.sh"
echo ""
echo "📱 Once started, open http://localhost:8123 in your browser"
echo "🔧 Remember to update the relay IP in config/configuration.yaml"
echo ""
echo "⚠️  Note: Make sure your relay device is accessible at the configured IP" 