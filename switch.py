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
        relay_name = relay_names.get(str(relay_num), f"Relay {relay_num}")
        switches.append(WaveshareRelaySwitch(hub, device_name, relay_num, relay_name))

    async_add_entities(switches, True)

class WaveshareRelaySwitch(SwitchEntity):
    """Representation of a Waveshare Relay switch."""

    def __init__(
        self,
        hub: WaveshareRelayHub,
        device_name: str,
        relay_num: int,
        relay_name: str,
    ) -> None:
        """Initialize the switch."""
        self._hub = hub
        self._device_name = device_name
        self._relay_num = relay_num
        self._name = relay_name
        self._state = False
        
        # Generate unique ID using relay name if present, otherwise use relay number
        id_suffix = relay_name.lower().replace(" ", "_") if relay_name != f"Relay {relay_num}" else str(relay_num)
        self._attr_unique_id = f"{device_name.lower().replace(' ', '_')}_{id_suffix}"

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
            await self._hub.set_relay(self._relay_num, True)
            self._state = True
        except Exception as err:
            _LOGGER.error("Error turning on relay %d: %s", self._relay_num, err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self._hub.set_relay(self._relay_num, False)
            self._state = False
        except Exception as err:
            _LOGGER.error("Error turning off relay %d: %s", self._relay_num, err)
            raise

    async def async_update(self) -> None:
        """Update the switch state."""
        try:
            self._state = await self._hub.read_relay(self._relay_num)
        except Exception as err:
            _LOGGER.error("Error updating relay %d: %s", self._relay_num, err)