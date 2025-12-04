<p align="center">
  <img src="https://raw.githubusercontent.com/shubham030/waveshare_relay/main/images/logo.svg" alt="Waveshare Relay Hub" width="120"/>
</p>

# Waveshare Relay Hub

**Production-ready Home Assistant integration for [Waveshare](https://www.waveshare.com/) Modbus RTU Relay modules.**

## ✨ Features

- 🔄 **Robust Connection** - Automatic retry with exponential backoff
- ⚡ **Circuit Breaker** - Prevents overload during failures
- 💾 **State Persistence** - Restores states after restart
- 🏠 **Device Registry** - Proper HA device integration
- ⚙️ **Config Flow** - Easy UI-based setup

## 🛠 Supported Hardware

| Gateway | Relay Modules |
|---------|---------------|
| RS485 TO ETH (B) | 8CH / 16CH / 32CH |
| RS485 TO POE ETH (B) | Modbus RTU Relay |

## ⚙️ Quick Setup

### Via UI
1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Waveshare Relay Hub"
3. Enter your device IP and configure relays

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

## 📚 More Info

- [Full Documentation](https://github.com/shubham030/waveshare_relay)
- [Waveshare Official](https://www.waveshare.com/)
- [Product Wiki](https://www.waveshare.com/wiki/Modbus_RTU_Relay)
