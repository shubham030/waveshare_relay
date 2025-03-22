"""
Waveshare Relay integration.
"""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from .hub import WaveshareRelayHub, WaveshareRelayError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "waveshare_relay"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waveshare Relay from a config entry."""
    try:
        hub = await WaveshareRelayHub.create(entry.data)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
        
        # Verify connection and read initial state
        await hub.read_relay_status()
        
        await hass.config_entries.async_forward_entry_setups(entry, ["switch"])
        return True
    except WaveshareRelayError as err:
        _LOGGER.error("Failed to setup Waveshare Relay: %s", err)
        raise ConfigEntryNotReady from err
    except Exception as err:
        _LOGGER.error("Unexpected error during Waveshare Relay setup: %s", err)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, ["switch"]):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok