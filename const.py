"""Constants for the Waveshare Relay integration."""

DOMAIN = "waveshare_relay"

# Configuration keys
CONF_DEVICE_NAME = "device_name"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_NUM_RELAYS = "num_relays"
CONF_DEVICE_ADDRESS = "device_address"
CONF_RELAY_NAMES = "relay_names"

# Default values
DEFAULT_PORT = 502
DEFAULT_NUM_RELAYS = 8
DEFAULT_DEVICE_ADDRESS = 1
DEFAULT_DEVICE_NAME = "waveshare"

# Validation
MIN_RELAY_NUMBER = 1
MAX_RELAY_NUMBER = 32
MIN_DEVICE_ADDRESS = 1
MAX_DEVICE_ADDRESS = 247
VALID_NUM_RELAYS = [8, 16, 32]
