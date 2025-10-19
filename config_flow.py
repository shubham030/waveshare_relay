"""Config flow for Waveshare Relay Hub integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_DEVICE_ADDRESS,
    CONF_TIMEOUT,
    CONF_RESTORE_STATE,
    CONF_POLL_INTERVAL,
    CONF_MAX_RETRIES,
    DEFAULT_PORT,
    DEFAULT_DEVICE_ADDRESS,
    DEFAULT_TIMEOUT,
    DEFAULT_RESTORE_STATE,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_MAX_RETRIES,
)
from .hub import WaveshareRelayHub

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_DEVICE_ADDRESS, default=DEFAULT_DEVICE_ADDRESS): vol.All(
            cv.positive_int, vol.Range(min=1, max=255)
        ),
        vol.Optional("num_relays", default=32): vol.In([8, 16, 32]),
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
            cv.positive_int, vol.Range(min=1, max=60)
        ),
        vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(
            cv.positive_int, vol.Range(min=5, max=300)
        ),
        vol.Optional(CONF_MAX_RETRIES, default=DEFAULT_MAX_RETRIES): vol.All(
            cv.positive_int, vol.Range(min=1, max=10)
        ),
        vol.Optional(CONF_RESTORE_STATE, default=DEFAULT_RESTORE_STATE): cv.boolean,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Convert num_relays from string to int
    if "num_relays" in data:
        data["num_relays"] = int(data["num_relays"])

    hub = WaveshareRelayHub(data)
    
    # Test the connection
    try:
        await hub.read_relay_status()
    except Exception as exc:
        _LOGGER.error("Failed to connect to hub: %s", exc)
        raise CannotConnect from exc

    # Return info that you want to store in the config entry.
    return {
        "title": data[CONF_NAME],
        "host": data[CONF_HOST],
        "port": data[CONF_PORT],
    }


class ConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Waveshare Relay Hub."""

    VERSION = 1
    
    def __init__(self):
        """Initialize the config flow."""
        self._reauth_entry: config_entries.ConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", 
                data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Check if already configured
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}_{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(self, entry_data: Dict[str, Any]) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        errors = {}

        try:
            await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            if self._reauth_entry:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry, data=user_input
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Waveshare Relay Hub."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_POLL_INTERVAL,
                        default=self.config_entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                    ): vol.All(cv.positive_int, vol.Range(min=5, max=300)),
                    vol.Optional(
                        CONF_MAX_RETRIES,
                        default=self.config_entry.data.get(CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES),
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=10)),
                    vol.Optional(
                        CONF_TIMEOUT,
                        default=self.config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=60)),
                    vol.Optional(
                        CONF_RESTORE_STATE,
                        default=self.config_entry.data.get(CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE),
                    ): cv.boolean,
                }
            ),
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""