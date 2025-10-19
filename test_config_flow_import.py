#!/usr/bin/env python3
"""Test script to verify config flow can be imported properly."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports for the config flow."""
    try:
        print("Testing const import...")
        from const import DOMAIN
        print(f"✓ DOMAIN = {DOMAIN}")
        
        print("Testing config_flow import...")
        from config_flow import ConfigFlow
        print(f"✓ ConfigFlow class imported successfully")
        print(f"✓ ConfigFlow.DOMAIN = {getattr(ConfigFlow, 'DOMAIN', 'NOT SET')}")
        print(f"✓ ConfigFlow.VERSION = {getattr(ConfigFlow, 'VERSION', 'NOT SET')}")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_flow_structure():
    """Test that the config flow has all required components."""
    try:
        from config_flow import ConfigFlow, OptionsFlowHandler
        
        # Check that required methods exist
        methods_to_check = [
            'async_step_user',
            'async_get_options_flow'
        ]
        
        for method in methods_to_check:
            if hasattr(ConfigFlow, method):
                print(f"✓ {method} exists")
            else:
                print(f"✗ {method} missing")
                return False
                
        print("✓ All required methods present")
        return True
        
    except Exception as e:
        print(f"✗ Structure test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Config Flow Import Test ===")
    
    success = True
    success &= test_imports()
    success &= test_config_flow_structure()
    
    if success:
        print("\n🎉 All tests passed! Config flow should work.")
    else:
        print("\n❌ Tests failed. Check the errors above.")
    
    sys.exit(0 if success else 1)