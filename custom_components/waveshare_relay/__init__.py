"""
Waveshare Relay integration.
"""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .hub import WaveshareRelayHub

DOMAIN = "waveshare_relay"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Waveshare Relay from a config entry."""
    hub = await WaveshareRelayHub.create(entry.data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    hass.config_entries.async_setup_platforms(entry, ["switch"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["switch"])