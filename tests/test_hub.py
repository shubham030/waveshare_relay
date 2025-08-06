"""Tests for the Waveshare Relay Hub."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from waveshare_relay.hub import WaveshareRelayHub
from waveshare_relay.const import (
    CONF_LIGHTS,
    CONF_SWITCHES,
    CONF_NAME,
    CONF_ADDRESS,
)


class TestWaveshareRelayHub:
    """Test the WaveshareRelayHub class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return {
            "host": "192.168.1.100",
            "port": 502,
            "device_address": 0x01,
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

    @pytest.mark.asyncio
    async def test_hub_initialization(self, config):
        """Test hub initialization."""
        hub = WaveshareRelayHub(config)
        
        assert hub._host == "192.168.1.100"
        assert hub._port == 502
        assert hub._device_address == 0x01
        assert hub._timeout == 5
        assert hub._num_relays == 32
        assert hub._byte_size == 4  # (32 + 7) // 8
        assert hub._configured_relays == {1, 2, 3, 4}
        assert len(hub._relay_states) == 32
        assert all(not state for state in hub._relay_states)

    @pytest.mark.asyncio
    async def test_hub_create_factory_method(self, config):
        """Test the create factory method."""
        with patch.object(WaveshareRelayHub, 'read_relay_status', new_callable=AsyncMock) as mock_read:
            hub = await WaveshareRelayHub.create(config)
            
            assert isinstance(hub, WaveshareRelayHub)
            mock_read.assert_called_once()

    def test_get_configured_relays(self, config):
        """Test getting configured relays."""
        hub = WaveshareRelayHub(config)
        configured = hub._get_configured_relays(config)
        
        assert configured == {1, 2, 3, 4}

    def test_get_configured_relays_empty(self):
        """Test getting configured relays with empty config."""
        config = {
            "host": "192.168.1.100",
            "port": 502,
            "num_relays": 32,
        }
        hub = WaveshareRelayHub(config)
        configured = hub._get_configured_relays(config)
        
        assert configured == set()

    @pytest.mark.asyncio
    async def test_set_relay_state_valid(self, config):
        """Test setting a valid relay state."""
        hub = WaveshareRelayHub(config)
        
        with patch.object(hub, '_send_relay_states', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            result = await hub.set_relay_state(1, True)
            
            assert result is True
            assert hub._relay_states[0] is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_relay_state_invalid_number(self, config):
        """Test setting relay state with invalid relay number."""
        hub = WaveshareRelayHub(config)
        
        result = await hub.set_relay_state(0, True)
        assert result is False
        
        result = await hub.set_relay_state(33, True)
        assert result is False

    @pytest.mark.asyncio
    async def test_set_relay_state_not_configured(self, config):
        """Test setting relay state for non-configured relay."""
        hub = WaveshareRelayHub(config)
        
        result = await hub.set_relay_state(10, True)
        assert result is False

    @pytest.mark.asyncio
    async def test_set_relay_state_send_failure(self, config):
        """Test setting relay state when send fails."""
        hub = WaveshareRelayHub(config)
        
        with patch.object(hub, '_send_relay_states', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None
            
            result = await hub.set_relay_state(1, True)
            
            assert result is False
            assert hub._relay_states[0] is True  # State should still be updated

    @pytest.mark.asyncio
    async def test_send_relay_states(self, config):
        """Test sending relay states."""
        hub = WaveshareRelayHub(config)
        hub._relay_states[0] = True  # Set relay 1 to on
        hub._relay_states[2] = True  # Set relay 3 to on
        
        with patch.object(hub, 'send_command', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = bytes([0x01, 0x0F, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00])
            
            result = await hub._send_relay_states()
            
            assert result is not None
            mock_send.assert_called_once()
            
            # Check that the command was built correctly
            call_args = mock_send.call_args[0][0]
            assert len(call_args) >= 7  # Basic command structure
            assert call_args[0] == 0x01  # Device address
            assert call_args[1] == 0x0F  # Function code

    @pytest.mark.asyncio
    async def test_send_command_success(self, config):
        """Test successful command sending."""
        hub = WaveshareRelayHub(config)
        test_command = bytes([0x01, 0x01, 0x00, 0x00, 0x00, 0x20])
        
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            reader = AsyncMock()
            writer = MagicMock()
            writer.write = MagicMock()
            writer.drain = AsyncMock()
            writer.close = MagicMock()
            writer.wait_closed = AsyncMock()
            mock_conn.return_value = (reader, writer)
            
            reader.read.return_value = bytes([0x01, 0x01, 0x04, 0x00, 0x00, 0x00, 0x00])
            
            result = await hub.send_command(test_command)
            
            assert result is not None
            writer.write.assert_called_once_with(test_command)
            writer.drain.assert_called_once()
            writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_timeout(self, config):
        """Test command sending with timeout."""
        hub = WaveshareRelayHub(config)
        test_command = bytes([0x01, 0x01, 0x00, 0x00, 0x00, 0x20])
        
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.side_effect = asyncio.TimeoutError()
            
            result = await hub.send_command(test_command)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_send_command_connection_error(self, config):
        """Test command sending with connection error."""
        hub = WaveshareRelayHub(config)
        test_command = bytes([0x01, 0x01, 0x00, 0x00, 0x00, 0x20])
        
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.side_effect = ConnectionError()
            
            result = await hub.send_command(test_command)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_read_relay_status_success(self, config):
        """Test successful relay status reading."""
        hub = WaveshareRelayHub(config)
        
        # Mock response: relays 24 and 26 on (0x05 = 00000101 in binary, reversed)
        mock_response = bytes([0x01, 0x01, 0x04, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00])
        
        with patch.object(hub, 'send_command', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = mock_response
            
            result = await hub.read_relay_status()
            
            assert result is not None
            assert len(result) == 32
            # Check that some relays are on (based on the debug output)
            assert any(result)  # At least one relay should be on
            # Check that the function returns the expected structure
            assert isinstance(result, list)
            assert all(isinstance(relay_state, bool) for relay_state in result)

    @pytest.mark.asyncio
    async def test_read_relay_status_invalid_response(self, config):
        """Test relay status reading with invalid response."""
        hub = WaveshareRelayHub(config)
        
        with patch.object(hub, 'send_command', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = bytes([0x01, 0x01])  # Too short
            
            result = await hub.read_relay_status()
            
            assert result is None

    @pytest.mark.asyncio
    async def test_read_relay_status_no_response(self, config):
        """Test relay status reading with no response."""
        hub = WaveshareRelayHub(config)
        
        with patch.object(hub, 'send_command', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None
            
            result = await hub.read_relay_status()
            
            assert result is None

    def test_calculate_crc(self, config):
        """Test CRC calculation."""
        hub = WaveshareRelayHub(config)
        
        # Test data: [0x01, 0x01, 0x00, 0x00, 0x00, 0x20]
        test_data = bytes([0x01, 0x01, 0x00, 0x00, 0x00, 0x20])
        crc = hub.calculate_crc(test_data)
        
        assert len(crc) == 2
        assert isinstance(crc, bytes)

    def test_calculate_crc_empty(self, config):
        """Test CRC calculation with empty data."""
        hub = WaveshareRelayHub(config)
        
        crc = hub.calculate_crc(bytes())
        
        assert len(crc) == 2
        assert crc == bytes([0xFF, 0xFF])  # Initial CRC value 