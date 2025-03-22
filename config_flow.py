"""Config flow for Waveshare Relay integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from . import DOMAIN
from .hub import WaveshareRelayHub

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
                    title=user_input["device_name"],
                    data=user_input
                )
            except ValueError as err:
                errors["base"] = str(err)
            except Exception as err:
                errors["base"] = "connection_error"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("device_name"): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=502): int,
                vol.Required("num_relays", default=8): vol.In([8, 16, 32]),
                vol.Optional("device_address", default=1): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=247)
                ),
            }),
            errors=errors,
        )