"""The Waveshare Relay integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.discovery import async_load_platform

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
_LOGGER.setLevel(logging.DEBUG)

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
    """Set up the Waveshare Relay component from YAML."""
    if DOMAIN not in config:
        return True

    try:
        # Validate only our section
        config[DOMAIN] = CONFIG_SCHEMA(config)[DOMAIN]
    except vol.Invalid as err:
        _LOGGER.error("Invalid configuration: %s", err)
        return False

    # Set up each relay hub from YAML
    hass.data.setdefault(DOMAIN, {})
    for entry_config in config[DOMAIN]:
        _LOGGER.debug("Setting up Waveshare Relay hub: %s", entry_config[CONF_NAME])
        hub = await WaveshareRelayHub.create(entry_config, hass)
        entry_id = f"{entry_config[CONF_HOST]}_{entry_config[CONF_NAME]}"
        hass.data[DOMAIN][entry_id] = hub

        # Restore last states if enabled
        if entry_config.get(CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE):
            await hub.restore_last_states()

        # Load platforms for this hub
        _LOGGER.debug("Loading light platform for hub: %s", entry_config[CONF_NAME])
        _LOGGER.debug("Light platform config: %s", {"entry_id": entry_id, "config": entry_config})
        hass.async_create_task(
            async_load_platform(
                hass,
                "light",
                DOMAIN,
                {"entry_id": entry_id, "config": entry_config},
                config,
            )
        )
        _LOGGER.debug("Loading switch platform for hub: %s", entry_config[CONF_NAME])
        _LOGGER.debug("Switch platform config: %s", {"entry_id": entry_id, "config": entry_config})
        hass.async_create_task(
            async_load_platform(
                hass,
                "switch",
                DOMAIN,
                {"entry_id": entry_id, "config": entry_config},
                config,
            )
        )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waveshare Relay from a config entry."""
    hub = await WaveshareRelayHub.create(entry.data, hass)
    
    # Create coordinator for this hub
    coordinator = WaveshareRelayCoordinator(
        hass, 
        hub, 
        poll_interval=entry.data.get("poll_interval", 30)
    )
    
    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "hub": hub,
        "coordinator": coordinator,
    }

    # Restore last states if enabled
    if entry.data.get(CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE):
        await hub.restore_last_states()

    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["light", "switch"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["light", "switch"])
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        # Clean up coordinator if it exists
        if "coordinator" in entry_data:
            coordinator = entry_data["coordinator"]
            # The coordinator will be automatically cleaned up when the entry is removed

    return unload_ok