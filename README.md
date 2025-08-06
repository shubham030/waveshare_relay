# Waveshare Relay Home Assistant Integration

A Home Assistant integration for controlling Waveshare Modbus RTU Relay modules (32-channel) via TCP/IP.

## Features

- **Dual Configuration**: Supports both YAML and Config Flow setup
- **Multiple Entity Types**: Create switch and light entities for relay control
- **Flexible Mapping**: Map specific relays to lights or switches
- **State Synchronization**: Reads actual relay states from device
- **Error Handling**: Comprehensive error handling and logging
- **Thread Safety**: Uses asyncio locks for concurrent access

## Supported Devices

- Waveshare Modbus RTU Relay 32CH
- Other compatible Modbus RTU relay modules

## Installation

### Manual Installation

1. Copy the `waveshare_relay` folder to your `custom_components` directory
2. Restart Home Assistant
3. Add configuration via YAML or use the Config Flow

### YAML Configuration

```yaml
waveshare_relay:
  - host: 192.168.1.100
    port: 502
    name: "Living Room Relays"
    device_address: 1
    timeout: 5
    num_relays: 32
    lights:
      - name: "Living Room Light 1"
        address: 1
      - name: "Living Room Light 2"
        address: 2
    switches:
      - name: "Fan"
        address: 3
      - name: "Heater"
        address: 4
```

### Config Flow

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Waveshare Relay Hub"
4. Enter your device details
5. Configure your entities

## Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `host` | Yes | - | IP address of the relay device |
| `port` | No | 502 | TCP port for Modbus communication |
| `name` | Yes | - | Name for this relay hub |
| `device_address` | No | 1 | Modbus device address |
| `timeout` | No | 5 | Connection timeout in seconds |
| `num_relays` | No | 32 | Number of relays (1-32) |
| `lights` | No | [] | List of light entities |
| `switches` | No | [] | List of switch entities |

## Testing

### Python 3.11 Setup (Recommended)

For optimal compatibility with Home Assistant, we recommend using Python 3.11 for testing and development.

#### Quick Start

1. **Create Python 3.11 virtual environment:**
   ```bash
   python3.11 -m venv test_env_py311
   test_env_py311/bin/pip install -r requirements-test.txt
   ```

2. **Run tests with Python 3.11:**
   ```bash
   # Using the convenience script
   ./run_tests_py311.sh
   
   # Or directly
   test_env_py311/bin/python -m pytest tests/ -v
   ```

3. **Run with coverage:**
   ```bash
   test_env_py311/bin/python -m pytest tests/ --cov=waveshare_relay --cov-report=html
   ```

#### Alternative: Python 3.13

If you prefer to use Python 3.13:

1. **Create Python 3.13 virtual environment:**
   ```bash
   python3.13 -m venv test_env
   test_env/bin/pip install -r requirements-test.txt
   ```

2. **Run tests:**
   ```bash
   test_env/bin/python -m pytest tests/ -v
   ```

### Test Categories

Run specific test categories:
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Async tests only
pytest -m asyncio
```

### Test Coverage

Current test coverage: **97%**

- **Core Components**: 99-100% coverage
- **Hub Communication**: 100% coverage
- **Entity Management**: 99% coverage
- **Integration Tests**: 100% coverage

### Test Structure

- `tests/test_hub.py` - Tests for the hub communication layer
- `tests/test_switch.py` - Tests for switch entities
- `tests/test_light.py` - Tests for light entities
- `tests/test_coordinator.py` - Tests for the coordinator
- `tests/test_integration.py` - Integration and end-to-end tests

### Test Coverage

The test suite covers:
- ✅ Hub initialization and configuration
- ✅ TCP communication and error handling
- ✅ Modbus protocol implementation
- ✅ Relay state management
- ✅ Entity creation and configuration
- ✅ Switch and light functionality
- ✅ State updates and synchronization
- ✅ Error scenarios and edge cases
- ✅ Integration workflows

## Development

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings for all functions and classes
- Use meaningful variable and function names

### Adding New Features

1. Create feature branch
2. Implement feature with tests
3. Ensure all tests pass
4. Update documentation
5. Submit pull request

## Troubleshooting

### Common Issues

1. **Connection Timeout**: Check device IP and network connectivity
2. **Invalid Response**: Verify device address and Modbus settings
3. **State Not Updating**: Check relay configuration and addresses

### Debug Logging

Enable debug logging in your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.waveshare_relay: debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Documentation**: [Waveshare Wiki](https://www.waveshare.com/wiki/Modbus_RTU_Relay_32CH)
- **Issues**: [GitHub Issues](https://github.com/shubham030/waveshare_rtu_relay/issues)
- **Discussions**: [GitHub Discussions](https://github.com/shubham030/waveshare_rtu_relay/discussions) 