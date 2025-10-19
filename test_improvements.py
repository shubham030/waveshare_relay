#!/usr/bin/env python3
"""
Test script to verify the improved functionality of the Waveshare Relay Hub.
This script tests the new connection management, retry logic, and circuit breaker features.
"""

import asyncio
import logging
import time
from unittest.mock import MagicMock, AsyncMock, patch

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_connection_manager():
    """Test the new connection manager with retry logic."""
    from hub import ConnectionManager
    
    # Test with a real configuration
    connection_manager = ConnectionManager("192.168.1.100", 502, timeout=5.0)
    
    # Test command (read relay status for device address 1)
    test_command = bytes([0x01, 0x01, 0x00, 0x00, 0x00, 0x20, 0x3D, 0xD2])
    
    logger.info("Testing connection manager with retry logic...")
    
    try:
        response = await connection_manager.send_command_with_retry(test_command)
        if response:
            logger.info(f"Success! Received response: {response.hex()}")
        else:
            logger.warning("No response received")
    except Exception as e:
        logger.error(f"Connection test failed: {e}")

async def test_hub_improvements():
    """Test the improved hub functionality."""
    from hub import WaveshareRelayHub
    
    config = {
        "host": "192.168.1.100",
        "port": 502,
        "name": "Test Hub",
        "device_address": 1,
        "timeout": 5,
        "num_relays": 32,
        "lights": [
            {"name": "Test Light 1", "address": 1},
            {"name": "Test Light 2", "address": 2},
        ],
        "switches": [
            {"name": "Test Switch 1", "address": 3},
            {"name": "Test Switch 2", "address": 4},
        ],
    }
    
    logger.info("Testing improved hub functionality...")
    
    try:
        hub = WaveshareRelayHub(config)
        
        # Test availability
        logger.info(f"Hub availability: {hub.is_available}")
        
        # Test connection stats
        stats = hub.connection_stats
        logger.info(f"Connection stats: {stats}")
        
        # Test reading relay status
        states = await hub.read_relay_status()
        if states:
            logger.info(f"Current relay states: {states[:8]}...")  # Show first 8 states
        
        # Test setting relay state with new retry logic
        logger.info("Testing relay state changes...")
        success = await hub.set_relay_state(1, True)
        logger.info(f"Set relay 1 to ON: {'Success' if success else 'Failed'}")
        
        await asyncio.sleep(1)
        
        success = await hub.set_relay_state(1, False)
        logger.info(f"Set relay 1 to OFF: {'Success' if success else 'Failed'}")
        
        # Show final stats
        final_stats = hub.connection_stats
        logger.info(f"Final connection stats: {final_stats}")
        
    except Exception as e:
        logger.error(f"Hub test failed: {e}")

async def test_circuit_breaker():
    """Test the circuit breaker functionality with mocked failures."""
    from hub import ConnectionManager
    
    logger.info("Testing circuit breaker functionality...")
    
    connection_manager = ConnectionManager("192.168.1.100", 502, timeout=1.0)
    # Set a lower threshold for testing
    connection_manager.circuit_breaker_config.failure_threshold = 3
    connection_manager.circuit_breaker_config.recovery_timeout = 5.0
    
    test_command = bytes([0x01, 0x01, 0x00, 0x00, 0x00, 0x20, 0x3D, 0xD2])
    
    # Mock the _send_command_single method to simulate failures
    original_method = connection_manager._send_command_single
    
    async def mock_failing_command(command):
        raise ConnectionError("Simulated network failure")
    
    connection_manager._send_command_single = mock_failing_command
    
    # Test multiple failures to trigger circuit breaker
    for i in range(5):
        logger.info(f"Attempt {i+1} (expecting failure)...")
        response = await connection_manager.send_command_with_retry(test_command)
        if response is None:
            logger.info(f"Command failed as expected (failure count: {connection_manager._failure_count})")
        
        if connection_manager._circuit_breaker_open:
            logger.info("Circuit breaker opened!")
            break
    
    # Test that circuit breaker blocks further attempts
    logger.info("Testing circuit breaker blocking...")
    response = await connection_manager.send_command_with_retry(test_command)
    if response is None:
        logger.info("Circuit breaker successfully blocked the command")
    
    # Restore original method for recovery test
    connection_manager._send_command_single = original_method
    
    logger.info("Waiting for circuit breaker recovery...")
    await asyncio.sleep(6)  # Wait for recovery timeout
    
    logger.info("Testing circuit breaker recovery...")
    response = await connection_manager.send_command_with_retry(test_command)
    if response is not None:
        logger.info("Circuit breaker recovered successfully!")
    else:
        logger.info("Circuit breaker recovery test - no response (may be normal if device not available)")

async def main():
    """Run all tests."""
    logger.info("Starting Waveshare Relay Hub improvement tests...")
    
    # Test 1: Connection Manager
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Connection Manager")
    logger.info("="*50)
    await test_connection_manager()
    
    # Test 2: Hub Improvements
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Hub Improvements")
    logger.info("="*50)
    await test_hub_improvements()
    
    # Test 3: Circuit Breaker
    logger.info("\n" + "="*50)
    logger.info("TEST 3: Circuit Breaker")
    logger.info("="*50)
    await test_circuit_breaker()
    
    logger.info("\n" + "="*50)
    logger.info("All tests completed!")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(main())