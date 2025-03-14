
import asyncio
class WaveshareRelayHub:
    """Hub to manage all the Waveshare Relays."""

    def __init__(self, config):
        self._host = config["host"]
        self._port = config["port"]
        self._num_relays = config["num_relays"]
        self._device_address = config.get("device_address", 0x01)
        self._relay_states = [False] * self._num_relays
        self._lock = asyncio.Lock()
        self._timer = None
        self._byte_size = (self._num_relays + 7) // 8

    @classmethod
    async def create(cls, config):
        """Alternative constructor to ensure initialization finishes before returning."""
        self = cls(config)
        await self.read_relay_status()
        return self

    async def set_relay_state(self, relay_number, state):
        """Set an individual relay state and immediately send the update."""
        async with self._lock:
            # Update the relay state
            self._relay_states[relay_number - 1] = state
            # Send the updated relay states immediately
            response = await self._send_relay_states()
            # Return success or failure based on response
            return response is not None

    async def _send_relay_states(self):
        """Prepare and send the updated relay state command."""
        bit_pattern = sum((1 << i) for i, relay_state in enumerate(self._relay_states) if relay_state)

        # Convert the bit pattern to 4 bytes in little-endian format
        bit_pattern_bytes = bit_pattern.to_bytes(self._byte_size)
        # Build the RS485 command
        rs485_command = bytes([self._device_address, 0x0F, 0x00, 0x00, 0x00, self._num_relays, self._byte_size]) + bit_pattern_bytes

        # Calculate CRC and append it to the command
        crc = self.calculate_crc(rs485_command)
        rs485_command += crc
        # Send command to the relay hub
        return await self.send_command(rs485_command)

    async def send_command(self, command):
        """Handle the TCP connection to the relay hub."""
        try:
            reader, writer = await asyncio.open_connection(self._host, self._port)
            writer.write(command)
            await writer.drain()
            response = await reader.read(1024)
            return response
        except (asyncio.TimeoutError, ConnectionError):
            return None
        finally:
            writer.close()
            await writer.wait_closed()

    async def read_relay_status(self):
        """Read the status of all relays, fully reversing the byte and bit order."""
        query_command = bytes([self._device_address, 0x01, 0x00, 0x00, 0x00, self._num_relays])
        crc = self.calculate_crc(query_command)
        query_command += crc

        response = await self.send_command(query_command)

        if response is None or len(response) < 5 + (self._num_relays + 7) // 8:
            return None

        # Extract the status bytes (exclude address, function code, and CRC)
        status_bytes = response[3:-2]

        # Convert bytes to a full binary string and reverse the order
        full_binary = ''.join(f"{byte:08b}" for byte in status_bytes)[::-1]

        # Convert binary string into relay status list
        self._relay_states = [bit == "1" for bit in full_binary[:self._num_relays]]
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
