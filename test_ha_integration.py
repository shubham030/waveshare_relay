#!/usr/bin/env python3
"""Test Home Assistant integration loading."""

import asyncio
import logging
import sys
import os
from unittest.mock import Mock

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_integration_loading():
    """Test if the integration can be loaded properly."""
    try:
        # Add the local test directory to Python path
        test_dir = "/Users/shubham/Desktop/Personal/waveshare_relay/local_ha_test/config/custom_components"
        if test_dir not in sys.path:
            sys.path.insert(0, test_dir)
        
        logger.info("Testing waveshare_relay integration import...")
        
        # Test importing the main module
        import waveshare_relay
        logger.info("✓ Main module imported successfully")
        
        # Test importing config flow
        from waveshare_relay.config_flow import ConfigFlow
        logger.info(f"✓ ConfigFlow imported: {ConfigFlow}")
        logger.info(f"✓ ConfigFlow.DOMAIN = {getattr(ConfigFlow, 'DOMAIN', 'NOT SET')}")
        logger.info(f"✓ ConfigFlow.VERSION = {getattr(ConfigFlow, 'VERSION', 'NOT SET')}")
        
        # Test const values
        from waveshare_relay.const import DOMAIN
        logger.info(f"✓ DOMAIN constant = {DOMAIN}")
        
        # Check if config flow has required methods
        required_methods = ['async_step_user', 'async_get_options_flow']
        for method in required_methods:
            if hasattr(ConfigFlow, method):
                logger.info(f"✓ {method} method exists")
            else:
                logger.error(f"✗ {method} method missing")
                return False
        
        logger.info("🎉 Integration loading test passed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Integration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_config_flow_creation():
    """Test if config flow can be instantiated."""
    try:
        from waveshare_relay.config_flow import ConfigFlow
        
        # Mock Home Assistant context
        mock_hass = Mock()
        mock_hass.config_entries = Mock()
        
        # Create config flow instance
        flow = ConfigFlow()
        flow.hass = mock_hass
        
        logger.info("✓ ConfigFlow instance created successfully")
        logger.info(f"✓ Flow domain: {getattr(flow, 'DOMAIN', 'NOT SET')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Config flow creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    logger.info("=== Home Assistant Integration Loading Test ===")
    
    success = True
    success &= await test_integration_loading()
    success &= await test_config_flow_creation()
    
    if success:
        logger.info("\n🎉 ALL TESTS PASSED! Integration should work in Home Assistant.")
    else:
        logger.error("\n❌ TESTS FAILED! Check errors above.")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)