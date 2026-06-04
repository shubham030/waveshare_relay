"""The Waveshare Relay integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_DEVICE_ADDRESS,
    CONF_TIMEOUT,
    CONF_LIGHTS,
    CONF_SWITCHES,
    CONF_ADDRESS,
    CONF_RESTORE_STATE,
    DEFAULT_PORT,
    DEFAULT_DEVICE_ADDRESS,
    DEFAULT_TIMEOUT,
    DEFAULT_RESTORE_STATE,
)
from .hub import WaveshareRelayHub
from .coordinator import WaveshareRelayCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light", "switch"]

# Config entry version - increment when making breaking changes to config schema
CONFIG_ENTRY_VERSION = 2

# YAML configuration schema for a single relay module
RELAY_MODULE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_DEVICE_ADDRESS, default=DEFAULT_DEVICE_ADDRESS): cv.positive_int,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional("num_relays", default=32): vol.All(cv.positive_int, vol.Range(min=1, max=32)),
        vol.Optional(CONF_RESTORE_STATE, default=DEFAULT_RESTORE_STATE): cv.boolean,
        vol.Optional(CONF_LIGHTS, default=[]): [
            vol.Schema(
                {
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_ADDRESS): vol.All(cv.positive_int, vol.Range(min=1, max=32)),
                }
            )
        ],
        vol.Optional(CONF_SWITCHES, default=[]): [
            vol.Schema(
                {
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_ADDRESS): vol.All(cv.positive_int, vol.Range(min=1, max=32)),
                }
            )
        ],
    }
)

# YAML configuration schema for the entire integration
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [RELAY_MODULE_SCHEMA]
        )
    },
    extra=vol.ALLOW_EXTRA  # Allow other configuration sections
)

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up Waveshare Relay from YAML by importing each board to a config entry.

    The YAML ``waveshare_relay:`` list stays the source of truth (bulk-friendly
    for many channels), but each board is imported into its own config entry so
    it becomes a proper device with its lights/switches nested under it — the way
    config-entry integrations (ESPHome, etc.) group their entities. Re-imports on
    restart update the existing entry rather than creating duplicates.
    """
    if DOMAIN not in config:
        return True

    try:
        boards = CONFIG_SCHEMA(config)[DOMAIN]
    except vol.Invalid as err:
        _LOGGER.error("Invalid configuration: %s", err)
        return False

    hass.data.setdefault(DOMAIN, {})
    for board in boards:
        _LOGGER.debug("Importing Waveshare Relay board from YAML: %s", board.get(CONF_NAME))
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(board)
            )
        )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waveshare Relay from a config entry."""
    # Create the hub and ensure it's properly initialized
    hub = await WaveshareRelayHub.create(entry.data, hass)
    
    # Verify hub is available before proceeding
    if not hub.is_available:
        _LOGGER.warning(
            "Hub at %s:%s is not responding, but will continue setup",
            entry.data.get(CONF_HOST),
            entry.data.get(CONF_PORT),
        )
    
    # Create coordinator for this hub
    coordinator = WaveshareRelayCoordinator(
        hass, 
        hub, 
        poll_interval=entry.options.get("poll_interval", entry.data.get("poll_interval", 30))
    )
    
    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()
    
    # Store references for proper lifecycle management
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "hub": hub,
        "coordinator": coordinator,
        "entry": entry,
    }

    # Register one device per board so all its lights/switches nest under it.
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{hub._host}_{hub._port}_{hub._device_address}")},
        manufacturer="Waveshare",
        name=f"{entry.data.get(CONF_NAME, hub._host).replace('_', ' ').title()} Relay",
        model=f"Modbus RTU Relay ({entry.data.get('num_relays', 32)}ch)",
    )

    # Restore last states if enabled
    if entry.data.get(CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE):
        await hub.restore_last_states()

    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        # Clean up coordinator if it exists
        if "coordinator" in entry_data:
            coordinator = entry_data["coordinator"]
            # The coordinator will be automatically cleaned up when the entry is removed
            _LOGGER.debug("Cleaned up coordinator for entry %s", entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entry to new version.
    
    This is called when the config entry version is older than the current version.
    """
    _LOGGER.info("Migrating config entry from version %s to %s", config_entry.version, CONFIG_ENTRY_VERSION)
    
    if config_entry.version == 1:
        # Version 1 -> 2: No schema changes, just update version
        # This handles the transition to new unique_id format
        new_data = {**config_entry.data}
        
        hass.config_entries.async_update_entry(
            config_entry,
            data=new_data,
            version=CONFIG_ENTRY_VERSION,
        )
        _LOGGER.info("Migration to version %s successful", CONFIG_ENTRY_VERSION)
    
    return True