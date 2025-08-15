#!/bin/bash

# Start Mock Modbus TCP Server for Testing
# This simulates the Waveshare relay device

cd "$(dirname "$0")"
source venv/bin/activate

echo "🚀 Starting Mock Modbus TCP Server..."
echo "🔌 This simulates a Waveshare relay device for testing"
echo "📱 Server will listen on 0.0.0.0:502"
echo "🌐 Use localhost or 127.0.0.1 in your Home Assistant config"
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Run the mock server
python3 mock_relay_server.py 