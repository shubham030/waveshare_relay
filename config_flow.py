"""Config flow for Waveshare Relay integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from . import DOMAIN
from .hub import WaveshareRelayHub
from .const import (
    CONF_DEVICE_NAME,
    CONF_NUM_RELAYS,
    CONF_DEVICE_ADDRESS,
    CONF_RELAY_NAMES,
    DEFAULT_PORT,
    DEFAULT_NUM_RELAYS,
    DEFAULT_DEVICE_ADDRESS,
    DEFAULT_DEVICE_NAME,
    VALID_NUM_RELAYS,
)

class WaveshareRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Waveshare Relay."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate the connection
                hub = await WaveshareRelayHub.create(user_input)
                await hub.read_relay_status()
                return self.async_create_entry(
                    title=user_input[CONF_DEVICE_NAME],
                    data=user_input
                )
            except ValueError as err:
                errors["base"] = str(err)
            except Exception as err:
                errors["base"] = "connection_error"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_NUM_RELAYS, default=DEFAULT_NUM_RELAYS): vol.In(VALID_NUM_RELAYS),
                vol.Optional(CONF_DEVICE_ADDRESS, default=DEFAULT_DEVICE_ADDRESS): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=247)
                ),
                vol.Optional(CONF_RELAY_NAMES): vol.Schema({
                    vol.Optional(str): str
                }),
            }),
            errors=errors,
        )

    async def async_step_import(self, import_data):
        """Import a config entry."""
        try:
            # Validate the connection
            hub = await WaveshareRelayHub.create(import_data)
            await hub.read_relay_status()
            return self.async_create_entry(
                title=import_data[CONF_DEVICE_NAME],
                data=import_data
            )
        except ValueError as err:
            return self.async_abort(reason=str(err))
        except Exception as err:
            return self.async_abort(reason="connection_error")