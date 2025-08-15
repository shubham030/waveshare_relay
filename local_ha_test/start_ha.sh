#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🏠 Starting Home Assistant..."
echo "📱 Open http://localhost:8123 in your browser"
echo "🔌 Your waveshare relay integration will be available"
echo "⏹️  Press Ctrl+C to stop"
hass --config config
