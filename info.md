<p align="center">
  <img src="https://raw.githubusercontent.com/shubham030/waveshare_relay/main/images/logo.svg" alt="Waveshare Relay Hub" width="120"/>
</p>

# Waveshare Relay Hub

**Production-ready Home Assistant integration for [Waveshare](https://www.waveshare.com/) Modbus RTU Relay modules (8/16/32 channel) via RS485 TO ETH gateway.**

## ✨ Key Features

- 🔄 **Robust Connection** - Automatic retry with exponential backoff
- ⚡ **Circuit Breaker** - Prevents overload during network failures
- 💾 **State Persistence** - Restores relay states after restart
- 🏠 **Device Registry** - Proper HA device integration
- ⚙️ **Config Flow** - Easy UI-based setup
- 📊 **Smart Polling** - Adaptive intervals based on network conditions
- 📈 **97% Test Coverage** - Production-ready reliability

## 🛠️ Supported Hardware

| Gateways | Relay Modules |
|----------|---------------|
| RS485 TO ETH (B) | Modbus RTU Relay 8CH |
| RS485 TO POE ETH (B) | Modbus RTU Relay 16CH |
| | Modbus RTU Relay 32CH |

## ⚙️ Quick Setup

### Via UI
1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **"Waveshare Relay Hub"**
3. Enter your gateway IP and configure relays

### Via YAML
```yaml
waveshare_relay:
  - host: 192.168.1.100
    name: "My Relays"
    device_address: 1
    lights:
      - name: "Light 1"
        address: 1
    switches:
      - name: "Switch 1"
        address: 2
```

## 📚 Resources

- [Full Documentation](https://github.com/shubham030/waveshare_relay)
- [Configuration Guide](https://github.com/shubham030/waveshare_relay/blob/main/docs/configuration.md)
- [Troubleshooting](https://github.com/shubham030/waveshare_relay/blob/main/docs/troubleshooting.md)
- [Waveshare Official](https://www.waveshare.com/)
- [Product Wiki](https://www.waveshare.com/wiki/Modbus_RTU_Relay)

## 🆘 Support

[GitHub Issues](https://github.com/shubham030/waveshare_relay/issues) | [Discussions](https://github.com/shubham030/waveshare_relay/discussions)
