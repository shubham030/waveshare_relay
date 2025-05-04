"""The Waveshare Relay Switch platform."""
import logging
from typing import Any, Dict

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.discovery import async_load_platform

from custom_components.waveshare_relay import DOMAIN
from custom_components.waveshare_relay.const import CONF_SWITCHES, CONF_NAME, CONF_ADDRESS

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: Dict[str, Any] = None,
) -> None:
    """Set up the Waveshare Relay switch platform from YAML."""
    if discovery_info is None:
        return

    _LOGGER.debug("Setting up Waveshare Relay switch platform from YAML")
    entry_id = discovery_info["entry_id"]
    config = discovery_info["config"]
    hub = hass.data[DOMAIN][entry_id]
    
    _LOGGER.debug("Relay config: %s", config)
    _LOGGER.debug("Relay name from config: %s", config.get(CONF_NAME))
    
    entities = []
    
    # Add switches
    for switch_config in config.get(CONF_SWITCHES, []):
        _LOGGER.debug("Adding switch entity: %s", switch_config[CONF_NAME])
        # Use the relay name from the parent config
        relay_name = config[CONF_NAME]
        unique_id = f"{relay_name}_{switch_config[CONF_NAME].lower().replace(' ', '_')}"
        _LOGGER.debug("Generated unique_id: %s", unique_id)
        entities.append(
            WaveshareRelaySwitch(
                hub=hub,
                name=switch_config[CONF_NAME],
                address=switch_config[CONF_ADDRESS],
                unique_id=unique_id
            )
        )
    
    _LOGGER.debug("Adding %d switch entities", len(entities))
    async_add_entities(entities, True)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Waveshare Relay switch entities from config entry."""
    _LOGGER.debug("Setting up Waveshare Relay switch platform from config entry")
    hub = hass.data[DOMAIN][entry.entry_id]
    config = entry.data
    
    _LOGGER.debug("Config entry data: %s", config)
    _LOGGER.debug("Relay name from config entry: %s", config.get(CONF_NAME))
    
    entities = []
    
    # Add switches
    for switch_config in config.get(CONF_SWITCHES, []):
        _LOGGER.debug("Adding switch entity: %s", switch_config[CONF_NAME])
        # Use the relay name from the parent config
        relay_name = config[CONF_NAME]
        unique_id = f"{relay_name}_{switch_config[CONF_NAME].lower().replace(' ', '_')}"
        _LOGGER.debug("Generated unique_id: %s", unique_id)
        entities.append(
            WaveshareRelaySwitch(
                hub=hub,
                name=switch_config[CONF_NAME],
                address=switch_config[CONF_ADDRESS],
                unique_id=unique_id
            )
        )
    
    _LOGGER.debug("Adding %d switch entities", len(entities))
    async_add_entities(entities, True)

class WaveshareRelaySwitch(SwitchEntity):
    """Representation of a Waveshare Relay Switch."""
    
    def __init__(self, hub, name, address, unique_id):
        """Initialize the switch."""
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._address = address
        self._attr_is_on = False
        _LOGGER.debug("Initialized switch entity: %s (address: %d)", name, address)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        _LOGGER.debug("Turning on switch: %s", self._attr_name)
        if await self._hub.set_relay_state(self._address, True):
            self._attr_is_on = True
            self.async_write_ha_state()
            _LOGGER.debug("Switch turned on: %s", self._attr_name)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        _LOGGER.debug("Turning off switch: %s", self._attr_name)
        if await self._hub.set_relay_state(self._address, False):
            self._attr_is_on = False
            self.async_write_ha_state()
            _LOGGER.debug("Switch turned off: %s", self._attr_name)

    async def async_update(self):
        """Update the switch state."""
        _LOGGER.debug("Updating switch state: %s", self._attr_name)
        await self._hub.read_relay_status()
        self._attr_is_on = self._hub._relay_states[self._address - 1]
        _LOGGER.debug("Switch state updated: %s (is_on: %s)", self._attr_name, self._attr_is_on) 