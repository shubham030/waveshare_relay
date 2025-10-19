# Waveshare Relay Hub

Production-ready Home Assistant integration for Waveshare Relay modules via RS485 TO ETH (B) gateway.

## What's New in V2.0

🚀 **Major reliability improvements** for production use:

- **Robust Connection Management**: Automatic retry logic with exponential backoff
- **Circuit Breaker Pattern**: Prevents system overload during network failures
- **Smart Polling**: Adaptive polling intervals based on network conditions
- **Performance Monitoring**: Real-time statistics and diagnostics
- **State Verification**: Ensures commands actually succeeded

## Features

- ⚡ **Production Ready**: Extensively tested for 24/7 reliability
- 🔄 **Auto-Recovery**: Automatic recovery from network issues
- 📊 **Monitoring**: Built-in performance metrics and diagnostics
- 🎯 **Smart**: Adaptive behavior based on network conditions
- ⚙️ **Configurable**: Tune retry behavior, timeouts, and polling
- 🏠 **Native HA**: Full integration with lights, switches, and automations

## Hardware Compatibility

- **Waveshare RS485 TO ETH (B)** - TCP server mode
- **Waveshare RS485 TO POE ETH (B)** - PoE powered version  
- **Waveshare Modbus RTU Relay** - 8CH, 16CH, or 32CH models

Perfect for:
- Industrial automation
- Home automation  
- IoT projects requiring reliable relay control
- Mixed RS485 networks (e.g., with Dooya curtains)

## Quick Start

1. **Install via HACS**:
   - Add custom repository: `https://github.com/shubham030/waveshare_relay`
   - Install "Waveshare Relay Hub"
   - Restart Home Assistant

2. **Add Integration**:
   - Settings → Devices & Services → Add Integration
   - Search "Waveshare Relay Hub"
   - Enter your gateway IP and configure relays

3. **Start Controlling**:
   - Relays appear as lights/switches
   - Use in automations, scripts, dashboards
   - Monitor performance via entity attributes

## Configuration Example

```yaml
# YAML configuration (optional)
waveshare_relay:
  - host: 192.168.1.100
    name: "Main Relay Hub"
    num_relays: 32
    lights:
      - name: "Kitchen Lights"
        address: 1
    switches:
      - name: "Water Pump"
        address: 2
```

Or use the Config Flow UI for easier setup!

## Why Choose This Integration?

### Before (V1.x)
- ❌ Basic connection handling
- ❌ No retry logic
- ❌ Poor error recovery
- ❌ Fixed polling intervals
- ❌ Limited diagnostics

### After (V2.x) 
- ✅ Robust connection management
- ✅ Automatic retry with backoff
- ✅ Circuit breaker protection
- ✅ Adaptive polling
- ✅ Comprehensive monitoring
- ✅ Production-grade reliability

## Support

- 📖 **Documentation**: Comprehensive README with examples
- 🐛 **Issues**: GitHub issue tracker
- 💬 **Community**: Home Assistant Community Forum
- 🔧 **Debug Tools**: Built-in diagnostics and logging

Ready for production use! ⭐