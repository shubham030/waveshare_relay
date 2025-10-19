# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Waveshare Relay Hub integration.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Connection Issues](#connection-issues)
- [Entity Issues](#entity-issues)
- [Performance Issues](#performance-issues)
- [Advanced Debugging](#advanced-debugging)
- [Getting Help](#getting-help)

## Quick Diagnostics

### 1. Check Integration Status

First, check if the integration is loaded and working:

1. Go to **Settings** → **Devices & Services**
2. Find **Waveshare Relay Hub** in the list
3. Check if it shows any error messages
4. Click on the integration to see entities

### 2. Check Entity Attributes

Any relay entity will show diagnostic information:

1. Go to **Developer Tools** → **States**
2. Find any light or switch from your relay hub
3. Look at the attributes section:
   ```yaml
   address: 1
   last_command_success: true
   command_retries: 0
   hub_host: "192.168.1.100"
   hub_available: true
   ```

### 3. Enable Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.waveshare_relay: debug
```

Then restart Home Assistant and check the logs.

## Connection Issues

### Problem: "Hub not available" / All entities unavailable

**Symptoms:**
- All entities show as "Unavailable"
- Logs show connection timeouts
- Entity attributes show `hub_available: false`

**Diagnostic Steps:**

1. **Test Network Connectivity:**
   ```bash
   # From Home Assistant host
   ping 192.168.1.100
   telnet 192.168.1.100 502
   ```

2. **Check Gateway Settings:**
   - Access gateway web interface (usually `http://192.168.1.200`)
   - Verify it's in **TCP Server** mode
   - Check local port is **502**
   - Ensure baud rate matches relay module (**9600**)

3. **Verify Gateway Status:**
   - Look for LED indicators on gateway
   - Check if "Link" LED is blue (TCP connection established)
   - Check if "Active" LED flashes during communication

**Solutions:**

| Cause | Solution |
|-------|----------|
| Network issue | Check cables, switch ports, IP configuration |
| Gateway in wrong mode | Set to TCP Server mode, port 502 |
| Firewall blocking | Disable firewall or add exception for port 502 |
| IP address changed | Update configuration with correct IP |
| Gateway power issue | Check power supply, restart gateway |

**Configuration Adjustments:**
```yaml
waveshare_relay:
  - host: 192.168.1.100
    timeout: 10        # Increase timeout
    max_retries: 5     # More retry attempts
    retry_delay: 2.0   # Longer delays between retries
```

### Problem: Intermittent Connection Failures

**Symptoms:**
- Entities sometimes unavailable
- Logs show "Failed to communicate with device"
- Circuit breaker messages in logs

**Diagnostic Steps:**

1. **Check Network Stability:**
   ```bash
   # Continuous ping test
   ping -i 1 192.168.1.100
   
   # Monitor for packet loss
   ping -c 100 192.168.1.100
   ```

2. **Check Entity Statistics:**
   Look at `connection_stats` in entity attributes:
   ```yaml
   connection_stats:
     total_commands: 150
     successful_commands: 142
     failed_commands: 8
     average_response_time: 0.035
   ```

**Solutions:**

| Cause | Solution |
|-------|----------|
| WiFi interference | Use wired connection or better WiFi |
| Network congestion | Increase timeouts, reduce polling frequency |
| Gateway overload | Reduce command frequency, increase delays |
| Power supply issues | Check gateway power supply stability |

**Configuration for Unreliable Networks:**
```yaml
waveshare_relay:
  - host: 192.168.1.100
    poll_interval: 60          # Less frequent polling
    timeout: 15               # Longer timeout
    max_retries: 5            # More retries
    retry_delay: 3.0          # Longer delays
    circuit_breaker_threshold: 3  # More tolerance before circuit opens
    circuit_breaker_timeout: 120.0  # Longer recovery time
```

## Entity Issues

### Problem: Entities Don't Appear

**Symptoms:**
- Integration loads but no entities are created
- Expected lights/switches missing

**Diagnostic Steps:**

1. **Check Configuration:**
   ```yaml
   waveshare_relay:
     - host: 192.168.1.100
       name: "Test Hub"
       num_relays: 32    # Must be >= highest address
       
       lights:
         - name: "Test Light"
           address: 1    # Must be between 1 and num_relays
   ```

2. **Check Logs:**
   Look for configuration validation errors:
   ```
   ERROR [custom_components.waveshare_relay] Invalid relay address: 33 (must be between 1 and 32)
   ```

**Common Causes:**
- Relay address exceeds `num_relays`
- Duplicate relay addresses
- Invalid configuration syntax
- Integration not reloaded after config changes

**Solutions:**
1. Validate relay addresses are within range
2. Ensure no duplicate addresses
3. Restart Home Assistant after config changes
4. Check configuration.yaml syntax

### Problem: Entities Show Wrong State

**Symptoms:**
- Entity shows "On" but relay is actually off
- State doesn't update when relay is controlled externally

**Diagnostic Steps:**

1. **Check Polling:**
   ```yaml
   # Entity attributes
   last_update: "2024-01-15T10:30:00Z"
   ```

2. **Test Manual Update:**
   Call the update service:
   ```yaml
   service: homeassistant.update_entity
   target:
     entity_id: switch.test_relay
   ```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Slow polling | Reduce `poll_interval` |
| Communication errors | Check connection stability |
| Wrong relay address | Verify address matches physical relay |
| Modbus conflicts | Ensure no other devices using same address |

### Problem: Commands Don't Work

**Symptoms:**
- Clicking switch/light doesn't change relay state
- Commands time out or fail
- Entity shows command executed but relay doesn't respond

**Diagnostic Steps:**

1. **Check Entity Attributes:**
   ```yaml
   last_command_success: false
   command_retries: 3
   ```

2. **Test with Modbus Tool:**
   ```bash
   # Test direct communication (if available)
   modpoll -m tcp -a 1 -r 1 -c 1 192.168.1.100
   ```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Wrong device address | Verify Modbus device address (default: 1) |
| Relay not responding | Check relay power, connections |
| Command conflicts | Ensure only one system controls relays |
| Network issues | Improve connection stability |

## Performance Issues

### Problem: Slow Response Times

**Symptoms:**
- Long delay between command and relay activation
- High response times in entity attributes
- Sluggish UI response

**Diagnostic Steps:**

1. **Check Response Times:**
   ```yaml
   # In entity attributes
   connection_stats:
     average_response_time: 0.250  # High if > 0.1
   ```

2. **Network Latency Test:**
   ```bash
   # Measure network latency
   ping -c 10 192.168.1.100
   
   # Test TCP connection time
   time telnet 192.168.1.100 502
   ```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Network latency | Use wired connection, improve network |
| High polling frequency | Increase `poll_interval` |
| Overloaded gateway | Reduce command frequency |
| Distance/interference | Improve physical connection |

**Optimized Configuration:**
```yaml
waveshare_relay:
  - host: 192.168.1.100
    poll_interval: 15   # Faster polling for responsive UI
    timeout: 3         # Short timeout for quick feedback
    max_retries: 2     # Fewer retries for speed
```

### Problem: Circuit Breaker Frequently Opens

**Symptoms:**
- "Circuit breaker is open" messages in logs
- Periods where commands are blocked
- High failure count in statistics

**Diagnostic Steps:**

1. **Check Failure Statistics:**
   ```yaml
   connection_stats:
     failed_commands: 25
     circuit_breaker_open: true
   ```

2. **Monitor Network:**
   ```bash
   # Check for network instability
   ping -i 0.5 -c 100 192.168.1.100
   ```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Network instability | Fix network issues first |
| Too sensitive settings | Increase `circuit_breaker_threshold` |
| Rapid commands | Add delays between commands |
| Gateway overload | Reduce command frequency |

**Less Sensitive Configuration:**
```yaml
waveshare_relay:
  - host: 192.168.1.100
    circuit_breaker_threshold: 5    # More failures before opening
    circuit_breaker_timeout: 90.0   # Longer recovery time
    max_retries: 3                  # Fewer retries per command
```

## Advanced Debugging

### Enable Detailed Logging

For comprehensive debugging:

```yaml
logger:
  default: info
  logs:
    custom_components.waveshare_relay: debug
    custom_components.waveshare_relay.hub: debug
    custom_components.waveshare_relay.coordinator: debug
    custom_components.waveshare_relay.light: debug
    custom_components.waveshare_relay.switch: debug
```

### Useful Log Messages

**Normal Operation:**
```
DEBUG [custom_components.waveshare_relay.hub] Sending command to device: 01 0f 00 00 00 20 04 ff ff ff ff c5 1c
DEBUG [custom_components.waveshare_relay.hub] Received response from device: 01 0f 00 00 00 20 54 13
```

**Connection Issues:**
```
WARNING [custom_components.waveshare_relay.hub] Failed to communicate with device: Timeout connecting to 192.168.1.100:502
ERROR [custom_components.waveshare_relay.coordinator] Update failed for hub 192.168.1.100: Failed to read relay states
```

**Circuit Breaker:**
```
WARNING [custom_components.waveshare_relay.hub] Circuit breaker opened after 5 failures
INFO [custom_components.waveshare_relay.hub] Circuit breaker entering half-open state
```

### Network Packet Capture

For deep network analysis:

```bash
# Capture packets on port 502
sudo tcpdump -i any -n port 502 -v

# Or use Wireshark for GUI analysis
# Filter: tcp.port == 502 and ip.addr == 192.168.1.100
```

### Test Script

Use the included test script for debugging:

```bash
cd /path/to/waveshare_relay
python3 test_improvements.py
```

This tests:
- Connection manager functionality
- Retry logic
- Circuit breaker behavior
- Hub statistics

### Manual Testing

Test direct Modbus communication:

```python
import asyncio
from hub import WaveshareRelayHub

async def test_hub():
    config = {
        "host": "192.168.1.100",
        "port": 502,
        "name": "Test",
        "device_address": 1,
        "num_relays": 32
    }
    
    hub = WaveshareRelayHub(config)
    
    # Test reading status
    states = await hub.read_relay_status()
    print(f"Relay states: {states}")
    
    # Test setting relay
    success = await hub.set_relay_state(1, True)
    print(f"Command success: {success}")
    
    # Check statistics
    stats = hub.connection_stats
    print(f"Statistics: {stats}")

asyncio.run(test_hub())
```

## Getting Help

If you can't resolve the issue:

### 1. Gather Information

Collect this information before asking for help:

- **Home Assistant version**
- **Integration version** (check manifest.json)
- **Hardware models** (gateway and relay)
- **Network setup** (wired/wireless, switches, etc.)
- **Complete error logs** with debug logging enabled
- **Configuration** (remove sensitive data like IPs)

### 2. Check Existing Issues

Search the [GitHub issues](https://github.com/shubham030/waveshare_relay/issues) for similar problems.

### 3. Create New Issue

If no existing issue matches, create a new one with:

- Clear problem description
- Steps to reproduce
- Expected vs actual behavior
- All information from step 1
- Any attempted solutions

### 4. Community Support

- [Home Assistant Community Forum](https://community.home-assistant.io/)
- Search for "Waveshare Relay" or "Modbus RTU"

### 5. Hardware Documentation

- [Waveshare RS485 TO ETH (B) Wiki](https://www.waveshare.com/wiki/RS485_TO_ETH_(B))
- [Waveshare Modbus RTU Relay Wiki](https://www.waveshare.com/wiki/Modbus_RTU_Relay_32CH)

## Common Solutions Summary

| Problem | Quick Fix |
|---------|-----------|
| Can't connect | Check IP, ping test, verify gateway mode |
| Slow response | Reduce poll_interval, check network latency |
| Intermittent failures | Increase timeouts and retries |
| No entities | Check relay addresses, restart HA |
| Wrong states | Reduce poll_interval, check relay address |
| Commands fail | Verify device address, check relay power |
| Circuit breaker | Fix network stability, adjust thresholds |

Most issues are network-related. Focus on ensuring stable communication between Home Assistant and the gateway first.