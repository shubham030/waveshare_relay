"""Test configuration and fixtures for the Waveshare Relay integration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from waveshare_relay import DOMAIN
from waveshare_relay.const import (
    CONF_NAME,
    CONF_DEVICE_ADDRESS,
    CONF_TIMEOUT,
    CONF_LIGHTS,
    CONF_SWITCHES,
    CONF_ADDRESS,
    DEFAULT_PORT,
    DEFAULT_DEVICE_ADDRESS,
    DEFAULT_TIMEOUT,
)


@pytest.fixture
def mock_hub():
    """Create a mock hub for testing."""
    hub = MagicMock()
    hub._relay_states = [False] * 32
    hub._num_relays = 32
    hub._configured_relays = {1, 2, 3, 4}
    hub.set_relay_state = AsyncMock(return_value=True)
    hub.read_relay_status = AsyncMock(return_value=[False] * 32)
    return hub


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: DEFAULT_PORT,
        CONF_NAME: "Test Relay",
        CONF_DEVICE_ADDRESS: DEFAULT_DEVICE_ADDRESS,
        CONF_TIMEOUT: DEFAULT_TIMEOUT,
        "num_relays": 32,
        CONF_LIGHTS: [
            {CONF_NAME: "Test Light 1", CONF_ADDRESS: 1},
            {CONF_NAME: "Test Light 2", CONF_ADDRESS: 2},
        ],
        CONF_SWITCHES: [
            {CONF_NAME: "Test Switch 1", CONF_ADDRESS: 3},
            {CONF_NAME: "Test Switch 2", CONF_ADDRESS: 4},
        ],
    }


@pytest.fixture
def mock_config_entry(mock_config):
    """Create a mock config entry for testing."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = mock_config
    entry.state = ConfigEntryState.LOADED
    return entry


@pytest.fixture
def mock_tcp_connection():
    """Mock TCP connection for testing."""
    reader = AsyncMock()
    writer = AsyncMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    
    return reader, writer


@pytest.fixture
def sample_relay_response():
    """Sample relay response data for testing."""
    # Mock response for reading 32 relay states (4 bytes)
    # All relays off: [0x00, 0x00, 0x00, 0x00]
    return bytes([0x01, 0x01, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])


@pytest.fixture
def sample_relay_on_response():
    """Sample relay response with some relays on."""
    # Mock response with relays 1 and 3 on: [0x05, 0x00, 0x00, 0x00]
    return bytes([0x01, 0x01, 0x04, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00]) 