#!/bin/bash

# Switch to Mock Testing Configuration
# This script replaces the real hardware config with mock config

cd "$(dirname "$0")"

echo "🔄 Switching to Mock Testing Configuration..."

# Backup current configuration
if [ -f "config/configuration.yaml" ]; then
    cp "config/configuration.yaml" "config/configuration_real_backup.yaml"
    echo "✅ Backed up real hardware configuration"
fi

# Copy mock configuration
cp "configuration.yaml" "config/configuration.yaml"
echo "✅ Switched to mock configuration"

echo ""
echo "🔧 Configuration Updated:"
echo "   Host: 127.0.0.1 (localhost)"
echo "   Port: 502"
echo "   Device Address: 1"
echo "   Number of Relays: 32"
echo "   Name: Test Relay Hub"
echo ""

echo "📱 To start testing with mock server:"
echo "   1. Start mock server: ./start_mock_server.sh"
echo "   2. Start Home Assistant: ./start_ha.sh"
echo ""

echo "🔄 To switch back to real hardware testing:"
echo "   ./switch_to_real_hardware.sh" 