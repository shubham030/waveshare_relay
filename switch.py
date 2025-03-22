"""Support for Waveshare Relay switches."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DEVICE_NAME,
    CONF_NUM_RELAYS,
    CONF_RELAY_NAMES,
    DOMAIN,
)
from .hub import WaveshareRelayHub

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Waveshare Relay switches from a config entry."""
    hub: WaveshareRelayHub = hass.data[DOMAIN][config_entry.entry_id]
    
    # Get configuration
    device_name = config_entry.data[CONF_DEVICE_NAME]
    num_relays = config_entry.data[CONF_NUM_RELAYS]
    relay_names = config_entry.data.get(CONF_RELAY_NAMES, {})

    # Create switches
    switches = []
    for relay_num in range(1, num_relays + 1):
        relay_name = relay_names.get(str(relay_num), f"{device_name} Relay {relay_num}")
        switches.append(WaveshareRelaySwitch(hub, device_name, relay_num, relay_name, bool(str(relay_num) in relay_names)))

    async_add_entities(switches, True)

class WaveshareRelaySwitch(SwitchEntity):
    """Representation of a Waveshare Relay switch."""

    def __init__(
        self,
        hub: WaveshareRelayHub,
        device_name: str,
        relay_num: int,
        relay_name: str,
        is_mapped: bool,
    ) -> None:
        """Initialize the switch."""
        self._hub = hub
        self._device_name = device_name
        self._relay_num = relay_num
        self._name = relay_name
        self._state = False
        
        # Generate unique ID and entity ID
        sanitized_device = device_name.lower().replace(' ', '_')
        if is_mapped:
            # For mapped relays, use the custom name in the entity ID
            sanitized_name = relay_name.lower().replace(' ', '_')
            self._attr_unique_id = f"{sanitized_device}_{sanitized_name}"
            self.entity_id = f"switch.{sanitized_device}_{sanitized_name}"
        else:
            # For unmapped relays, use the relay number
            self._attr_unique_id = f"{sanitized_device}_relay_{relay_num}"
            self.entity_id = f"switch.{sanitized_device}_relay_{relay_num}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._device_name)},
            "name": self._device_name,
            "manufacturer": "Waveshare",
            "model": "Relay Module",
        }

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            if await self._hub.set_relay_state(self._relay_num, True):
                self._state = True
        except Exception as err:
            _LOGGER.error("Error turning on relay %d: %s", self._relay_num, err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            if await self._hub.set_relay_state(self._relay_num, False):
                self._state = False
        except Exception as err:
            _LOGGER.error("Error turning off relay %d: %s", self._relay_num, err)
            raise

    async def async_update(self) -> None:
        """Update the switch state."""
        try:
            states = await self._hub.read_relay_status()
            if states is not None:
                self._state = states[self._relay_num - 1]
        except Exception as err:
            _LOGGER.error("Error updating relay %d: %s", self._relay_num, err)