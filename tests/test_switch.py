"""Tests for the Waveshare Relay Switch platform."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT

from waveshare_relay import DOMAIN
from waveshare_relay.switch import (
    async_setup_platform,
    async_setup_entry,
    WaveshareRelaySwitch,
)
from waveshare_relay.const import (
    CONF_NAME,
    CONF_ADDRESS,
    CONF_SWITCHES,
)


class TestWaveshareRelaySwitch:
    """Test the WaveshareRelaySwitch class."""

    @pytest.fixture
    def mock_hub(self):
        """Create a mock hub."""
        hub = MagicMock()
        hub._relay_states = [False] * 32
        hub.set_relay_state = AsyncMock(return_value=True)
        hub.read_relay_status = AsyncMock()
        return hub

    @pytest.fixture
    def switch_config(self):
        """Create a switch configuration."""
        return {
            CONF_NAME: "Test Switch",
            CONF_ADDRESS: 1,
        }

    def test_switch_initialization(self, mock_hub, switch_config):
        """Test switch initialization."""
        switch = WaveshareRelaySwitch(
            hub=mock_hub,
            name=switch_config[CONF_NAME],
            address=switch_config[CONF_ADDRESS],
            unique_id="test_switch"
        )
        
        assert switch._attr_name == "Test Switch"
        assert switch._attr_unique_id == "test_switch"
        assert switch._address == 1
        assert switch._attr_is_on is False
        assert switch._hub == mock_hub

    @pytest.mark.asyncio
    async def test_switch_turn_on_success(self, mock_hub, switch_config):
        """Test successful switch turn on."""
        switch = WaveshareRelaySwitch(
            hub=mock_hub,
            name=switch_config[CONF_NAME],
            address=switch_config[CONF_ADDRESS],
            unique_id="test_switch"
        )
        
        with patch.object(switch, 'async_write_ha_state') as mock_write:
            await switch.async_turn_on()
            
            mock_hub.set_relay_state.assert_called_once_with(1, True)
            assert switch._attr_is_on is True
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_switch_turn_on_failure(self, mock_hub, switch_config):
        """Test switch turn on failure."""
        mock_hub.set_relay_state.return_value = False
        
        switch = WaveshareRelaySwitch(
            hub=mock_hub,
            name=switch_config[CONF_NAME],
            address=switch_config[CONF_ADDRESS],
            unique_id="test_switch"
        )
        
        with patch.object(switch, 'async_write_ha_state') as mock_write:
            await switch.async_turn_on()
            
            mock_hub.set_relay_state.assert_called_once_with(1, True)
            assert switch._attr_is_on is True  # State should still be updated
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_switch_turn_off_success(self, mock_hub, switch_config):
        """Test successful switch turn off."""
        switch = WaveshareRelaySwitch(
            hub=mock_hub,
            name=switch_config[CONF_NAME],
            address=switch_config[CONF_ADDRESS],
            unique_id="test_switch"
        )
        switch._attr_is_on = True
        
        with patch.object(switch, 'async_write_ha_state') as mock_write:
            await switch.async_turn_off()
            
            mock_hub.set_relay_state.assert_called_once_with(1, False)
            assert switch._attr_is_on is False
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_switch_update(self, mock_hub, switch_config):
        """Test switch state update."""
        mock_hub._relay_states[0] = True  # Relay 1 is on
        
        switch = WaveshareRelaySwitch(
            hub=mock_hub,
            name=switch_config[CONF_NAME],
            address=switch_config[CONF_ADDRESS],
            unique_id="test_switch"
        )
        
        await switch.async_update()
        
        mock_hub.read_relay_status.assert_called_once()
        assert switch._attr_is_on is True

    @pytest.mark.asyncio
    async def test_switch_update_relay_off(self, mock_hub, switch_config):
        """Test switch state update when relay is off."""
        mock_hub._relay_states[0] = False  # Relay 1 is off
        
        switch = WaveshareRelaySwitch(
            hub=mock_hub,
            name=switch_config[CONF_NAME],
            address=switch_config[CONF_ADDRESS],
            unique_id="test_switch"
        )
        switch._attr_is_on = True  # Start with on state
        
        await switch.async_update()
        
        mock_hub.read_relay_status.assert_called_once()
        assert switch._attr_is_on is False


class TestSwitchPlatform:
    """Test the switch platform setup."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = MagicMock()
        hass.data = {DOMAIN: {}}
        return hass

    @pytest.fixture
    def mock_add_entities(self):
        """Create a mock add_entities function."""
        return AsyncMock()

    @pytest.fixture
    def platform_config(self):
        """Create a platform configuration."""
        return {
            CONF_NAME: "Test Relay",
            CONF_SWITCHES: [
                {CONF_NAME: "Switch 1", CONF_ADDRESS: 1},
                {CONF_NAME: "Switch 2", CONF_ADDRESS: 2},
            ],
        }

    @pytest.mark.asyncio
    async def test_async_setup_platform(self, mock_hass, mock_add_entities, platform_config):
        """Test platform setup from YAML."""
        mock_hub = MagicMock()
        mock_hass.data[DOMAIN]["test_entry_id"] = mock_hub
        
        discovery_info = {
            "entry_id": "test_entry_id",
            "config": platform_config,
        }
        
        await async_setup_platform(
            mock_hass,
            {},
            mock_add_entities,
            discovery_info
        )
        
        # Check that entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 2
        
        # Check entity properties
        assert entities[0]._attr_name == "Switch 1"
        assert entities[0]._address == 1
        assert entities[1]._attr_name == "Switch 2"
        assert entities[1]._address == 2

    @pytest.mark.asyncio
    async def test_async_setup_platform_no_discovery_info(self, mock_hass, mock_add_entities):
        """Test platform setup without discovery info."""
        await async_setup_platform(
            mock_hass,
            {},
            mock_add_entities,
            None
        )
        
        mock_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_setup_entry(self, mock_hass, mock_add_entities, platform_config):
        """Test platform setup from config entry."""
        mock_hub = MagicMock()
        mock_hass.data[DOMAIN]["test_entry_id"] = mock_hub
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        mock_entry.data = platform_config
        
        await async_setup_entry(
            mock_hass,
            mock_entry,
            mock_add_entities
        )
        
        # Check that entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 2

    @pytest.mark.asyncio
    async def test_async_setup_entry_no_switches(self, mock_hass, mock_add_entities):
        """Test platform setup with no switches configured."""
        mock_hub = MagicMock()
        mock_hass.data[DOMAIN]["test_entry_id"] = mock_hub
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        mock_entry.data = {CONF_NAME: "Test Relay", CONF_SWITCHES: []}
        
        await async_setup_entry(
            mock_hass,
            mock_entry,
            mock_add_entities
        )
        
        # Check that no entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 0

    def test_unique_id_generation(self, platform_config):
        """Test unique ID generation."""
        relay_name = platform_config[CONF_NAME]
        switch_name = platform_config[CONF_SWITCHES][0][CONF_NAME]
        expected_unique_id = f"{relay_name}_{switch_name.lower().replace(' ', '_')}"
        
        assert expected_unique_id == "Test Relay_switch_1" 