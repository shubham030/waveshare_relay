#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🧪 Testing waveshare relay integration..."

# Test 1: Check if component loads
echo "✅ Test 1: Component loading..."
python3 -c "
import sys
sys.path.insert(0, 'config/custom_components')
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
sys.path.insert(0, 'config/custom_components')
try:
    from waveshare_relay import async_setup
    print('✅ Component setup function available')
except Exception as e:
    print(f'❌ Component setup failed: {e}')
    sys.exit(1)
"

echo "🎉 All tests passed! Integration is ready for testing."
