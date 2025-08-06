import asyncio
import logging
import json
import os
from pathlib import Path
from .const import CONF_LIGHTS, CONF_SWITCHES, CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE, DOMAIN

_LOGGER = logging.getLogger(__name__)

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
        self._timer = None
        self._byte_size = (self._num_relays + 7) // 8
        
        # Last state configuration
        self._restore_state = config.get(CONF_RESTORE_STATE, DEFAULT_RESTORE_STATE)
        self._state_file = None
        if self._hass and self._restore_state:
            self._state_file = Path(self._hass.config.config_dir) / f"{DOMAIN}_{self._host}_{self._port}.json"
        
        # Track which relays are actually configured
        self._configured_relays = self._get_configured_relays(config)
        
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
        """Handle the TCP connection to the relay hub with timeout."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=self._timeout
            )
            writer.write(command)
            await writer.drain()

            # Read response with timeout
            response = await asyncio.wait_for(reader.read(1024), timeout=self._timeout)
            return response
        except (asyncio.TimeoutError, ConnectionError) as err:
            _LOGGER.error("Failed to communicate with device: %s", err)
            return None
        finally:
            if 'writer' in locals():
                writer.close()
                await writer.wait_closed()

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
