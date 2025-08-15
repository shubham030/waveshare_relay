#!/usr/bin/env python3
"""
Mock Modbus TCP Server for Waveshare Relay Testing
This simulates the relay device for local testing without hardware
"""

import asyncio
import logging
import socket
import struct
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockModbusServer:
    """Mock Modbus TCP server that simulates the Waveshare relay"""
    
    def __init__(self, host='0.0.0.0', port=502):
        self.host = host
        self.port = port
        self.relay_states = [False] * 32  # 32 relays, all initially off
        self.server = None
        self.running = False
        
    async def start(self):
        """Start the mock server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client, self.host, self.port
            )
            self.running = True
            
            logger.info(f"🚀 Mock Modbus server started on {self.host}:{self.port}")
            logger.info(f"🔌 Simulating 32 relays")
            logger.info(f"📱 Use this IP in your Home Assistant configuration")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            self.running = False
            
    async def handle_client(self, reader, writer):
        """Handle incoming Modbus client connections"""
        addr = writer.get_extra_info('peername')
        logger.info(f"🔗 Client connected from {addr}")
        
        try:
            while True:
                # Read Modbus request
                data = await reader.read(256)
                if not data:
                    break
                    
                # Parse and handle the request
                response = await self.process_modbus_request(data)
                if response:
                    writer.write(response)
                    await writer.drain()
                    
        except Exception as e:
            logger.error(f"❌ Error handling client {addr}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"🔌 Client {addr} disconnected")
            
    async def process_modbus_request(self, data: bytes) -> bytes:
        """Process Modbus request and return response"""
        if len(data) < 12:  # Minimum Modbus TCP header
            return None
            
        try:
            # Parse Modbus TCP header
            transaction_id = struct.unpack('>H', data[0:2])[0]
            protocol_id = struct.unpack('>H', data[2:4])[0]
            length = struct.unpack('>H', data[4:6])[0]
            unit_id = data[6]
            function_code = data[7]
            
            logger.debug(f"📨 Modbus request: function={function_code}, unit={unit_id}")
            
            # Handle different function codes
            if function_code == 0x01:  # Read Coils
                response = self.handle_read_coils(data[8:])
            elif function_code == 0x0F:  # Write Multiple Coils
                response = self.handle_write_multiple_coils(data[8:])
            else:
                logger.warning(f"⚠️ Unsupported function code: {function_code}")
                response = self.create_error_response(function_code, 0x01)  # Illegal function
                
            if response:
                # Build Modbus TCP response header
                response_length = len(response) + 2  # +2 for unit_id and function_code
                header = struct.pack('>HHHBB', 
                                   transaction_id, protocol_id, response_length, unit_id, function_code)
                return header + response
                
        except Exception as e:
            logger.error(f"❌ Error processing request: {e}")
            
        return None
        
    def handle_read_coils(self, data: bytes) -> bytes:
        """Handle Read Coils (0x01) function"""
        if len(data) < 4:
            return None
            
        start_address = struct.unpack('>H', data[0:2])[0]
        coil_count = struct.unpack('>H', data[2:4])[0]
        
        logger.debug(f"📖 Read coils: start={start_address}, count={coil_count}")
        
        # Calculate byte count
        byte_count = (coil_count + 7) // 8
        
        # Build response
        response = bytes([byte_count])
        
        # Pack relay states into bytes
        for i in range(byte_count):
            byte_value = 0
            for bit in range(8):
                relay_index = start_address + i * 8 + bit
                if relay_index < len(self.relay_states) and self.relay_states[relay_index]:
                    byte_value |= (1 << bit)
            response += bytes([byte_value])
            
        return response
        
    def handle_write_multiple_coils(self, data: bytes) -> bytes:
        """Handle Write Multiple Coils (0x0F) function"""
        if len(data) < 6:
            return None
            
        start_address = struct.unpack('>H', data[0:2])[0]
        coil_count = struct.unpack('>H', data[2:4])[0]
        byte_count = data[4]
        coil_values = data[5:5+byte_count]
        
        logger.debug(f"✏️ Write coils: start={start_address}, count={coil_count}")
        
        # Update relay states
        for i in range(coil_count):
            relay_index = start_address + i
            if relay_index < len(self.relay_states):
                byte_index = i // 8
                bit_index = i % 8
                if byte_index < len(coil_values):
                    self.relay_states[relay_index] = bool(coil_values[byte_index] & (1 << bit_index))
                    
        logger.info(f"🔌 Relay states updated: {self.relay_states[:8]}...")  # Show first 8
        
        # Return success response
        return struct.pack('>HH', start_address, coil_count)
        
    def create_error_response(self, function_code: int, error_code: int) -> bytes:
        """Create Modbus error response"""
        return bytes([function_code | 0x80, error_code])
        
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server:
            self.server.close()
        logger.info("🛑 Mock Modbus server stopped")

async def main():
    """Main function to run the mock server"""
    server = MockModbusServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    finally:
        server.stop()

if __name__ == "__main__":
    print("🚀 Starting Mock Modbus TCP Server for Waveshare Relay")
    print("📱 This simulates a relay device for testing")
    print("🔌 Server will listen on 0.0.0.0:502")
    print("⏹️  Press Ctrl+C to stop")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user") 