"""Hub to manage Waveshare Relay communication.

This module handles the communication with Waveshare relay modules using TCP protocol.
It provides methods to control multiple relays and manage their states.
"""

import asyncio
import logging
from typing import List, Optional, Tuple
from async_timeout import timeout

from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

class WaveshareRelayError(Exception):
    """Base exception for Waveshare relay errors."""
    pass

class WaveshareRelayHub:
    """Hub to manage all the Waveshare Relays.
    
    This class handles communication with the Waveshare relay module using TCP protocol.
    It manages the state of multiple relays and provides methods to control them.
    """

    def __init__(self, config: dict):
        """Initialize the Waveshare Relay Hub.
        
        Args:
            config: Configuration dictionary containing:
                - host: IP address of the relay module
                - port: TCP port number
                - num_relays: Number of relays (1-32)
                - device_address: Device address (default: 0x01)
                - timeout: Connection timeout in seconds (default: 5)
        """
        if not 1 <= config["num_relays"] <= 32:
            raise ValueError("Number of relays must be between 1 and 32")
            
        self._host = config["host"]
        self._port = config["port"]
        self._num_relays = config["num_relays"]
        self._device_address = config.get("device_address", 0x01)
        self._relay_states = [False] * self._num_relays
        self._lock = asyncio.Lock()
        self._connection: Optional[Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = None
        self._connection_lock = asyncio.Lock()
        self._byte_size = (self._num_relays + 7) // 8
        self._timeout = config.get("timeout", 5)
        self._last_update = None
        self._is_connected = False
        self._read_lock = asyncio.Lock()

    @classmethod
    async def create(cls, config: dict) -> 'WaveshareRelayHub':
        """Alternative constructor to ensure initialization finishes before returning.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Initialized WaveshareRelayHub instance
        """
        self = cls(config)
        await self.read_relay_status()
        return self

    async def _ensure_connection(self) -> None:
        """Ensure a connection is established with the relay module."""
        async with self._connection_lock:
            if self._connection is None:
                try:
                    async with timeout(self._timeout):
                        self._connection = await asyncio.open_connection(self._host, self._port)
                    self._is_connected = True
                except (asyncio.TimeoutError, ConnectionError) as e:
                    self._is_connected = False
                    raise WaveshareRelayError(f"Failed to connect to relay module: {e}")

    async def _close_connection(self) -> None:
        """Close the connection to the relay module."""
        async with self._connection_lock:
            if self._connection is not None:
                writer = self._connection[1]
                writer.close()
                await writer.wait_closed()
                self._connection = None
                self._is_connected = False

    async def set_relay_state(self, relay_number: int, state: bool) -> bool:
        """Set an individual relay state and immediately send the update.
        
        Args:
            relay_number: Relay number (1-based index)
            state: True to turn on, False to turn off
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not 1 <= relay_number <= self._num_relays:
            raise ValueError(f"Relay number must be between 1 and {self._num_relays}")
            
        async with self._lock:
            try:
                self._relay_states[relay_number - 1] = state
                response = await self._send_relay_states()
                if response is not None:
                    self._last_update = asyncio.get_event_loop().time()
                    return True
                return False
            except WaveshareRelayError as e:
                _LOGGER.error("Failed to set relay state: %s", e)
                return False

    async def _send_relay_states(self) -> Optional[bytes]:
        """Prepare and send the updated relay state command.
        
        Returns:
            bytes: Response from the relay module if successful, None otherwise
        """
        try:
            await self._ensure_connection()
            bit_pattern = sum((1 << i) for i, relay_state in enumerate(self._relay_states) if relay_state)
            bit_pattern_bytes = bit_pattern.to_bytes(self._byte_size)
            
            rs485_command = bytes([
                self._device_address, 0x0F, 0x00, 0x00, 0x00,
                self._num_relays, self._byte_size
            ]) + bit_pattern_bytes
            
            crc = self.calculate_crc(rs485_command)
            rs485_command += crc
            
            return await self.send_command(rs485_command)
        except WaveshareRelayError:
            await self._close_connection()
            return None

    async def send_command(self, command: bytes, max_retries: int = 3) -> Optional[bytes]:
        """Handle the TCP connection to the relay hub with timeout and retries.
        
        Args:
            command: Command bytes to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            bytes: Response from the relay module if successful, None otherwise
        """
        for attempt in range(max_retries):
            try:
                await self._ensure_connection()
                reader, writer = self._connection
                
                async with timeout(self._timeout):
                    writer.write(command)
                    await writer.drain()
                    
                    # Use a separate lock for reading to prevent concurrent reads
                    async with self._read_lock:
                        response = await reader.read(1024)
                    
                if not response:
                    raise WaveshareRelayError("Empty response from relay module")
                    
                return response
                
            except (asyncio.TimeoutError, ConnectionError) as e:
                _LOGGER.warning("Attempt %d failed: %s", attempt + 1, e)
                await self._close_connection()
                if attempt == max_retries - 1:
                    raise WaveshareRelayError(f"Failed after {max_retries} attempts: {e}")
                await asyncio.sleep(1)
                
        return None

    async def read_relay_status(self) -> Optional[List[bool]]:
        """Read the status of all relays.
        
        Returns:
            List[bool]: List of relay states if successful, None otherwise
        """
        try:
            query_command = bytes([
                self._device_address, 0x01, 0x00, 0x00, 0x00, self._num_relays
            ])
            crc = self.calculate_crc(query_command)
            query_command += crc

            response = await self.send_command(query_command)
            if response is None or len(response) < 5 + (self._num_relays + 7) // 8:
                raise WaveshareRelayError("Invalid response length")

            status_bytes = response[3:-2]
            full_binary = ''.join(f"{byte:08b}" for byte in status_bytes)[::-1]
            self._relay_states = [bit == "1" for bit in full_binary[:self._num_relays]]
            self._last_update = asyncio.get_event_loop().time()
            return self._relay_states
            
        except WaveshareRelayError as e:
            _LOGGER.error("Failed to read relay status: %s", e)
            return None

    @property
    def is_connected(self) -> bool:
        """Get the connection status of the hub."""
        return self._is_connected

    @property
    def last_update(self) -> Optional[float]:
        """Get the timestamp of the last successful update."""
        return self._last_update

    @staticmethod
    def calculate_crc(data: bytes) -> bytes:
        """Calculate CRC-16 (Modbus) checksum.
        
        Args:
            data: Data bytes to calculate CRC for
            
        Returns:
            bytes: 2-byte CRC value
        """
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc >> 1) ^ 0xA001 if crc & 0x0001 else crc >> 1
        return crc.to_bytes(2, byteorder='little')
