"""Integration tests for the Waveshare Relay component."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT

from waveshare_relay import DOMAIN, async_setup, async_setup_entry, async_unload_entry
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


class TestIntegration:
    """Test the complete integration."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = MagicMock()
        hass.data = {}
        hass.async_create_task = MagicMock()
        hass.config_entries = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        return hass

    @pytest.fixture
    def yaml_config(self):
        """Create a YAML configuration."""
        return {
            DOMAIN: [
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_PORT: DEFAULT_PORT,
                    CONF_NAME: "Test Relay 1",
                    CONF_DEVICE_ADDRESS: DEFAULT_DEVICE_ADDRESS,
                    CONF_TIMEOUT: DEFAULT_TIMEOUT,
                    "num_relays": 32,
                    CONF_LIGHTS: [
                        {CONF_NAME: "Light 1", CONF_ADDRESS: 1},
                        {CONF_NAME: "Light 2", CONF_ADDRESS: 2},
                    ],
                    CONF_SWITCHES: [
                        {CONF_NAME: "Switch 1", CONF_ADDRESS: 3},
                        {CONF_NAME: "Switch 2", CONF_ADDRESS: 4},
                    ],
                },
                {
                    CONF_HOST: "192.168.1.101",
                    CONF_PORT: DEFAULT_PORT,
                    CONF_NAME: "Test Relay 2",
                    CONF_DEVICE_ADDRESS: DEFAULT_DEVICE_ADDRESS,
                    CONF_TIMEOUT: DEFAULT_TIMEOUT,
                    "num_relays": 16,
                    CONF_LIGHTS: [
                        {CONF_NAME: "Light 3", CONF_ADDRESS: 1},
                    ],
                    CONF_SWITCHES: [
                        {CONF_NAME: "Switch 3", CONF_ADDRESS: 2},
                    ],
                },
            ]
        }

    @pytest.fixture
    def config_entry_data(self):
        """Create config entry data."""
        return {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: DEFAULT_PORT,
            CONF_NAME: "Test Relay",
            CONF_DEVICE_ADDRESS: DEFAULT_DEVICE_ADDRESS,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            "num_relays": 32,
            CONF_LIGHTS: [
                {CONF_NAME: "Light 1", CONF_ADDRESS: 1},
                {CONF_NAME: "Light 2", CONF_ADDRESS: 2},
            ],
            CONF_SWITCHES: [
                {CONF_NAME: "Switch 1", CONF_ADDRESS: 3},
                {CONF_NAME: "Switch 2", CONF_ADDRESS: 4},
            ],
        }

    @pytest.mark.asyncio
    async def test_async_setup_yaml(self, mock_hass, yaml_config):
        """Test YAML setup."""
        with patch('waveshare_relay.async_load_platform') as mock_load_platform:
            with patch('waveshare_relay.WaveshareRelayHub.create', new_callable=AsyncMock) as mock_create:
                mock_hub = MagicMock()
                mock_create.return_value = mock_hub
                
                result = await async_setup(mock_hass, yaml_config)
                
                assert result is True
                assert DOMAIN in mock_hass.data
                assert len(mock_hass.data[DOMAIN]) == 2
                
                # Check that hubs were created
                mock_create.assert_called()
                assert mock_create.call_count == 2
                
                # Check that platforms were loaded
                assert mock_hass.async_create_task.call_count == 4  # 2 relays * 2 platforms

    @pytest.mark.asyncio
    async def test_async_setup_yaml_invalid_config(self, mock_hass):
        """Test YAML setup with invalid configuration."""
        invalid_config = {
            DOMAIN: [
                {
                    CONF_HOST: "192.168.1.100",
                    # Missing required CONF_NAME
                }
            ]
        }
        
        result = await async_setup(mock_hass, invalid_config)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_async_setup_yaml_no_config(self, mock_hass):
        """Test YAML setup with no waveshare_relay config."""
        config = {"other_domain": {}}
        
        result = await async_setup(mock_hass, config)
        
        assert result is True
        assert DOMAIN not in mock_hass.data

    @pytest.mark.asyncio
    async def test_async_setup_entry(self, mock_hass, config_entry_data):
        """Test config entry setup."""
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        mock_entry.data = config_entry_data
        
        with patch('waveshare_relay.WaveshareRelayHub.create', new_callable=AsyncMock) as mock_create:
            mock_hub = MagicMock()
            mock_create.return_value = mock_hub
            
            result = await async_setup_entry(mock_hass, mock_entry)
            
            assert result is True
            assert DOMAIN in mock_hass.data
            assert "test_entry_id" in mock_hass.data[DOMAIN]
            assert mock_hass.data[DOMAIN]["test_entry_id"] == mock_hub
            
            # Check that platforms were forwarded
            mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
                mock_entry, ["light", "switch"]
            )

    @pytest.mark.asyncio
    async def test_async_unload_entry(self, mock_hass, config_entry_data):
        """Test config entry unload."""
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        
        # Setup the entry first
        mock_hass.data[DOMAIN] = {"test_entry_id": MagicMock()}
        
        result = await async_unload_entry(mock_hass, mock_entry)
        
        assert result is True
        assert "test_entry_id" not in mock_hass.data[DOMAIN]
        
        # Check that platforms were unloaded
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_entry, ["light", "switch"]
        )

    @pytest.mark.asyncio
    async def test_async_unload_entry_failure(self, mock_hass, config_entry_data):
        """Test config entry unload failure."""
        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_id"
        
        # Setup the entry first
        mock_hass.data[DOMAIN] = {"test_entry_id": MagicMock()}
        
        # Mock platform unload failure
        mock_hass.config_entries.async_unload_platforms.return_value = False
        
        result = await async_unload_entry(mock_hass, mock_entry)
        
        assert result is False
        assert "test_entry_id" in mock_hass.data[DOMAIN]  # Should not be removed

    @pytest.mark.asyncio
    async def test_hub_creation_with_different_relay_counts(self, mock_hass):
        """Test hub creation with different relay counts."""
        configs = [
            {"num_relays": 8, "expected_byte_size": 1},
            {"num_relays": 16, "expected_byte_size": 2},
            {"num_relays": 24, "expected_byte_size": 3},
            {"num_relays": 32, "expected_byte_size": 4},
        ]
        
        for config in configs:
            hub_config = {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: DEFAULT_PORT,
                CONF_NAME: "Test Relay",
                "num_relays": config["num_relays"],
            }
            
            with patch('waveshare_relay.WaveshareRelayHub.read_relay_status', new_callable=AsyncMock):
                from waveshare_relay.hub import WaveshareRelayHub
                hub = await WaveshareRelayHub.create(hub_config)
                
                assert hub._num_relays == config["num_relays"]
                assert hub._byte_size == config["expected_byte_size"]
                assert len(hub._relay_states) == config["num_relays"]


class TestEndToEnd:
    """End-to-end tests for the complete component."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test a complete workflow from setup to relay control."""
        from waveshare_relay.hub import WaveshareRelayHub
        from waveshare_relay.switch import WaveshareRelaySwitch
        from waveshare_relay.light import WaveshareRelayLight
        
        # Test configuration
        config = {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: DEFAULT_PORT,
            CONF_NAME: "Test Relay",
            CONF_DEVICE_ADDRESS: DEFAULT_DEVICE_ADDRESS,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            "num_relays": 32,
            CONF_LIGHTS: [
                {CONF_NAME: "Test Light", CONF_ADDRESS: 1},
            ],
            CONF_SWITCHES: [
                {CONF_NAME: "Test Switch", CONF_ADDRESS: 2},
            ],
        }
        
        # Mock the hub communication
        with patch.object(WaveshareRelayHub, 'send_command', new_callable=AsyncMock) as mock_send:
            # Mock successful responses
            mock_send.return_value = bytes([0x01, 0x0F, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00])
            
            # Create hub
            hub = await WaveshareRelayHub.create(config)
            
            # Create entities
            light = WaveshareRelayLight(
                hub=hub,
                name="Test Light",
                address=1,
                unique_id="test_light"
            )
            
            switch = WaveshareRelaySwitch(
                hub=hub,
                name="Test Switch",
                address=2,
                unique_id="test_switch"
            )
            
            # Test initial states
            assert light._attr_is_on is False
            assert switch._attr_is_on is False
            
            # Test turning on light
            with patch.object(light, 'async_write_ha_state'):
                await light.async_turn_on()
                assert light._attr_is_on is True
                assert hub._relay_states[0] is True
            
            # Test turning on switch
            with patch.object(switch, 'async_write_ha_state'):
                await switch.async_turn_on()
                assert switch._attr_is_on is True
                assert hub._relay_states[1] is True
            
            # Test turning off light
            with patch.object(light, 'async_write_ha_state'):
                await light.async_turn_off()
                assert light._attr_is_on is False
                assert hub._relay_states[0] is False
            
            # Test turning off switch
            with patch.object(switch, 'async_write_ha_state'):
                await switch.async_turn_off()
                assert switch._attr_is_on is False
                assert hub._relay_states[1] is False
            
            # Verify that commands were sent
            assert mock_send.call_count >= 4  # At least 4 commands (2 on, 2 off) 