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
    entry_data = hass.data[DOMAIN][entry.entry_id]
    hub = entry_data["hub"]
    coordinator = entry_data["coordinator"]
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
                unique_id=unique_id,
                coordinator=coordinator
            )
        )
    
    _LOGGER.debug("Adding %d light entities", len(entities))
    async_add_entities(entities, True)

class WaveshareRelayLight(LightEntity):
    """Representation of a Waveshare Relay Light with improved reliability."""
    
    def __init__(self, hub, name, address, unique_id, coordinator=None):
        """Initialize the light."""
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._address = address
        self._attr_is_on = False
        self._coordinator = coordinator
        self._last_command_success = True
        self._command_retries = 0
        self._max_retries = 3
        _LOGGER.debug("Initialized light entity: %s (address: %d)", name, address)

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        if self._coordinator:
            return self._coordinator.hub_available
        return self._hub.is_available

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attrs = {
            "address": self._address,
            "last_command_success": self._last_command_success,
            "command_retries": self._command_retries,
        }
        
        if self._hub:
            attrs.update({
                "hub_host": self._hub._host,
                "hub_available": self._hub.is_available,
            })
            
        return attrs

    async def async_turn_on(self, **kwargs):
        """Turn the light on with retry logic."""
        _LOGGER.debug("Turning on light: %s", self._attr_name)
        
        success = await self._execute_command(True)
        if success:
            self._attr_is_on = True
            _LOGGER.debug("Light turned on: %s", self._attr_name)
        else:
            _LOGGER.error("Failed to turn on light after retries: %s", self._attr_name)
            
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off with retry logic."""
        _LOGGER.debug("Turning off light: %s", self._attr_name)
        
        success = await self._execute_command(False)
        if success:
            self._attr_is_on = False
            _LOGGER.debug("Light turned off: %s", self._attr_name)
        else:
            _LOGGER.error("Failed to turn off light after retries: %s", self._attr_name)
            
        self.async_write_ha_state()

    async def _execute_command(self, target_state: bool) -> bool:
        """Execute command with retry logic."""
        self._command_retries = 0
        
        for attempt in range(self._max_retries):
            try:
                success = await self._hub.set_relay_state(self._address, target_state)
                if success:
                    self._last_command_success = True
                    self._command_retries = attempt
                    
                    # Verify state if possible
                    if attempt == 0:  # Only verify on first attempt to avoid excessive polling
                        await self._verify_state(target_state)
                    
                    return True
                else:
                    self._command_retries = attempt + 1
                    if attempt < self._max_retries - 1:
                        _LOGGER.warning(
                            f"Command failed for {self._attr_name}, attempt {attempt + 1}/{self._max_retries}"
                        )
                        
            except Exception as e:
                self._command_retries = attempt + 1
                _LOGGER.warning(f"Exception during command for {self._attr_name}: {e}")
                
        self._last_command_success = False
        return False

    async def _verify_state(self, expected_state: bool):
        """Verify the actual state matches expected state."""
        try:
            actual_states = await self._hub.read_relay_status()
            if actual_states and len(actual_states) >= self._address:
                actual_state = actual_states[self._address - 1]
                if actual_state != expected_state:
                    _LOGGER.warning(
                        f"State mismatch for {self._attr_name}: expected {expected_state}, got {actual_state}"
                    )
        except Exception as e:
            _LOGGER.debug(f"Could not verify state for {self._attr_name}: {e}")

    async def async_update(self):
        """Update the light state from coordinator or hub."""
        _LOGGER.debug("Updating light state: %s", self._attr_name)
        
        try:
            if self._coordinator and self._coordinator.data:
                # Use coordinator data if available
                relay_states = self._coordinator.data.get("relay_states", [])
                if len(relay_states) >= self._address:
                    self._attr_is_on = relay_states[self._address - 1]
                    _LOGGER.debug("Light state updated from coordinator: %s (is_on: %s)", 
                                self._attr_name, self._attr_is_on)
                    return
                    
            # Fallback to direct hub polling
            await self._hub.read_relay_status()
            if len(self._hub._relay_states) >= self._address:
                self._attr_is_on = self._hub._relay_states[self._address - 1]
                _LOGGER.debug("Light state updated from hub: %s (is_on: %s)", 
                            self._attr_name, self._attr_is_on)
        except Exception as e:
            _LOGGER.warning(f"Failed to update state for {self._attr_name}: {e}") 