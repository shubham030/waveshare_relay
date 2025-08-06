"""The Waveshare Relay Light platform."""
import logging
from typing import Any, Dict

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.discovery import async_load_platform

from . import DOMAIN
from .const import CONF_LIGHTS, CONF_NAME, CONF_ADDRESS

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: Dict[str, Any] = None,
) -> None:
    """Set up the Waveshare Relay light platform from YAML."""
    if discovery_info is None:
        return

    _LOGGER.debug("Setting up Waveshare Relay light platform from YAML")
    entry_id = discovery_info["entry_id"]
    config = discovery_info["config"]
    hub = hass.data[DOMAIN][entry_id]
    
    _LOGGER.debug("Relay config: %s", config)
    _LOGGER.debug("Relay name from config: %s", config.get(CONF_NAME))
    
    entities = []
    
    # Add lights
    for light_config in config.get(CONF_LIGHTS, []):
        _LOGGER.debug("Adding light entity: %s", light_config[CONF_NAME])
        # Use the relay name from the parent config
        relay_name = config[CONF_NAME]
        unique_id = f"{relay_name}_{light_config[CONF_NAME].lower().replace(' ', '_')}"
        _LOGGER.debug("Generated unique_id: %s", unique_id)
        entities.append(
            WaveshareRelayLight(
                hub=hub,
                name=light_config[CONF_NAME],
                address=light_config[CONF_ADDRESS],
                unique_id=unique_id
            )
        )
    
    _LOGGER.debug("Adding %d light entities", len(entities))
    async_add_entities(entities, True)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Waveshare Relay light entities from config entry."""
    _LOGGER.debug("Setting up Waveshare Relay light platform from config entry")
    hub = hass.data[DOMAIN][entry.entry_id]
    config = entry.data
    
    _LOGGER.debug("Config entry data: %s", config)
    _LOGGER.debug("Relay name from config entry: %s", config.get(CONF_NAME))
    
    entities = []
    
    # Add lights
    for light_config in config.get(CONF_LIGHTS, []):
        _LOGGER.debug("Adding light entity: %s", light_config[CONF_NAME])
        # Use the relay name from the parent config
        relay_name = config[CONF_NAME]
        unique_id = f"{relay_name}_{light_config[CONF_NAME].lower().replace(' ', '_')}"
        _LOGGER.debug("Generated unique_id: %s", unique_id)
        entities.append(
            WaveshareRelayLight(
                hub=hub,
                name=light_config[CONF_NAME],
                address=light_config[CONF_ADDRESS],
                unique_id=unique_id
            )
        )
    
    _LOGGER.debug("Adding %d light entities", len(entities))
    async_add_entities(entities, True)

class WaveshareRelayLight(LightEntity):
    """Representation of a Waveshare Relay Light."""
    
    def __init__(self, hub, name, address, unique_id):
        """Initialize the light."""
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._address = address
        self._attr_is_on = False
        _LOGGER.debug("Initialized light entity: %s (address: %d)", name, address)

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        _LOGGER.debug("Turning on light: %s", self._attr_name)
        success = await self._hub.set_relay_state(self._address, True)
        self._attr_is_on = True
        self.async_write_ha_state()
        if success:
            _LOGGER.debug("Light turned on: %s", self._attr_name)
        else:
            _LOGGER.warning("Light turn on command failed: %s", self._attr_name)

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        _LOGGER.debug("Turning off light: %s", self._attr_name)
        success = await self._hub.set_relay_state(self._address, False)
        self._attr_is_on = False
        self.async_write_ha_state()
        if success:
            _LOGGER.debug("Light turned off: %s", self._attr_name)
        else:
            _LOGGER.warning("Light turn off command failed: %s", self._attr_name)

    async def async_update(self):
        """Update the light state."""
        _LOGGER.debug("Updating light state: %s", self._attr_name)
        await self._hub.read_relay_status()
        self._attr_is_on = self._hub._relay_states[self._address - 1]
        _LOGGER.debug("Light state updated: %s (is_on: %s)", self._attr_name, self._attr_is_on) 