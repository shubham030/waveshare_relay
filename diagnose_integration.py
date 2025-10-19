#!/usr/bin/env python3
"""Diagnostic script to check if the Waveshare Relay integration is properly configured."""

import os
import json
import sys
from pathlib import Path

def check_integration_files():
    """Check if all required integration files exist and are valid."""
    print("🔍 Diagnosing Waveshare Relay Integration...")
    print("=" * 50)
    
    # Required files for the integration
    required_files = {
        '__init__.py': 'Main integration module',
        'manifest.json': 'Integration metadata',  
        'config_flow.py': 'Configuration flow handler',
        'const.py': 'Constants and configuration',
        'hub.py': 'Hub communication module',
        'light.py': 'Light platform',
        'switch.py': 'Switch platform',
        'strings.json': 'UI translations'
    }
    
    print("📁 Checking Required Files:")
    all_files_exist = True
    for filename, description in required_files.items():
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"   ✅ {filename:<15} ({size:>5} bytes) - {description}")
        else:
            print(f"   ❌ {filename:<15} - MISSING - {description}")
            all_files_exist = False
    
    print()
    
    # Check manifest.json
    print("📋 Checking manifest.json:")
    try:
        with open('manifest.json', 'r') as f:
            manifest = json.load(f)
        
        required_keys = ['domain', 'name', 'version', 'config_flow', 'platforms']
        for key in required_keys:
            value = manifest.get(key, 'MISSING')
            print(f"   {key:<12}: {value}")
        
        # Validation checks
        if manifest.get('domain') != 'waveshare_relay':
            print("   ❌ Domain should be 'waveshare_relay'")
        else:
            print("   ✅ Domain is correct")
            
        if not manifest.get('config_flow'):
            print("   ❌ Config flow should be enabled")
        else:
            print("   ✅ Config flow is enabled")
            
        if 'light' not in manifest.get('platforms', []) or 'switch' not in manifest.get('platforms', []):
            print("   ❌ Missing required platforms")
        else:
            print("   ✅ All required platforms present")
            
    except Exception as e:
        print(f"   ❌ Error reading manifest.json: {e}")
        all_files_exist = False
    
    print()
    
    # Check strings.json
    print("🌐 Checking strings.json:")
    try:
        with open('strings.json', 'r') as f:
            strings = json.load(f)
        
        if 'config' in strings and 'step' in strings['config']:
            steps = list(strings['config']['step'].keys())
            print(f"   ✅ Config steps: {steps}")
        else:
            print("   ❌ Missing config steps")
            
        if 'options' in strings:
            print("   ✅ Options flow translations present")
        else:
            print("   ⚠️  Options flow translations missing (optional)")
            
    except Exception as e:
        print(f"   ❌ Error reading strings.json: {e}")
    
    print()
    
    # Try importing the main module
    print("🐍 Testing Python Import:")
    try:
        # Check if const.py can be imported
        import const
        print(f"   ✅ const.py imports successfully")
        print(f"      Domain: {getattr(const, 'DOMAIN', 'NOT FOUND')}")
    except Exception as e:
        print(f"   ❌ Error importing const.py: {e}")
    
    print()
    
    # Installation instructions
    print("📦 Installation Check:")
    current_dir = os.getcwd()
    print(f"   Current directory: {current_dir}")
    
    # Check if we're in the right location
    if current_dir.endswith('custom_components/waveshare_relay'):
        print("   ✅ Appears to be in correct Home Assistant location")
    elif 'custom_components' in current_dir:
        print("   ⚠️  In custom_components but not in waveshare_relay subdirectory")
    else:
        print("   ❌ Not in Home Assistant custom_components directory")
        print()
        print("📝 Installation Instructions:")
        print("   1. Copy all files to: /config/custom_components/waveshare_relay/")
        print("   2. Restart Home Assistant")
        print("   3. Go to Settings → Devices & Services → Add Integration")
        print("   4. Search for 'Waveshare Relay Hub'")
    
    print()
    
    if all_files_exist:
        print("🎉 Integration files look good!")
        print()
        print("🔄 Next Steps:")
        print("   1. Ensure files are in /config/custom_components/waveshare_relay/")
        print("   2. Restart Home Assistant completely")
        print("   3. Check Home Assistant logs for any errors")
        print("   4. Try adding the integration via UI")
    else:
        print("❌ Some issues found. Please fix the missing/invalid files.")
    
    return all_files_exist

if __name__ == "__main__":
    check_integration_files()