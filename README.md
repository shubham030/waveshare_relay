<p align="center">
  <img src="images/logo.svg" alt="Waveshare Relay Hub" width="180"/>
</p>

<h1 align="center">Waveshare Relay Hub for Home Assistant</h1>

<p align="center">
  <strong>Production-ready Home Assistant integration for <a href="https://www.waveshare.com/">Waveshare</a> Modbus RTU Relay modules via RS485 TO ETH (B) gateway.</strong>
</p>

<p align="center">
  <a href="https://github.com/shubham030/waveshare_relay/releases"><img src="https://img.shields.io/github/v/release/shubham030/waveshare_relay?style=for-the-badge" alt="Release"></a>
  <a href="https://github.com/shubham030/waveshare_relay/blob/main/LICENSE"><img src="https://img.shields.io/github/license/shubham030/waveshare_relay?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge" alt="HACS"></a>
  <a href="https://github.com/shubham030/waveshare_relay/stargazers"><img src="https://img.shields.io/github/stars/shubham030/waveshare_relay?style=for-the-badge" alt="Stars"></a>
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=shubham030&repository=waveshare_relay&category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." />
  </a>
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔄 **Robust Connection** | Automatic retry logic with exponential backoff |
| ⚡ **Circuit Breaker** | Prevents system overload during network failures |
| 📊 **Smart Polling** | Adaptive polling intervals based on network conditions |
| 🔍 **State Verification** | Ensures commands actually succeeded on hardware |
| 💾 **State Persistence** | Restores relay states after Home Assistant restart |
| 🏠 **Device Registry** | Proper HA device integration with unique IDs |
| ⚙️ **Config Flow** | Easy setup via Home Assistant UI |
| 📝 **YAML Support** | Advanced configuration via YAML for power users |
| 🎛️ **Flexible Entities** | Configure relays as lights or switches |
| 📈 **97% Test Coverage** | Production-ready with comprehensive tests |

---

## 🛠️ Supported Hardware

> All products available at [waveshare.com](https://www.waveshare.com/)

### Gateways

| Model | Product Link |
|-------|--------------|
| RS485 TO ETH (B) | [Product Page](https://www.waveshare.com/rs485-to-eth-b.htm) |
| RS485 TO POE ETH (B) | [Product Page](https://www.waveshare.com/rs485-to-poe-eth-b.htm) |

### Relay Modules

| Model | Channels | Product Link |
|-------|----------|--------------|
| Modbus RTU Relay 8CH | 8 | [Product Page](https://www.waveshare.com/modbus-rtu-relay-8ch.htm) |
| Modbus RTU Relay 16CH | 16 | [Product Page](https://www.waveshare.com/modbus-rtu-relay-16ch.htm) |
| Modbus RTU Relay 32CH | 32 | [Product Page](https://www.waveshare.com/modbus-rtu-relay-32ch.htm) |

---

## 📦 Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=shubham030&repository=waveshare_relay&category=integration)

1. Click the button above, or:
   - Open HACS in Home Assistant
   - Click on **Integrations**
   - Click the **⋮** menu → **Custom repositories**
   - Add `https://github.com/shubham030/waveshare_relay` as **Integration**
   - Search for **"Waveshare Relay Hub"** and click **Download**

2. **Restart Home Assistant**

3. Go to **Settings** → **Devices & Services** → **Add Integration** → Search for **"Waveshare Relay Hub"**

### Manual Installation

```bash
# Navigate to your Home Assistant config directory
cd /config/custom_components/

# Clone the repository
git clone https://github.com/shubham030/waveshare_relay.git
```

Restart Home Assistant after installation.

---

## ⚙️ Configuration

### Via UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Waveshare Relay Hub"**
4. Fill in your device details:
   - **Host**: IP address of your RS485 gateway
   - **Port**: TCP port (default: 502)
   - **Name**: Friendly name for this hub
   - **Device Address**: Modbus device address (default: 1)
   - **Number of Relays**: 8, 16, or 32

### Via YAML

```yaml
# configuration.yaml
waveshare_relay:
  - host: 192.168.1.100
    port: 502
    name: "Living Room Relays"
    device_address: 1
    num_relays: 32
    restore_state: true
    
    # Configure relays as lights
    lights:
      - name: "Ceiling Light"
        address: 1
      - name: "Wall Light"
        address: 2
        
    # Configure relays as switches
    switches:
      - name: "Fan"
        address: 3
      - name: "Heater"
        address: 4
```

### Configuration Options

| Option | Required | Default | Description |
|--------|:--------:|:-------:|-------------|
| `host` | ✅ | - | IP address of RS485 gateway |
| `port` | ❌ | `502` | TCP port |
| `name` | ✅ | - | Friendly name for this hub |
| `device_address` | ❌ | `1` | Modbus device address (1-255) |
| `num_relays` | ❌ | `32` | Number of relays (8/16/32) |
| `timeout` | ❌ | `5` | Connection timeout (seconds) |
| `restore_state` | ❌ | `true` | Restore states on restart |
| `poll_interval` | ❌ | `30` | Polling interval (seconds) |
| `max_retries` | ❌ | `3` | Command retry attempts |
| `retry_delay` | ❌ | `1.0` | Delay between retries (seconds) |

---

## 🔧 Advanced Configuration

### Network Optimization

**Stable Wired Network:**
```yaml
waveshare_relay:
  - host: 192.168.1.100
    timeout: 3
    max_retries: 2
    poll_interval: 15
```

**Unreliable Network:**
```yaml
waveshare_relay:
  - host: 192.168.1.100
    timeout: 15
    max_retries: 5
    retry_delay: 3.0
    poll_interval: 120
    circuit_breaker_threshold: 3
```

### Multiple Hubs

```yaml
waveshare_relay:
  - host: 192.168.1.100
    name: "Main House"
    lights:
      - name: "Living Room"
        address: 1
        
  - host: 192.168.1.101
    name: "Garage"
    switches:
      - name: "Garage Door"
        address: 1
```

---

## 🔍 Troubleshooting

### Enable Debug Logging

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.waveshare_relay: debug
```

### Common Issues

| Issue | Solution |
|-------|----------|
| **Connection timeout** | Check device IP and network connectivity. Verify gateway is in TCP Server mode on port 502. |
| **Invalid response** | Verify Modbus device address matches relay module settings (default: 1). |
| **State not updating** | Check relay configuration and addresses. Reduce `poll_interval` for faster updates. |
| **Entities missing** | Ensure `address` values are between 1 and `num_relays`. Restart Home Assistant. |
| **Intermittent failures** | Increase `timeout` and `max_retries`. Check network stability. |

### Network Testing

```bash
# Test connectivity
ping 192.168.1.100

# Test TCP port
telnet 192.168.1.100 502
```

For detailed troubleshooting, see the [Troubleshooting Guide](docs/troubleshooting.md).

---

## 🧪 Development

```bash
# Create virtual environment
python3.11 -m venv test_env
source test_env/bin/activate

# Install dependencies
pip install -r requirements-test.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=term-missing
```

**Current Test Coverage: 97%**

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Configuration Guide](docs/configuration.md) | Detailed configuration options and examples |
| [Troubleshooting Guide](docs/troubleshooting.md) | Step-by-step troubleshooting instructions |
| [HACS Setup](docs/hacs-setup.md) | HACS installation and publishing guide |
| [Waveshare Wiki](https://www.waveshare.com/wiki/Modbus_RTU_Relay) | Official hardware documentation |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- 🐛 [Issue Tracker](https://github.com/shubham030/waveshare_relay/issues)
- 💬 [Discussions](https://github.com/shubham030/waveshare_relay/discussions)
- 🏠 [Home Assistant Community](https://community.home-assistant.io/)
- 📖 [Waveshare Official Site](https://www.waveshare.com/)
- 📚 [Waveshare Wiki](https://www.waveshare.com/wiki/Main_Page)

---

## 👏 Credits

- Created and maintained by [@shubham030](https://github.com/shubham030)
- Hardware by [Waveshare](https://www.waveshare.com/)

---

<p align="center">
  <a href="https://www.buymeacoffee.com/shubham030">
    <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=shubham030&button_colour=65ae00&font_colour=ffffff&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff" />
  </a>
</p>
