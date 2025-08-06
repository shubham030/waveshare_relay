"""Tests for the Waveshare Relay Hub."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import json
from pathlib import Path

from waveshare_relay.hub import WaveshareRelayHub
from waveshare_relay.const import CONF_LIGHTS, CONF_SWITCHES, CONF_RESTORE_STATE, CONF_NAME, CONF_ADDRESS


class TestWaveshareRelayHub:
    """Test the WaveshareRelayHub class."""

    @pytest.fixture
    def sample_config(self):
        """Create a sample configuration."""
        return {
            "host": "192.168.1.100",
            "port": 502,
            "name": "Test Hub",
            "device_address": 1,
            "timeout": 5,
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
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = MagicMock()
        hass.config.config_dir = "/tmp"
        return hass

    @pytest.fixture
    def hub(self, sample_config, mock_hass):
        """Create a hub instance."""
        return WaveshareRelayHub(sample_config, mock_hass)

    def test_hub_initialization(self, sample_config, mock_hass):
        """Test hub initialization."""
        hub = WaveshareRelayHub(sample_config, mock_hass)
        
        assert hub._host == "192.168.1.100"
        assert hub._port == 502
        assert hub._device_address == 1
        assert hub._timeout == 5
        assert hub._num_relays == 32
        assert hub._hass == mock_hass
        assert hub._restore_state is True  # Default value
        assert hub._configured_relays == {1, 2, 3, 4}

    def test_hub_initialization_without_hass(self, sample_config):
        """Test hub initialization without hass instance."""
        hub = WaveshareRelayHub(sample_config)
        
        assert hub._host == "192.168.1.100"
        assert hub._hass is None
        assert hub._restore_state is True
        assert hub._state_file is None

    def test_hub_initialization_with_restore_state_disabled(self, sample_config, mock_hass):
        """Test hub initialization with restore_state disabled."""
        config = sample_config.copy()
        config[CONF_RESTORE_STATE] = False
        hub = WaveshareRelayHub(config, mock_hass)
        
        assert hub._restore_state is False
        assert hub._state_file is None

    @pytest.mark.asyncio
    async def test_hub_create_factory_method(self, sample_config, mock_hass):
        """Test hub creation using factory method."""
        with patch.object(WaveshareRelayHub, 'read_relay_status', new_callable=AsyncMock) as mock_read:
            hub = await WaveshareRelayHub.create(sample_config, mock_hass)
            
            assert isinstance(hub, WaveshareRelayHub)
            assert hub._host == "192.168.1.100"
            mock_read.assert_called_once()

    def test_get_configured_relays(self, sample_config, mock_hass):
        """Test getting configured relays."""
        hub = WaveshareRelayHub(sample_config, mock_hass)
        
        configured = hub._get_configured_relays(sample_config)
        assert configured == {1, 2, 3, 4}

    def test_get_configured_relays_empty(self, sample_config, mock_hass):
        """Test getting configured relays with empty config."""
        config = {
            "host": "192.168.1.100",
            "port": 502,
            "name": "Test Hub",
        }
        hub = WaveshareRelayHub(config, mock_hass)
        
        configured = hub._get_configured_relays(config)
        assert configured == set()

    @pytest.mark.asyncio
    async def test_set_relay_state_valid(self, hub):
        """Test setting a valid relay state."""
        with patch.object(hub, '_send_relay_states', new_callable=AsyncMock) as mock_send:
            with patch.object(hub, '_save_last_states', new_callable=AsyncMock) as mock_save:
                mock_send.return_value = True
                
                result = await hub.set_relay_state(1, True)
                
                assert result is True
                assert hub._relay_states[0] is True
                mock_send.assert_called_once()
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_relay_state_invalid_number(self, hub):
        """Test setting relay state with invalid relay number."""
        with pytest.raises(ValueError):
            await hub.set_relay_state(0, True)
        
        with pytest.raises(ValueError):
            await hub.set_relay_state(33, True)

    @pytest.mark.asyncio
    async def test_set_relay_state_not_configured(self, hub):
        """Test setting relay state for non-configured relay."""
        with pytest.raises(ValueError):
            await hub.set_relay_state(10, True)  # Relay 10 is not configured

    @pytest.mark.asyncio
    async def test_set_relay_state_send_failure(self, hub):
        """Test setting relay state when send fails."""
        with patch.object(hub, '_send_relay_states', new_callable=AsyncMock) as mock_send:
            with patch.object(hub, '_save_last_states', new_callable=AsyncMock) as mock_save:
                mock_send.return_value = None
                
                result = await hub.set_relay_state(1, True)
                
                assert result is False
                assert hub._relay_states[0] is True  # State should still be updated
                mock_send.assert_called_once()
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_relay_states(self, hub):
        """Test sending relay states."""
        with patch.object(hub, 'send_command', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = b'\x01\x0F\x00\x00\x00\x20\x04\x00\x00\x00\x00\x00\x00'
            
            result = await hub._send_relay_states()
            
            assert result is not None
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_success(self, hub):
        """Test successful command sending."""
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_conn.return_value = (mock_reader, mock_writer)
            
            command = b'\x01\x0F\x00\x00\x00\x20\x04\x00\x00\x00\x00\x00\x00'
            result = await hub.send_command(command)
            
            assert result is not None
            mock_writer.write.assert_called_once_with(command)
            mock_writer.drain.assert_called_once()
            mock_writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_timeout(self, hub):
        """Test command sending with timeout."""
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.side_effect = asyncio.TimeoutError()
            
            command = b'\x01\x0F\x00\x00\x00\x20\x04\x00\x00\x00\x00\x00\x00'
            result = await hub.send_command(command)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_send_command_connection_error(self, hub):
        """Test command sending with connection error."""
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.side_effect = ConnectionRefusedError()
            
            command = b'\x01\x0F\x00\x00\x00\x20\x04\x00\x00\x00\x00\x00\x00'
            result = await hub.send_command(command)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_read_relay_status_success(self, hub):
        """Test successful relay status reading."""
        with patch.object(hub, 'send_command', new_callable=AsyncMock) as mock_send:
            # Mock response with some data
            mock_response = b'\x01\x01\x04\x05\x00\x00\x00\x00\x00\x00'
            mock_send.return_value = mock_response
            
            result = await hub.read_relay_status()
            
            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 32
            # Just check that the method works and returns the expected structure
            assert all(isinstance(state, bool) for state in result)

    @pytest.mark.asyncio
    async def test_read_relay_status_invalid_response(self, hub):
        """Test relay status reading with invalid response."""
        with patch.object(hub, 'send_command', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None
            
            result = await hub.read_relay_status()
            
            assert result is None

    @pytest.mark.asyncio
    async def test_read_relay_status_no_response(self, hub):
        """Test relay status reading with no response."""
        with patch.object(hub, 'send_command', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = b''  # Empty response
            
            result = await hub.read_relay_status()
            
            assert result is None

    def test_calculate_crc(self, hub):
        """Test CRC calculation."""
        data = b'\x01\x0F\x00\x00\x00\x20\x04\x00\x00\x00\x00\x00'
        crc = hub.calculate_crc(data)
        
        assert isinstance(crc, bytes)
        assert len(crc) == 2

    def test_calculate_crc_empty(self, hub):
        """Test CRC calculation with empty data."""
        data = b''
        crc = hub.calculate_crc(data)
        
        assert isinstance(crc, bytes)
        assert len(crc) == 2

    @pytest.mark.asyncio
    async def test_load_last_states_file_exists(self, hub):
        """Test loading last states when file exists."""
        saved_states = {"1": True, "3": False, "4": True}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(saved_states))):
            with patch.object(Path, 'exists', return_value=True):
                await hub._load_last_states()
                
                # Check that configured relays are restored
                assert hub._relay_states[0] is True   # Relay 1
                assert hub._relay_states[2] is False  # Relay 3
                assert hub._relay_states[3] is True   # Relay 4

    @pytest.mark.asyncio
    async def test_load_last_states_file_not_exists(self, hub):
        """Test loading last states when file doesn't exist."""
        with patch.object(Path, 'exists', return_value=False):
            await hub._load_last_states()
            
            # States should remain unchanged (all False)
            assert all(not state for state in hub._relay_states)

    @pytest.mark.asyncio
    async def test_load_last_states_invalid_json(self, hub):
        """Test loading last states with invalid JSON."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch.object(Path, 'exists', return_value=True):
                await hub._load_last_states()
                
                # States should remain unchanged
                assert all(not state for state in hub._relay_states)

    @pytest.mark.asyncio
    async def test_save_last_states(self, hub):
        """Test saving last states."""
        # Set some relay states
        hub._relay_states[0] = True   # Relay 1
        hub._relay_states[2] = False  # Relay 3
        hub._relay_states[4] = True   # Relay 5
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch.object(Path, 'mkdir') as mock_mkdir:
                await hub._save_last_states()
                
                mock_mkdir.assert_called_once()
                mock_file.assert_called_once()
                
                # Check that write was called with JSON data
                write_calls = mock_file().write.call_args_list
                assert len(write_calls) > 0

    @pytest.mark.asyncio
    async def test_save_last_states_no_file(self, hub):
        """Test saving last states when no file is configured."""
        hub._state_file = None
        
        await hub._save_last_states()
        # Should not raise any exceptions

    @pytest.mark.asyncio
    async def test_restore_last_states_enabled(self, hub):
        """Test restoring last states when enabled."""
        # Set up some saved states
        hub._relay_states[0] = True   # Relay 1
        hub._relay_states[2] = False  # Relay 3
        
        with patch.object(hub, '_load_last_states', new_callable=AsyncMock) as mock_load:
            with patch.object(hub, '_send_relay_states', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = True
                
                await hub.restore_last_states()
                
                mock_load.assert_called_once()
                mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_last_states_disabled(self, hub):
        """Test restoring last states when disabled."""
        hub._restore_state = False
        
        with patch.object(hub, '_load_last_states', new_callable=AsyncMock) as mock_load:
            with patch.object(hub, '_send_relay_states', new_callable=AsyncMock) as mock_send:
                await hub.restore_last_states()
                
                mock_load.assert_not_called()
                mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_restore_last_states_no_saved_states(self, hub):
        """Test restoring last states when no saved states exist."""
        with patch.object(hub, '_load_last_states', new_callable=AsyncMock) as mock_load:
            with patch.object(hub, '_send_relay_states', new_callable=AsyncMock) as mock_send:
                # Set all states to False
                hub._relay_states = [False] * 32
                
                await hub.restore_last_states()
                
                mock_load.assert_called_once()
                mock_send.assert_not_called()  # No states to restore 