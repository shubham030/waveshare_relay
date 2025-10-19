#!/bin/bash

# Switch to Real Hardware Testing Configuration
# This script replaces the mock configuration with real hardware config

cd "$(dirname "$0")"

echo "🔄 Switching to Real Hardware Testing Configuration..."

# Backup current configuration
if [ -f "config/configuration.yaml" ]; then
    cp "config/configuration.yaml" "config/configuration_mock_backup.yaml"
    echo "✅ Backed up mock configuration"
fi

# Copy real hardware configuration
cp "configuration_real_hardware.yaml" "config/configuration.yaml"
echo "✅ Switched to real hardware configuration"

echo ""
echo "🔧 Configuration Updated:"
echo "   Host: 192.168.68.200"
echo "   Port: 502"
echo "   Device Address: 2"
echo "   Number of Relays: 32"
echo "   Name: Common Room Relay Hub"
echo ""

echo "📱 To start Home Assistant with real hardware:"
echo "   ./start_ha.sh"
echo ""

echo "⚠️  Make sure your relay device is accessible at 192.168.68.200:502"
echo "🔌 No need to run the mock server - Home Assistant will connect directly"
echo ""

echo "🔄 To switch back to mock testing:"
echo "   ./switch_to_mock.sh" 