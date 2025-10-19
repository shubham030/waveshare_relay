import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from .const import CONF_LIGHTS, CONF_SWITCHES, CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE, DOMAIN

_LOGGER = logging.getLogger(__name__)

class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"

@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3

class ConnectionManager:
    """Manages TCP connection with retry logic and circuit breaker pattern."""
    
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.state = ConnectionState.DISCONNECTED
        self._connection_lock = asyncio.Lock()
        self._failure_count = 0
        self._last_failure_time = 0
        self._circuit_breaker_open = False
        self._half_open_calls = 0
        
        # Configuration
        self.retry_config = RetryConfig()
        self.circuit_breaker_config = CircuitBreakerConfig()
        
    async def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open."""
        if not self._circuit_breaker_open:
            return False
            
        # Check if we should attempt to close the circuit breaker
        if (time.time() - self._last_failure_time) > self.circuit_breaker_config.recovery_timeout:
            self._circuit_breaker_open = False
            self._half_open_calls = 0
            _LOGGER.info("Circuit breaker entering half-open state")
            return False
            
        return True
        
    async def _record_success(self):
        """Record a successful operation."""
        self._failure_count = 0
        if self._circuit_breaker_open:
            self._circuit_breaker_open = False
            _LOGGER.info("Circuit breaker closed after successful operation")
            
    async def _record_failure(self):
        """Record a failed operation."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.circuit_breaker_config.failure_threshold:
            self._circuit_breaker_open = True
            _LOGGER.warning(f"Circuit breaker opened after {self._failure_count} failures")
            
    async def send_command_with_retry(self, command: bytes) -> Optional[bytes]:
        """Send command with retry logic and circuit breaker."""
        if await self._is_circuit_breaker_open():
            _LOGGER.warning("Circuit breaker is open, skipping command")
            return None
            
        last_exception = None
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                async with self._connection_lock:
                    result = await self._send_command_single(command)
                    await self._record_success()
                    return result
                    
            except Exception as e:
                last_exception = e
                _LOGGER.warning(f"Command attempt {attempt + 1} failed: {e}")
                
                if attempt < self.retry_config.max_attempts - 1:
                    delay = min(
                        self.retry_config.base_delay * (self.retry_config.backoff_factor ** attempt),
                        self.retry_config.max_delay
                    )
                    if self.retry_config.jitter:
                        delay *= (0.5 + 0.5 * time.time() % 1)  # Add jitter
                    await asyncio.sleep(delay)
                    
        await self._record_failure()
        _LOGGER.error(f"All {self.retry_config.max_attempts} attempts failed. Last error: {last_exception}")
        return None
        
    async def _send_command_single(self, command: bytes) -> bytes:
        """Send a single command over TCP."""
        self.state = ConnectionState.CONNECTING
        writer = None
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), 
                timeout=self.timeout
            )
            
            self.state = ConnectionState.CONNECTED
            writer.write(command)
            await writer.drain()
            
            response = await asyncio.wait_for(
                reader.read(1024), 
                timeout=self.timeout
            )
            
            return response
            
        except asyncio.TimeoutError as e:
            self.state = ConnectionState.FAILED
            raise ConnectionError(f"Timeout connecting to {self.host}:{self.port}")
        except Exception as e:
            self.state = ConnectionState.FAILED
            raise ConnectionError(f"Failed to communicate with {self.host}:{self.port}: {e}")
        finally:
            if writer:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception as e:
                    _LOGGER.debug(f"Error closing connection: {e}")
            self.state = ConnectionState.DISCONNECTED

class WaveshareRelayHub:
    """Hub to manage all the Waveshare Relays."""

    def __init__(self, config, hass=None):
        self._host = config["host"]
        self._port = config["port"]
        self._device_address = config.get("device_address", 0x01)
        self._timeout = config.get("timeout", 5)
        self._hass = hass
        
        # Get the total number of relays from the device
        self._num_relays = config.get("num_relays", 32)  # Default to 32 if not specified
        self._relay_states = [False] * self._num_relays
        self._lock = asyncio.Lock()
        self._byte_size = (self._num_relays + 7) // 8
        
        # Connection management
        self._connection_manager = ConnectionManager(self._host, self._port, self._timeout)
        self._last_successful_communication = 0
        self._is_available = True
        
        # Last state configuration
        self._restore_state = config.get(CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE)
        self._state_file = None
        if self._hass and self._restore_state:
            self._state_file = Path(self._hass.config.config_dir) / f"{DOMAIN}_{self._host}_{self._port}.json"
        
        # Track which relays are actually configured
        self._configured_relays = self._get_configured_relays(config)
        
        # Performance monitoring
        self._command_stats = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "average_response_time": 0.0
        }
        
        _LOGGER.debug(
            "Initialized WaveshareRelayHub: host=%s, port=%s, num_relays=%s, configured_relays=%s, restore_state=%s",
            self._host,
            self._port,
            self._num_relays,
            self._configured_relays,
            self._restore_state
        )

    def _get_configured_relays(self, config):
        """Get a set of relay numbers that are actually configured."""
        configured = set()
        
        # Check lights
        for light in config.get(CONF_LIGHTS, []):
            configured.add(light["address"])
            
        # Check switches
        for switch in config.get(CONF_SWITCHES, []):
            configured.add(switch["address"])
            
        return configured

    @classmethod
    async def create(cls, config, hass=None):
        """Alternative constructor to ensure initialization finishes before returning."""
        self = cls(config, hass)
        await self.read_relay_status()
        return self

    async def _load_last_states(self):
        """Load last known states from file."""
        if not self._state_file or not self._state_file.exists():
            _LOGGER.debug("No last state file found, using default states")
            return
            
        try:
            with open(self._state_file, 'r') as f:
                saved_states = json.load(f)
                _LOGGER.debug("Loaded last states: %s", saved_states)
                
                # Apply saved states to configured relays only
                for relay_num, state in saved_states.items():
                    relay_num = int(relay_num)
                    if relay_num in self._configured_relays and 1 <= relay_num <= self._num_relays:
                        self._relay_states[relay_num - 1] = state
                        _LOGGER.debug("Restored relay %s to state: %s", relay_num, state)
                        
        except (json.JSONDecodeError, IOError) as e:
            _LOGGER.warning("Failed to load last states: %s", e)

    async def _save_last_states(self):
        """Save current states to file."""
        if not self._state_file:
            return
            
        try:
            # Create directory if it doesn't exist
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save only configured relay states
            states_to_save = {}
            for relay_num in self._configured_relays:
                if 1 <= relay_num <= self._num_relays:
                    states_to_save[str(relay_num)] = self._relay_states[relay_num - 1]
            
            with open(self._state_file, 'w') as f:
                json.dump(states_to_save, f)
                
            _LOGGER.debug("Saved last states: %s", states_to_save)
            
        except IOError as e:
            _LOGGER.error("Failed to save last states: %s", e)

    async def set_relay_state(self, relay_number, state):
        """Set an individual relay state and immediately send the update."""
        if relay_number < 1 or relay_number > self._num_relays:
            _LOGGER.error("Invalid relay number: %s (must be between 1 and %s)", relay_number, self._num_relays)
            raise ValueError(f"Invalid relay number: {relay_number} (must be between 1 and {self._num_relays})")
            
        if relay_number not in self._configured_relays:
            _LOGGER.error("Relay %s is not configured", relay_number)
            raise ValueError(f"Relay {relay_number} is not configured")
            
        async with self._lock:
            # Update the relay state
            self._relay_states[relay_number - 1] = state
            _LOGGER.debug(
                "Setting relay %s to %s, current states: %s",
                relay_number,
                state,
                self._relay_states
            )
            
            # Save the new state
            await self._save_last_states()
            
            # Send the updated relay states immediately
            response = await self._send_relay_states()
            # Return success or failure based on response
            if response is None:
                _LOGGER.error("Failed to send relay states to device")
            return response is not None

    async def restore_last_states(self):
        """Restore last known states to the device."""
        if not self._restore_state:
            _LOGGER.debug("State restoration disabled")
            return
            
        await self._load_last_states()
        
        # Check if we have any saved states to restore
        has_saved_states = any(self._relay_states)
        if not has_saved_states:
            _LOGGER.debug("No saved states to restore")
            return
            
        _LOGGER.info("Restoring last known relay states")
        
        # Send the restored states to the device
        response = await self._send_relay_states()
        if response is None:
            _LOGGER.error("Failed to restore relay states to device")
        else:
            _LOGGER.info("Successfully restored relay states")

    async def _send_relay_states(self):
        """Prepare and send the updated relay state command."""
        bit_pattern = sum((1 << i) for i, relay_state in enumerate(self._relay_states) if relay_state)

        # Convert the bit pattern to bytes in little-endian format
        bit_pattern_bytes = bit_pattern.to_bytes(self._byte_size)
        # Build the RS485 command
        rs485_command = bytes([self._device_address, 0x0F, 0x00, 0x00, 0x00, self._num_relays, self._byte_size]) + bit_pattern_bytes

        # Calculate CRC and append it to the command
        crc = self.calculate_crc(rs485_command)
        rs485_command += crc
        
        _LOGGER.debug(
            "Sending command to device: %s",
            ' '.join(f'{b:02x}' for b in rs485_command)
        )
        
        # Send command to the relay hub
        response = await self.send_command(rs485_command)
        
        if response:
            _LOGGER.debug(
                "Received response from device: %s",
                ' '.join(f'{b:02x}' for b in response)
            )
        
        return response

    async def send_command(self, command):
        """Handle the TCP connection to the relay hub with timeout and retry logic."""
        start_time = time.time()
        
        try:
            response = await self._connection_manager.send_command_with_retry(command)
            
            # Update statistics
            end_time = time.time()
            response_time = end_time - start_time
            self._update_command_stats(success=response is not None, response_time=response_time)
            
            if response:
                self._last_successful_communication = end_time
                self._is_available = True
            else:
                self._is_available = False
                
            return response
            
        except Exception as err:
            self._update_command_stats(success=False, response_time=time.time() - start_time)
            self._is_available = False
            _LOGGER.error("Failed to communicate with device: %s", err)
            return None

    def _update_command_stats(self, success: bool, response_time: float):
        """Update command statistics."""
        self._command_stats["total_commands"] += 1
        
        if success:
            self._command_stats["successful_commands"] += 1
        else:
            self._command_stats["failed_commands"] += 1
            
        # Update average response time
        total = self._command_stats["total_commands"]
        current_avg = self._command_stats["average_response_time"]
        self._command_stats["average_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )

    @property
    def is_available(self) -> bool:
        """Return if the hub is available."""
        return self._is_available and (
            time.time() - self._last_successful_communication < 300  # 5 minutes
        )

    @property
    def connection_stats(self) -> Dict[str, Any]:
        """Return connection statistics."""
        return {
            "connection_state": self._connection_manager.state.value,
            "is_available": self.is_available,
            "last_successful_communication": self._last_successful_communication,
            "command_stats": self._command_stats.copy(),
            "circuit_breaker_open": self._connection_manager._circuit_breaker_open,
            "failure_count": self._connection_manager._failure_count,
        }

    async def read_relay_status(self):
        """Read the status of all relays, fully reversing the byte and bit order."""
        query_command = bytes([self._device_address, 0x01, 0x00, 0x00, 0x00, self._num_relays])
        crc = self.calculate_crc(query_command)
        query_command += crc

        _LOGGER.debug(
            "Sending status query to device: %s",
            ' '.join(f'{b:02x}' for b in query_command)
        )

        response = await self.send_command(query_command)

        if response is None or len(response) < 5 + (self._num_relays + 7) // 8:
            _LOGGER.error("Invalid response from device when reading status")
            return None

        # Extract the status bytes (exclude address, function code, and CRC)
        status_bytes = response[3:-2]

        # Convert bytes to a full binary string and reverse the order
        full_binary = ''.join(f"{byte:08b}" for byte in status_bytes)[::-1]

        # Convert binary string into relay status list
        self._relay_states = [bit == "1" for bit in full_binary[:self._num_relays]]
        
        _LOGGER.debug(
            "Read relay status: %s",
            self._relay_states
        )
        
        return self._relay_states

    @staticmethod
    def calculate_crc(data):
        """Calculate CRC-16 (Modbus) checksum."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc >> 1) ^ 0xA001 if crc & 0x0001 else crc >> 1
        return crc.to_bytes(2, byteorder='little')
