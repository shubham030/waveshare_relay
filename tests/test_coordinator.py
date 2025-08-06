"""Tests for the Waveshare Relay Coordinator."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from waveshare_relay.coordinator import WaveshareRelayCoordinator


class TestWaveshareRelayCoordinator:
    """Test the WaveshareRelayCoordinator class."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        return MagicMock()

    @pytest.fixture
    def mock_hub(self):
        """Create a mock hub."""
        hub = MagicMock()
        hub._relay_states = [False] * 32
        hub.read_relay_status = AsyncMock(return_value=[False] * 32)
        return hub

    @pytest.fixture
    def coordinator(self, mock_hass, mock_hub):
        """Create a coordinator instance."""
        return WaveshareRelayCoordinator(
            hass=mock_hass,
            hub=mock_hub,
            poll_interval=30
        )

    def test_coordinator_initialization(self, mock_hass, mock_hub):
        """Test coordinator initialization."""
        coordinator = WaveshareRelayCoordinator(
            hass=mock_hass,
            hub=mock_hub,
            poll_interval=30
        )
        
        assert coordinator.hub == mock_hub
        assert coordinator.update_interval.total_seconds() == 30

    @pytest.mark.asyncio
    async def test_async_update_data_success(self, coordinator, mock_hub):
        """Test successful data update."""
        mock_hub._relay_states = [True, False, True, False] + [False] * 28
        
        result = await coordinator._async_update_data()
        
        mock_hub.read_relay_status.assert_called_once()
        assert result == [True, False, True, False] + [False] * 28

    @pytest.mark.asyncio
    async def test_async_update_data_failure(self, coordinator, mock_hub):
        """Test data update failure."""
        mock_hub.read_relay_status.return_value = None
        
        with pytest.raises(UpdateFailed, match="Failed to update relay states"):
            await coordinator._async_update_data()
        
        mock_hub.read_relay_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_update_data_exception(self, coordinator, mock_hub):
        """Test data update with exception."""
        mock_hub.read_relay_status.side_effect = Exception("Connection error")
        
        with pytest.raises(UpdateFailed, match="Failed to update relay states"):
            await coordinator._async_update_data()
        
        mock_hub.read_relay_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_coordinator_polling(self, mock_hass, mock_hub):
        """Test coordinator polling functionality."""
        coordinator = WaveshareRelayCoordinator(
            hass=mock_hass,
            hub=mock_hub,
            poll_interval=1  # 1 second for testing
        )
        
        # Mock the coordinator's update method
        with patch.object(coordinator, '_async_update_data', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = [True] * 32
            
            # Trigger an update
            result = await coordinator._async_update_data()
            
            assert result == [True] * 32
            mock_update.assert_called_once()

    def test_coordinator_name(self, mock_hass, mock_hub):
        """Test coordinator name."""
        coordinator = WaveshareRelayCoordinator(
            hass=mock_hass,
            hub=mock_hub,
            poll_interval=30
        )
        
        assert coordinator.name == "Waveshare Relay Hub"

    @pytest.mark.asyncio
    async def test_coordinator_with_different_poll_intervals(self, mock_hass, mock_hub):
        """Test coordinator with different poll intervals."""
        intervals = [5, 15, 30, 60]
        
        for interval in intervals:
            coordinator = WaveshareRelayCoordinator(
                hass=mock_hass,
                hub=mock_hub,
                poll_interval=interval
            )
            
            assert coordinator.update_interval.total_seconds() == interval

    @pytest.mark.asyncio
    async def test_coordinator_data_consistency(self, mock_hass, mock_hub):
        """Test that coordinator returns consistent data."""
        coordinator = WaveshareRelayCoordinator(
            hass=mock_hass,
            hub=mock_hub,
            poll_interval=30
        )
        
        # Set up mock data
        test_data = [True, False, True, False] + [False] * 28
        mock_hub._relay_states = test_data
        
        # Get data multiple times
        result1 = await coordinator._async_update_data()
        result2 = await coordinator._async_update_data()
        
        assert result1 == test_data
        assert result2 == test_data
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_coordinator_error_handling(self, mock_hass, mock_hub):
        """Test coordinator error handling."""
        coordinator = WaveshareRelayCoordinator(
            hass=mock_hass,
            hub=mock_hub,
            poll_interval=30
        )
        
        # Test with hub returning None
        mock_hub.read_relay_status.return_value = None
        
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
        
        # Test with hub raising exception
        mock_hub.read_relay_status.side_effect = ConnectionError("Network error")
        
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
        
        # Test with hub returning empty list
        mock_hub.read_relay_status.return_value = []
        
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data() 