"""The Waveshare Relay integration."""
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DEVICE_NAME,
    CONF_NUM_RELAYS,
    CONF_DEVICE_ADDRESS,
    CONF_RELAY_NAMES,
    DEFAULT_PORT,
    DEFAULT_NUM_RELAYS,
    DEFAULT_DEVICE_ADDRESS,
    DEFAULT_DEVICE_NAME,
    DOMAIN,
    VALID_NUM_RELAYS,
)
from .hub import WaveshareRelayHub

_LOGGER = logging.getLogger(__name__)

# YAML configuration schema
PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): cv.string,
    vol.Optional(CONF_NUM_RELAYS, default=DEFAULT_NUM_RELAYS): vol.In(VALID_NUM_RELAYS),
    vol.Optional(CONF_DEVICE_ADDRESS, default=DEFAULT_DEVICE_ADDRESS): vol.All(
        vol.Coerce(int),
        vol.Range(min=1, max=247)
    ),
    vol.Optional(CONF_RELAY_NAMES): vol.Schema({
        vol.Optional(str): str
    }),
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Waveshare Relay integration from YAML."""
    if DOMAIN not in config:
        return True

    for entry_config in config[DOMAIN]:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data=entry_config,
            )
        )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waveshare Relay from a config entry."""
    try:
        hub = await WaveshareRelayHub.create(entry.data)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
    except Exception as err:
        _LOGGER.error("Error setting up Waveshare Relay: %s", err)
        return False

    await hass.config_entries.async_forward_entry_setups(entry, ["switch"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["switch"])
    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        hub = hass.data[DOMAIN][entry.entry_id]
        await hub.close()
        del hass.data[DOMAIN][entry.entry_id]
    return unload_ok