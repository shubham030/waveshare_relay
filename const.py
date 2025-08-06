"""Constants for the Waveshare Relay integration."""
DOMAIN = "waveshare_relay"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"
CONF_ADDRESS = "address"
CONF_DEVICE_ADDRESS = "device_address"
CONF_TIMEOUT = "timeout"
CONF_RESTORE_STATE = "restore_state"
CONF_LAST_STATE = "last_state"

# Entity types
CONF_LIGHTS = "lights"
CONF_SWITCHES = "switches"

# Default values
DEFAULT_PORT = 502
DEFAULT_DEVICE_ADDRESS = 0x01
DEFAULT_TIMEOUT = 5
DEFAULT_RESTORE_STATE = True
