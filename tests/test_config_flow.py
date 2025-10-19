"""Tests for the Waveshare Relay config flow."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.data_entry_flow import FlowResultType

from custom_components.waveshare_relay import config_flow
from custom_components.waveshare_relay.const import (
    DOMAIN,
    CONF_DEVICE_ADDRESS,
    CONF_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_DEVICE_ADDRESS,
    DEFAULT_TIMEOUT,
)


class TestConfigFlow:
    """Test the config flow."""

    @pytest.fixture
    def mock_setup_entry(self):
        """Mock setting up a config entry."""
        with patch(
            "custom_components.waveshare_relay.async_setup_entry", return_value=True
        ) as mock_setup:
            yield mock_setup

    @pytest.mark.asyncio
    async def test_form(self, hass):
        """Test we get the form."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_form_invalid_host(self, hass):
        """Test we handle invalid host."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.waveshare_relay.config_flow.validate_input",
            side_effect=config_flow.CannotConnect,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_NAME: "Test Hub",
                    CONF_PORT: DEFAULT_PORT,
                    CONF_DEVICE_ADDRESS: DEFAULT_DEVICE_ADDRESS,
                    "num_relays": 32,
                    CONF_TIMEOUT: DEFAULT_TIMEOUT,
                },
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    async def test_form_cannot_connect(self, hass):
        """Test we handle cannot connect error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.waveshare_relay.config_flow.validate_input",
            side_effect=config_flow.CannotConnect,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_NAME: "Test Hub",
                },
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    async def test_form_unexpected_exception(self, hass):
        """Test we handle unexpected exception."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.waveshare_relay.config_flow.validate_input",
            side_effect=Exception,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_NAME: "Test Hub",
                },
            )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "unknown"}

    @pytest.mark.asyncio
    async def test_form_success(self, hass, mock_setup_entry):
        """Test successful form submission."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.waveshare_relay.config_flow.validate_input",
            return_value={
                "title": "Test Hub",
                "host": "192.168.1.100",
                "port": DEFAULT_PORT,
            },
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_NAME: "Test Hub",
                    CONF_PORT: DEFAULT_PORT,
                    CONF_DEVICE_ADDRESS: DEFAULT_DEVICE_ADDRESS,
                    "num_relays": 32,
                    CONF_TIMEOUT: DEFAULT_TIMEOUT,
                },
            )

        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["title"] == "Test Hub"
        assert result2["data"] == {
            CONF_HOST: "192.168.1.100",
            CONF_NAME: "Test Hub",
            CONF_PORT: DEFAULT_PORT,
            CONF_DEVICE_ADDRESS: DEFAULT_DEVICE_ADDRESS,
            "num_relays": 32,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
        }

    @pytest.mark.asyncio
    async def test_form_already_configured(self, hass):
        """Test we handle already configured."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: DEFAULT_PORT,
            },
            unique_id="192.168.1.100_502",
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.waveshare_relay.config_flow.validate_input",
            return_value={
                "title": "Test Hub",
                "host": "192.168.1.100",
                "port": DEFAULT_PORT,
            },
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_NAME: "Test Hub",
                    CONF_PORT: DEFAULT_PORT,
                },
            )

        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "already_configured"


class TestValidateInput:
    """Test the validate_input function."""

    @pytest.mark.asyncio
    async def test_validate_input_success(self, hass):
        """Test successful validation."""
        data = {
            CONF_HOST: "192.168.1.100",
            CONF_NAME: "Test Hub",
            CONF_PORT: DEFAULT_PORT,
            CONF_DEVICE_ADDRESS: DEFAULT_DEVICE_ADDRESS,
            "num_relays": 32,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
        }

        with patch(
            "custom_components.waveshare_relay.config_flow.WaveshareRelayHub"
        ) as mock_hub:
            mock_hub.return_value.read_relay_status = AsyncMock(return_value=[False] * 32)
            
            result = await config_flow.validate_input(hass, data)

        assert result == {
            "title": "Test Hub",
            "host": "192.168.1.100",
            "port": DEFAULT_PORT,
        }

    @pytest.mark.asyncio
    async def test_validate_input_cannot_connect(self, hass):
        """Test validation with connection error."""
        data = {
            CONF_HOST: "192.168.1.100",
            CONF_NAME: "Test Hub",
            CONF_PORT: DEFAULT_PORT,
        }

        with patch(
            "custom_components.waveshare_relay.config_flow.WaveshareRelayHub"
        ) as mock_hub:
            mock_hub.return_value.read_relay_status = AsyncMock(side_effect=Exception("Connection failed"))
            
            with pytest.raises(config_flow.CannotConnect):
                await config_flow.validate_input(hass, data)


class MockConfigEntry:
    """Mock config entry."""

    def __init__(self, domain, data, unique_id=None):
        """Initialize mock config entry."""
        self.domain = domain
        self.data = data
        self.unique_id = unique_id

    def add_to_hass(self, hass):
        """Add to hass."""
        pass