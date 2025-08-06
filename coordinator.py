import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class WaveshareRelayCoordinator(DataUpdateCoordinator):
    """Class to manage polling and relay state updates."""

    def __init__(self, hass, hub, poll_interval):
        super().__init__(
            hass,
            _LOGGER,
            name="Waveshare Relay Hub",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.hub = hub

    async def _async_update_data(self):
        """Fetch data from relay hub."""
        try:
            if not await self.hub.read_relay_status():
                raise UpdateFailed("Failed to update relay states")
            return self.hub._relay_states
        except Exception as err:
            raise UpdateFailed(f"Failed to update relay states: {err}")
