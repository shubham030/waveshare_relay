"""The Waveshare Relay Switch platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, CONF_SWITCHES, CONF_NAME, CONF_ADDRESS

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
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
        # Include host and port in unique_id to prevent collisions
        unique_id = f"{hub._host}_{hub._port}_{relay_name}_{switch_config[CONF_NAME].lower().replace(' ', '_')}"
        _LOGGER.debug("Generated unique_id: %s", unique_id)
        entities.append(
            WaveshareRelaySwitch(
                hub=hub,
                name=switch_config[CONF_NAME],
                address=switch_config[CONF_ADDRESS],
                unique_id=unique_id,
                coordinator=None,  # YAML setup doesn't use coordinator
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
    entry_data = hass.data[DOMAIN][entry.entry_id]
    hub = entry_data["hub"]
    coordinator = entry_data["coordinator"]
    config = entry.data

    _LOGGER.debug("Config entry data: %s", config)
    _LOGGER.debug("Relay name from config entry: %s", config.get(CONF_NAME))

    entities = []

    # Add switches
    for switch_config in config.get(CONF_SWITCHES, []):
        _LOGGER.debug("Adding switch entity: %s", switch_config[CONF_NAME])
        # Use the relay name from the parent config
        relay_name = config[CONF_NAME]
        # Include host and port in unique_id to prevent collisions
        unique_id = f"{hub._host}_{hub._port}_{relay_name}_{switch_config[CONF_NAME].lower().replace(' ', '_')}"
        _LOGGER.debug("Generated unique_id: %s", unique_id)
        entities.append(
            WaveshareRelaySwitch(
                hub=hub,
                name=switch_config[CONF_NAME],
                address=switch_config[CONF_ADDRESS],
                unique_id=unique_id,
                coordinator=coordinator,
            )
        )

    _LOGGER.debug("Adding %d switch entities", len(entities))
    async_add_entities(entities, True)


class WaveshareRelaySwitch(RestoreEntity, SwitchEntity):
    """Representation of a Waveshare Relay Switch with improved reliability."""

    # Use coordinator for polling when available
    _attr_has_entity_name = True

    def __init__(
        self,
        hub,
        name: str,
        address: int,
        unique_id: str,
        coordinator: DataUpdateCoordinator | None = None,
    ) -> None:
        """Initialize the switch."""
        super().__init__()

        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._address = address
        self._attr_is_on = False
        self.coordinator = coordinator  # Use public attribute for compatibility
        self._last_command_success = True
        self._command_retries = 0
        self._max_retries = 3
        _LOGGER.debug("Initialized switch entity: %s (address: %d)", name, address)

    @property
    def should_poll(self) -> bool:
        """Return False if coordinator handles updates, True otherwise."""
        return self.coordinator is None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information to link entity to a device."""
        return {
            "identifiers": {(DOMAIN, f"{self._hub._host}_{self._hub._port}")},
            "name": f"Waveshare Relay {self._hub._host}",
            "manufacturer": "Waveshare",
            "model": "Modbus RTU Relay",
        }

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        if self.coordinator is not None:
            # Check both coordinator availability and hub availability
            if not self.coordinator.last_update_success:
                return False
            return getattr(self.coordinator, 'hub_available', self._hub.is_available)
        return self._hub.is_available

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
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
        """Handle entity which will be added to hass."""
        await super().async_added_to_hass()

        # Restore previous state
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == "on"
            _LOGGER.debug(
                "Restored state for %s: %s", self._attr_name, self._attr_is_on
            )

        # If using coordinator, register for updates
        if self.coordinator is not None:
            self.async_on_remove(
                self.coordinator.async_add_listener(self._handle_coordinator_update)
            )
            if self.coordinator.data:
                self._handle_coordinator_update()

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal from hass."""
        await super().async_will_remove_from_hass()
        _LOGGER.debug("Removing switch entity: %s", self._attr_name)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator is None or self.coordinator.data is None:
            return

        relay_states = self.coordinator.data.get("relay_states", [])
        if len(relay_states) >= self._address:
            new_state = relay_states[self._address - 1]
            if new_state != self._attr_is_on:
                self._attr_is_on = new_state
                _LOGGER.debug(
                    "Switch state updated from coordinator: %s (is_on: %s)",
                    self._attr_name,
                    self._attr_is_on,
                )

        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on with retry logic."""
        _LOGGER.debug("Turning on switch: %s", self._attr_name)

        success = await self._execute_command(True)
        if success:
            self._attr_is_on = True
            _LOGGER.debug("Switch turned on: %s", self._attr_name)
        else:
            _LOGGER.error("Failed to turn on switch after retries: %s", self._attr_name)

        self.async_write_ha_state()

        # Request coordinator refresh if available
        if self.coordinator is not None:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off with retry logic."""
        _LOGGER.debug("Turning off switch: %s", self._attr_name)

        success = await self._execute_command(False)
        if success:
            self._attr_is_on = False
            _LOGGER.debug("Switch turned off: %s", self._attr_name)
        else:
            _LOGGER.error("Failed to turn off switch after retries: %s", self._attr_name)

        self.async_write_ha_state()

        # Request coordinator refresh if available
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
                            self._max_retries,
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
                        actual_state,
                    )
        except Exception as e:
            _LOGGER.debug("Could not verify state for %s: %s", self._attr_name, e)

    async def async_update(self) -> None:
        """Update the switch state (only used when coordinator is None)."""
        # Skip if using coordinator - it handles updates
        if self.coordinator is not None:
            return

        _LOGGER.debug("Updating switch state: %s", self._attr_name)

        try:
            # Direct hub polling for YAML setup
            await self._hub.read_relay_status()
            if len(self._hub._relay_states) >= self._address:
                self._attr_is_on = self._hub._relay_states[self._address - 1]
                _LOGGER.debug(
                    "Switch state updated from hub: %s (is_on: %s)",
                    self._attr_name,
                    self._attr_is_on,
                )
        except Exception as e:
            _LOGGER.warning("Failed to update state for %s: %s", self._attr_name, e)
