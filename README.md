# Waveshare Relay Integration for Home Assistant

This is a custom integration for Home Assistant that allows you to control Waveshare relay modules using Modbus RTU protocol over TCP.

## Features

- Control multiple relays (up to 32)
- Automatic reconnection handling
- Error tracking and recovery
- State persistence
- Detailed logging
- Type hints and comprehensive documentation

## Requirements

- Home Assistant 2023.8.0 or later
- Waveshare relay module with TCP interface
- Network connectivity to the relay module

## Installation

1. Copy the `waveshare_relay` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Settings -> Devices & Services -> Add Integration
4. Search for "Waveshare Relay" and add it

## Configuration

When adding the integration, you'll need to provide the following information:

- Host: IP address of your relay module
- Port: TCP port number (default: 502)
- Number of Relays: Number of relays on your module (1-32)
- Device Address: Modbus device address (default: 0x01)
- Device Name: Name for your device (default: "waveshare")
- Timeout: Connection timeout in seconds (default: 5)

## Usage

After installation, each relay will appear as a switch in Home Assistant. You can:

- Turn relays on/off
- Monitor relay states
- View last update time
- Track error counts
- Monitor connection status

## Troubleshooting

If you experience issues:

1. Check the Home Assistant logs for detailed error messages
2. Verify network connectivity to the relay module
3. Ensure the relay module is powered and properly connected
4. Check if the IP address and port are correct
5. Verify the number of relays matches your hardware

## Error Handling

The integration includes several error handling features:

- Automatic reconnection attempts
- Error counting and tracking
- Detailed logging of all operations
- Graceful degradation when errors occur

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details. 