"""Hub to manage Waveshare Relay communication.

This module handles the communication with Waveshare relay modules using Modbus RTU protocol.
It provides methods to control multiple relays and manage their states.
"""

import asyncio
import logging
from typing import List, Optional, Tuple, Any, Dict
from async_timeout import timeout
from datetime import datetime

from homeassistant.exceptions import ConfigEntryNotReady
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CONF_DEVICE_NAME,
    CONF_HOST,
    CONF_PORT,
    CONF_NUM_RELAYS,
    CONF_DEVICE_ADDRESS,
    DEFAULT_PORT,
    DEFAULT_NUM_RELAYS,
    DEFAULT_DEVICE_ADDRESS,
    MIN_RELAY_NUMBER,
    MAX_RELAY_NUMBER,
)

_LOGGER = logging.getLogger(__name__)

class WaveshareRelayError(Exception):
    """Base exception for Waveshare relay errors."""
    pass

class WaveshareRelayHub:
    """Hub to manage all the Waveshare Relays.
    
    This class handles communication with the Waveshare relay module using Modbus RTU protocol.
    It manages the state of multiple relays and provides methods to control them.
    """

    def __init__(
        self,
        host: str,
        port: int,
        device_address: int,
        num_relays: int,
        device_name: str,
    ) -> None:
        """Initialize the hub."""
        self._host = host
        self._port = port
        self._device_address = device_address
        self._num_relays = num_relays
        self._device_name = device_name
        self._client: Optional[AsyncModbusTcpClient] = None
        self._is_connected = False
        self._last_update = None
        self._error_count = 0
        self._max_errors = 3

    @classmethod
    async def create(cls, config: Dict[str, Any]) -> "WaveshareRelayHub":
        """Create a new hub instance."""
        hub = cls(
            host=config[CONF_HOST],
            port=config.get(CONF_PORT, DEFAULT_PORT),
            device_address=config.get(CONF_DEVICE_ADDRESS, DEFAULT_DEVICE_ADDRESS),
            num_relays=config.get(CONF_NUM_RELAYS, DEFAULT_NUM_RELAYS),
            device_name=config.get(CONF_DEVICE_NAME, "waveshare"),
        )
        await hub.connect()
        return hub

    async def connect(self) -> None:
        """Connect to the Modbus TCP client."""
        try:
            self._client = AsyncModbusTcpClient(
                host=self._host,
                port=self._port,
                timeout=1,
            )
            await self._client.connect()
            self._is_connected = True
            self._error_count = 0
        except Exception as err:
            self._is_connected = False
            self._error_count += 1
            _LOGGER.error("Failed to connect to %s: %s", self._host, err)
            raise ConfigEntryNotReady from err

    async def close(self) -> None:
        """Close the Modbus TCP client."""
        if self._client:
            await self._client.close()
            self._is_connected = False

    async def read_relay_status(self) -> Optional[list[bool]]:
        """Read the status of all relays."""
        if not self._is_connected:
            await self.connect()
            if not self._is_connected:
                return None

        try:
            # Read holding registers for relay status
            result = await self._client.read_holding_registers(
                address=0,  # Starting address for relay status
                count=self._num_relays,
                slave=self._device_address,
            )
            if result.isError():
                self._error_count += 1
                _LOGGER.error("Error reading relay status: %s", result)
                return None

            # Convert register values to boolean list
            states = []
            for i in range(self._num_relays):
                # Each relay status is stored in a bit of the register
                register_index = i // 16
                bit_position = i % 16
                register_value = result.registers[register_index]
                state = bool(register_value & (1 << bit_position))
                states.append(state)

            self._error_count = 0
            self._last_update = datetime.now()
            return states

        except ModbusException as err:
            self._error_count += 1
            _LOGGER.error("Modbus error reading relay status: %s", err)
            return None
        except Exception as err:
            self._error_count += 1
            _LOGGER.error("Error reading relay status: %s", err)
            return None

    async def read_relay(self, relay_number: int) -> bool:
        """Read the status of a specific relay."""
        if not MIN_RELAY_NUMBER <= relay_number <= self._num_relays:
            raise ValueError(f"Relay number must be between {MIN_RELAY_NUMBER} and {self._num_relays}")

        states = await self.read_relay_status()
        if states is None:
            raise ValueError("Failed to read relay status")
        return states[relay_number - 1]

    async def set_relay(self, relay_number: int, state: bool) -> None:
        """Set the state of a specific relay."""
        if not MIN_RELAY_NUMBER <= relay_number <= self._num_relays:
            raise ValueError(f"Relay number must be between {MIN_RELAY_NUMBER} and {self._num_relays}")

        if not self._is_connected:
            await self.connect()
            if not self._is_connected:
                raise ValueError("Failed to connect to device")

        try:
            # Calculate register address and bit position
            register_index = (relay_number - 1) // 16
            bit_position = (relay_number - 1) % 16

            # Read current register value
            result = await self._client.read_holding_registers(
                address=register_index,
                count=1,
                slave=self._device_address,
            )
            if result.isError():
                raise ValueError(f"Error reading register: {result}")

            current_value = result.registers[0]

            # Update the specific bit
            if state:
                new_value = current_value | (1 << bit_position)
            else:
                new_value = current_value & ~(1 << bit_position)

            # Write the updated value
            result = await self._client.write_register(
                address=register_index,
                value=new_value,
                slave=self._device_address,
            )
            if result.isError():
                raise ValueError(f"Error writing register: {result}")

            self._error_count = 0
            self._last_update = datetime.now()

        except ModbusException as err:
            self._error_count += 1
            _LOGGER.error("Modbus error setting relay state: %s", err)
            raise ValueError(f"Modbus error: {err}")
        except Exception as err:
            self._error_count += 1
            _LOGGER.error("Error setting relay state: %s", err)
            raise ValueError(f"Error: {err}")

    @property
    def is_connected(self) -> bool:
        """Return True if the hub is connected."""
        return self._is_connected

    @property
    def last_update(self) -> Optional[datetime]:
        """Return the timestamp of the last successful update."""
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
