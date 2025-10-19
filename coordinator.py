import logging
from datetime import timedelta
from typing import Dict, Any, Optional, List
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class WaveshareRelayCoordinator(DataUpdateCoordinator):
    """Class to manage polling and relay state updates with improved error handling."""

    def __init__(self, hass: HomeAssistant, hub, poll_interval: int = 30):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Waveshare Relay Hub {hub._host}",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.hub = hub
        self._consecutive_failures = 0
        self._max_consecutive_failures = 3
        self._base_poll_interval = poll_interval
        self._current_poll_interval = poll_interval

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from relay hub with improved error handling."""
        try:
            # Check if hub is available
            if not self.hub.is_available:
                self._handle_failure()
                raise UpdateFailed(f"Hub {self.hub._host} is not available")
            
            # Attempt to read relay status
            states = await self.hub.read_relay_status()
            if states is None:
                self._handle_failure()
                raise UpdateFailed(f"Failed to read relay states from {self.hub._host}")
            
            # Success - reset failure count and polling interval
            self._consecutive_failures = 0
            self._current_poll_interval = self._base_poll_interval
            self.update_interval = timedelta(seconds=self._current_poll_interval)
            
            return {
                "relay_states": states,
                "connection_stats": self.hub.connection_stats,
                "last_update": self.last_update_success,
                "hub_available": True,
            }
            
        except Exception as err:
            self._handle_failure()
            _LOGGER.warning(f"Update failed for hub {self.hub._host}: {err}")
            raise UpdateFailed(f"Failed to update relay states: {err}")

    def _handle_failure(self):
        """Handle update failures with backoff strategy."""
        self._consecutive_failures += 1
        
        # Implement exponential backoff for polling interval
        if self._consecutive_failures >= self._max_consecutive_failures:
            self._current_poll_interval = min(
                self._base_poll_interval * (2 ** (self._consecutive_failures - self._max_consecutive_failures)),
                300  # Max 5 minutes
            )
            self.update_interval = timedelta(seconds=self._current_poll_interval)
            _LOGGER.warning(
                f"Hub {self.hub._host} has {self._consecutive_failures} consecutive failures, "
                f"increasing poll interval to {self._current_poll_interval}s"
            )

    async def async_set_relay_state(self, relay_number: int, state: bool) -> bool:
        """Set relay state and immediately update coordinator data."""
        try:
            success = await self.hub.set_relay_state(relay_number, state)
            if success:
                # Immediately refresh data after successful state change
                await self.async_request_refresh()
            return success
        except Exception as err:
            _LOGGER.error(f"Failed to set relay {relay_number} state: {err}")
            return False

    @property
    def hub_available(self) -> bool:
        """Return if the hub is currently available."""
        return self.hub.is_available and self._consecutive_failures < self._max_consecutive_failures

    @property
    def connection_info(self) -> Dict[str, Any]:
        """Return connection information."""
        return {
            "hub_host": self.hub._host,
            "hub_port": self.hub._port,
            "available": self.hub_available,
            "consecutive_failures": self._consecutive_failures,
            "current_poll_interval": self._current_poll_interval,
            "connection_stats": self.hub.connection_stats,
        }
