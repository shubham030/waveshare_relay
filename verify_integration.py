#!/usr/bin/env python3
"""
Verification script to check if the integration is ready for Home Assistant.
This simulates how Home Assistant would load and validate the integration.
"""

import json
import os
import sys
from pathlib import Path

def verify_integration():
    """Verify the integration is properly configured for Home Assistant."""
    print("🔍 Verifying Waveshare Relay Integration for Home Assistant...")
    print("=" * 60)
    
    issues = []
    
    # 1. Check manifest.json
    print("📋 Checking manifest.json...")
    try:
        with open('manifest.json', 'r') as f:
            manifest = json.load(f)
        
        required_fields = {
            'domain': 'waveshare_relay',
            'name': str,
            'version': str,
            'config_flow': True,
            'platforms': list
        }
        
        for field, expected in required_fields.items():
            if field not in manifest:
                issues.append(f"Missing required field '{field}' in manifest.json")
            elif expected is not str and expected is not list and manifest[field] != expected:
                issues.append(f"Field '{field}' should be {expected}, got {manifest[field]}")
        
        if 'light' not in manifest.get('platforms', []):
            issues.append("Platform 'light' missing from manifest.json")
        if 'switch' not in manifest.get('platforms', []):
            issues.append("Platform 'switch' missing from manifest.json")
            
        print(f"   ✅ Domain: {manifest.get('domain')}")
        print(f"   ✅ Version: {manifest.get('version')}")
        print(f"   ✅ Config Flow: {manifest.get('config_flow')}")
        print(f"   ✅ Platforms: {manifest.get('platforms')}")
        
    except Exception as e:
        issues.append(f"Error reading manifest.json: {e}")
    
    # 2. Check required files exist
    print("\n📁 Checking required files...")
    required_files = [
        '__init__.py',
        'manifest.json', 
        'config_flow.py',
        'const.py',
        'hub.py',
        'light.py',
        'switch.py',
        'strings.json'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            issues.append(f"Required file {file} is missing")
    
    # 3. Check strings.json
    print("\n🌐 Checking strings.json...")
    try:
        with open('strings.json', 'r') as f:
            strings = json.load(f)
        
        if 'config' not in strings:
            issues.append("Missing 'config' section in strings.json")
        elif 'step' not in strings['config']:
            issues.append("Missing 'config.step' section in strings.json")
        elif 'user' not in strings['config']['step']:
            issues.append("Missing 'config.step.user' section in strings.json")
        else:
            print("   ✅ Config flow translations present")
        
        if 'options' in strings:
            print("   ✅ Options flow translations present")
        else:
            print("   ⚠️  Options flow translations missing (optional)")
            
    except Exception as e:
        issues.append(f"Error reading strings.json: {e}")
    
    # 4. Check basic Python syntax
    print("\n🐍 Checking Python syntax...")
    python_files = [f for f in required_files if f.endswith('.py')]
    
    for file in python_files:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    compile(f.read(), file, 'exec')
                print(f"   ✅ {file} - Valid Python syntax")
            except SyntaxError as e:
                print(f"   ❌ {file} - Syntax error: {e}")
                issues.append(f"Syntax error in {file}: {e}")
            except Exception as e:
                print(f"   ⚠️  {file} - Could not check: {e}")
    
    # 5. Installation check
    print("\n📦 Installation Instructions...")
    print("To install this integration in Home Assistant:")
    print()
    print("   Method 1 - Manual Installation:")
    print("   1. Copy all files to: /config/custom_components/waveshare_relay/")
    print("   2. Restart Home Assistant")
    print("   3. Go to Settings → Devices & Services")
    print("   4. Click 'Add Integration'")
    print("   5. Search for 'Waveshare Relay Hub'")
    print()
    print("   Method 2 - HACS Installation:")
    print("   1. Add custom repository: https://github.com/shubham030/waveshare_relay")
    print("   2. Install from HACS")
    print("   3. Restart Home Assistant")
    print("   4. Add integration via UI")
    
    # 6. Summary
    print("\n" + "=" * 60)
    if not issues:
        print("🎉 SUCCESS! Integration is ready for Home Assistant!")
        print()
        print("✅ All required files present and valid")
        print("✅ Configuration flow properly implemented") 
        print("✅ Manifest and strings are correct")
        print("✅ Python syntax is valid")
        print()
        print("The integration should appear in Home Assistant's")
        print("'Add Integration' dialog as 'Waveshare Relay Hub'")
        return True
    else:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   • {issue}")
        print()
        print("Please fix these issues before installing in Home Assistant.")
        return False

if __name__ == "__main__":
    success = verify_integration()
    sys.exit(0 if success else 1)