"""Switch platform for Waveshare Relay integration."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import DOMAIN
from .hub import WaveshareRelayError

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Waveshare Relay switches."""
    hub = hass.data[DOMAIN][entry.entry_id]
    device_name = entry.data.get("device_name", "waveshare")
    
    switches = [
        WaveshareRelaySwitch(hub, relay_num, device_name)
        for relay_num in range(1, hub._num_relays + 1)
    ]
    async_add_entities(switches, True)

class WaveshareRelaySwitch(SwitchEntity):
    """Representation of a Waveshare Relay switch."""

    def __init__(self, hub, relay_number: int, device_name: str) -> None:
        """Initialize the switch.
        
        Args:
            hub: The WaveshareRelayHub instance
            relay_number: The relay number (1-based index)
            device_name: The name of the device
        """
        self._hub = hub
        self._relay_number = relay_number
        self._attr_name = f"{device_name} Relay {relay_number}"
        self._attr_unique_id = f"{device_name}_relay_{relay_number}"
        self._attr_is_on = False
        self._last_update = None
        self._error_count = 0
        self._max_errors = 3

    @property
    def available(self) -> bool:
        """Return True if the switch is available."""
        return (
            self._hub.is_connected
            and self._error_count < self._max_errors
        )

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "relay_number": self._relay_number,
            "last_update": self._last_update,
            "error_count": self._error_count,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            if await self._hub.set_relay_state(self._relay_number, True):
                self._attr_is_on = True
                self._error_count = 0
                self._last_update = self._hub.last_update
                self.async_write_ha_state()
            else:
                self._error_count += 1
                _LOGGER.error("Failed to turn on relay %d", self._relay_number)
        except WaveshareRelayError as e:
            self._error_count += 1
            _LOGGER.error("Error turning on relay %d: %s", self._relay_number, e)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            if await self._hub.set_relay_state(self._relay_number, False):
                self._attr_is_on = False
                self._error_count = 0
                self._last_update = self._hub.last_update
                self.async_write_ha_state()
            else:
                self._error_count += 1
                _LOGGER.error("Failed to turn off relay %d", self._relay_number)
        except WaveshareRelayError as e:
            self._error_count += 1
            _LOGGER.error("Error turning off relay %d: %s", self._relay_number, e)

    async def async_update(self) -> None:
        """Update the switch state."""
        try:
            states = await self._hub.read_relay_status()
            if states is not None:
                self._attr_is_on = states[self._relay_number - 1]
                self._error_count = 0
                self._last_update = self._hub.last_update
                self.async_write_ha_state()
            else:
                self._error_count += 1
                _LOGGER.error("Failed to update relay %d state", self._relay_number)
        except WaveshareRelayError as e:
            self._error_count += 1
            _LOGGER.error("Error updating relay %d state: %s", self._relay_number, e)