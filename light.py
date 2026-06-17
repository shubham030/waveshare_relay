"""The Waveshare Relay Light platform."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, CONF_LIGHTS, CONF_NAME, CONF_ADDRESS

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[Dict[str, Any]] = None,
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
        # Use address-based unique_id for stability across config changes
        # Format: {host}_{port}_{device_address}_{relay_address}_light
        device_address = config.get("device_address", 1)
        unique_id = f"{hub._host}_{hub._port}_{device_address}_{light_config[CONF_ADDRESS]}_light"
        _LOGGER.debug("Generated unique_id: %s", unique_id)
        entities.append(
            WaveshareRelayLight(
                hub=hub,
                name=light_config[CONF_NAME],
                address=light_config[CONF_ADDRESS],
                unique_id=unique_id,
                coordinator=None  # YAML setup doesn't use coordinator
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
        # Use address-based unique_id for stability across config changes
        # Format: {host}_{port}_{device_address}_{relay_address}_light
        device_address = config.get("device_address", 1)
        unique_id = f"{hub._host}_{hub._port}_{device_address}_{light_config[CONF_ADDRESS]}_light"
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
    async_add_entities(entities, False)  # False because coordinator handles updates


class WaveshareRelayLight(RestoreEntity, LightEntity):
    """Representation of a Waveshare Relay Light with improved reliability."""
    
    # Use proper entity naming in HA
    has_entity_name = True
    
    # ColorMode support for on/off lights
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}
    
    def __init__(
        self,
        hub,
        name: str,
        address: int,
        unique_id: str,
        coordinator: Optional[DataUpdateCoordinator] = None
    ) -> None:
        """Initialize the light."""
        super().__init__()
        
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._address = address
        self._attr_is_on = False
        self.coordinator = coordinator  # Use public attribute for CoordinatorEntity compatibility
        self._last_command_success = True
        self._command_retries = 0
        self._max_retries = 3
        _LOGGER.debug("Initialized light entity: %s (address: %d)", name, address)

    @property
    def should_poll(self) -> bool:
        """Return if polling is needed.
        
        When using coordinator, polling is handled by the coordinator.
        For YAML setup (no coordinator), manual polling is needed.
        """
        return self.coordinator is None

    @property
    def device_info(self) -> Dict[str, Any]:
        """Link the entity to its board's device (created in __init__)."""
        return {
            "identifiers": {
                (DOMAIN, f"{self._hub._host}_{self._hub._port}_{self._hub._device_address}")
            },
        }

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        if self.coordinator is not None:
            # Check both coordinator availability and hub availability
            if not self.coordinator.last_update_success:
                return False
            return self.coordinator.hub_available
        return self._hub.is_available

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
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

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant.
        
        Restores previous state and registers coordinator listener.
        """
        await super().async_added_to_hass()
        
        # Restore previous state
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
            _LOGGER.debug(
                "Restored state for %s: is_on=%s", 
                self._attr_name, 
                self._attr_is_on
            )
        
        # If we have a coordinator, register for updates and sync with current data
        if self.coordinator is not None:
            self.async_on_remove(
                self.coordinator.async_add_listener(self._handle_coordinator_update)
            )
            if self.coordinator.data:
                self._handle_coordinator_update()

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal from Home Assistant.
        
        Cleanup any resources.
        """
        await super().async_will_remove_from_hass()
        _LOGGER.debug("Removing light entity: %s", self._attr_name)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator is None or self.coordinator.data is None:
            return
            
        relay_states = self.coordinator.data.get("relay_states", [])
        if len(relay_states) >= self._address:
            new_state = relay_states[self._address - 1]
            if self._attr_is_on != new_state:
                self._attr_is_on = new_state
                _LOGGER.debug(
                    "Light state updated from coordinator: %s (is_on: %s)", 
                    self._attr_name, 
                    self._attr_is_on
                )
        
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on with retry logic."""
        _LOGGER.debug("Turning on light: %s", self._attr_name)
        
        success = await self._execute_command(True)
        if success:
            self._attr_is_on = True
            _LOGGER.debug("Light turned on: %s", self._attr_name)
        else:
            _LOGGER.error("Failed to turn on light after retries: %s", self._attr_name)
            
        self.async_write_ha_state()
        
        # Request coordinator refresh to sync state
        if self.coordinator is not None:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off with retry logic."""
        _LOGGER.debug("Turning off light: %s", self._attr_name)
        
        success = await self._execute_command(False)
        if success:
            self._attr_is_on = False
            _LOGGER.debug("Light turned off: %s", self._attr_name)
        else:
            _LOGGER.error("Failed to turn off light after retries: %s", self._attr_name)
            
        self.async_write_ha_state()
        
        # Request coordinator refresh to sync state
        if self.coordinator is not None:
            await self.coordinator.async_request_refresh()

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
                            "Command failed for %s, attempt %d/%d",
                            self._attr_name,
                            attempt + 1,
                            self._max_retries
                        )
                        
            except Exception as e:
                self._command_retries = attempt + 1
                _LOGGER.warning("Exception during command for %s: %s", self._attr_name, e)
                
        self._last_command_success = False
        return False

    async def _verify_state(self, expected_state: bool) -> None:
        """Verify the actual state matches expected state."""
        try:
            actual_states = await self._hub.read_relay_status()
            if actual_states and len(actual_states) >= self._address:
                actual_state = actual_states[self._address - 1]
                if actual_state != expected_state:
                    _LOGGER.warning(
                        "State mismatch for %s: expected %s, got %s",
                        self._attr_name,
                        expected_state,
                        actual_state
                    )
        except Exception as e:
            _LOGGER.debug("Could not verify state for %s: %s", self._attr_name, e)

    async def async_update(self) -> None:
        """Update the light state (only used for YAML setup without coordinator)."""
        # Skip if using coordinator - it handles updates
        if self.coordinator is not None:
            return
            
        _LOGGER.debug("Updating light state: %s", self._attr_name)
        
        try:
            # Direct hub polling for YAML setup
            await self._hub.read_relay_status()
            if len(self._hub._relay_states) >= self._address:
                self._attr_is_on = self._hub._relay_states[self._address - 1]
                _LOGGER.debug(
                    "Light state updated from hub: %s (is_on: %s)", 
                    self._attr_name, 
                    self._attr_is_on
                )
        except Exception as e:
            _LOGGER.warning("Failed to update state for %s: %s", self._attr_name, e)
