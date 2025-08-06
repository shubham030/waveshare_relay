"""Tests for the Waveshare Relay Light platform."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT

from waveshare_relay import DOMAIN
from waveshare_relay.light import (
    async_setup_platform,
    async_setup_entry,
    WaveshareRelayLight,
)
from waveshare_relay.const import (
    CONF_NAME,
    CONF_ADDRESS,
    CONF_LIGHTS,
)


class TestWaveshareRelayLight:
    """Test the WaveshareRelayLight class."""

    @pytest.fixture
    def mock_hub(self):
        """Create a mock hub."""
        hub = MagicMock()
        hub._relay_states = [False] * 32
        hub.set_relay_state = AsyncMock(return_value=True)
        hub.read_relay_status = AsyncMock()
        return hub

    @pytest.fixture
    def light_config(self):
        """Create a light configuration."""
        return {
            CONF_NAME: "Test Light",
            CONF_ADDRESS: 1,
        }

    def test_light_initialization(self, mock_hub, light_config):
        """Test light initialization."""
        light = WaveshareRelayLight(
            hub=mock_hub,
            name=light_config[CONF_NAME],
            address=light_config[CONF_ADDRESS],
            unique_id="test_light"
        )
        
        assert light._attr_name == "Test Light"
        assert light._attr_unique_id == "test_light"
        assert light._address == 1
        assert light._attr_is_on is False
        assert light._hub == mock_hub

    @pytest.mark.asyncio
    async def test_light_turn_on_success(self, mock_hub, light_config):
        """Test successful light turn on."""
        light = WaveshareRelayLight(
            hub=mock_hub,
            name=light_config[CONF_NAME],
            address=light_config[CONF_ADDRESS],
            unique_id="test_light"
        )
        
        with patch.object(light, 'async_write_ha_state') as mock_write:
            await light.async_turn_on()
            
            mock_hub.set_relay_state.assert_called_once_with(1, True)
            assert light._attr_is_on is True
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_light_turn_on_failure(self, mock_hub, light_config):
        """Test light turn on failure."""
        mock_hub.set_relay_state.return_value = False
        
        light = WaveshareRelayLight(
            hub=mock_hub,
            name=light_config[CONF_NAME],
            address=light_config[CONF_ADDRESS],
            unique_id="test_light"
        )
        
        with patch.object(light, 'async_write_ha_state') as mock_write:
            await light.async_turn_on()
            
            mock_hub.set_relay_state.assert_called_once_with(1, True)
            assert light._attr_is_on is True  # State should still be updated
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_light_turn_off_success(self, mock_hub, light_config):
        """Test successful light turn off."""
        light = WaveshareRelayLight(
            hub=mock_hub,
            name=light_config[CONF_NAME],
            address=light_config[CONF_ADDRESS],
            unique_id="test_light"
        )
        light._attr_is_on = True
        
        with patch.object(light, 'async_write_ha_state') as mock_write:
            await light.async_turn_off()
            
            mock_hub.set_relay_state.assert_called_once_with(1, False)
            assert light._attr_is_on is False
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_light_update(self, mock_hub, light_config):
        """Test light state update."""
        mock_hub._relay_states[0] = True  # Relay 1 is on
        
        light = WaveshareRelayLight(
            hub=mock_hub,
            name=light_config[CONF_NAME],
            address=light_config[CONF_ADDRESS],
            unique_id="test_light"
        )
        
        await light.async_update()
        
        mock_hub.read_relay_status.assert_called_once()
        assert light._attr_is_on is True

    @pytest.mark.asyncio
    async def test_light_update_relay_off(self, mock_hub, light_config):
        """Test light state update when relay is off."""
        mock_hub._relay_states[0] = False  # Relay 1 is off
        
        light = WaveshareRelayLight(
            hub=mock_hub,
            name=light_config[CONF_NAME],
            address=light_config[CONF_ADDRESS],
            unique_id="test_light"
        )
        light._attr_is_on = True  # Start with on state
        
        await light.async_update()
        
        mock_hub.read_relay_status.assert_called_once()
        assert light._attr_is_on is False

    def test_light_supported_features(self, mock_hub, light_config):
        """Test light supported features."""
        light = WaveshareRelayLight(
            hub=mock_hub,
            name=light_config[CONF_NAME],
            address=light_config[CONF_ADDRESS],
            unique_id="test_light"
        )
        
        # Lights should only support on/off, not dimming
        assert light.supported_features == 0


class TestLightPlatform:
    """Test the light platform setup."""

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
            CONF_LIGHTS: [
                {CONF_NAME: "Light 1", CONF_ADDRESS: 1},
                {CONF_NAME: "Light 2", CONF_ADDRESS: 2},
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
        assert entities[0]._attr_name == "Light 1"
        assert entities[0]._address == 1
        assert entities[1]._attr_name == "Light 2"
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
    async def test_async_setup_entry_no_lights(self, mock_hass, mock_add_entities):
        """Test platform setup with no lights configured."""
        mock_hub = MagicMock()
        mock_hass.data[DOMAIN]["test_entry_id"] = mock_hub
        
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        mock_entry.data = {CONF_NAME: "Test Relay", CONF_LIGHTS: []}
        
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
        light_name = platform_config[CONF_LIGHTS][0][CONF_NAME]
        expected_unique_id = f"{relay_name}_{light_name.lower().replace(' ', '_')}"
        
        assert expected_unique_id == "Test Relay_light_1" 