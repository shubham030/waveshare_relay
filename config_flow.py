import voluptuous as vol
from homeassistant import config_entries
from . import DOMAIN

class WaveshareRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Waveshare Relay."""

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("host"): str,
                    vol.Required("port", default=502): int,
                    vol.Required("num_relays", default=8): vol.In([8, 16, 32]),
                    vol.Optional("device_address", default=1): int,
                })
            )
        return self.async_create_entry(title=user_input["host"], data=user_input)