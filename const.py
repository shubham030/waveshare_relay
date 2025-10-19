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
DEFAULT_POLL_INTERVAL = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_CIRCUIT_BREAKER_THRESHOLD = 5
DEFAULT_CIRCUIT_BREAKER_TIMEOUT = 30.0

# Additional configuration keys
CONF_POLL_INTERVAL = "poll_interval"
CONF_MAX_RETRIES = "max_retries"
CONF_RETRY_DELAY = "retry_delay"
CONF_CIRCUIT_BREAKER_THRESHOLD = "circuit_breaker_threshold"
CONF_CIRCUIT_BREAKER_TIMEOUT = "circuit_breaker_timeout"
