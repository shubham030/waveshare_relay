# Configuration Guide

This guide covers all configuration options for the Waveshare Relay Hub integration.

## Table of Contents

- [Basic Configuration](#basic-configuration)
- [Advanced Configuration](#advanced-configuration)
- [Entity Configuration](#entity-configuration)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

## Basic Configuration

### Config Flow (Recommended)

The easiest way to configure the integration is through the Home Assistant UI:

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Waveshare Relay Hub"**
4. Fill in the basic settings:
   - **Host**: IP address of your RS485 TO ETH gateway
   - **Port**: TCP port (usually 502)
   - **Name**: Friendly name for this hub
   - **Device Address**: Modbus device address (usually 1)
   - **Number of Relays**: 8, 16, or 32

### YAML Configuration

For users who prefer YAML or need to configure multiple hubs:

```yaml
# configuration.yaml
waveshare_relay:
  - host: 192.168.1.100
    port: 502
    name: "Main Relay Hub"
    device_address: 1
    num_relays: 32
    
    lights:
      - name: "Kitchen Lights"
        address: 1
      - name: "Living Room Lights"
        address: 2
        
    switches:
      - name: "Water Pump"
        address: 3
      - name: "Garden Sprinkler"
        address: 4
```

## Advanced Configuration

### All Configuration Options

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `host` | string | **Required** | - | IP address of RS485 TO ETH gateway |
| `port` | integer | `502` | 1-65535 | TCP port number |
| `name` | string | **Required** | - | Friendly name for the hub |
| `device_address` | integer | `1` | 1-255 | Modbus device address |
| `num_relays` | integer | `32` | 1-32 | Number of relay channels |
| `timeout` | integer | `5` | 1-60 | Command timeout in seconds |
| `poll_interval` | integer | `30` | 5-300 | Status polling interval in seconds |
| `max_retries` | integer | `3` | 1-10 | Number of retry attempts |
| `retry_delay` | float | `1.0` | 0.1-10.0 | Base delay between retries |
| `restore_state` | boolean | `true` | - | Restore relay states on restart |

### Reliability Configuration

For improved reliability in challenging network environments:

```yaml
waveshare_relay:
  - host: 192.168.1.100
    name: "Production Relay Hub"
    
    # Basic settings
    timeout: 10
    max_retries: 5
    retry_delay: 2.0
    
    # Circuit breaker settings (advanced)
    circuit_breaker_threshold: 3
    circuit_breaker_timeout: 60.0
    
    # Polling settings
    poll_interval: 60
```

### Network Optimization

Different network scenarios require different settings:

#### Stable Wired Network
```yaml
waveshare_relay:
  - host: 192.168.1.100
    timeout: 3
    max_retries: 2
    retry_delay: 0.5
    poll_interval: 15
```

#### Wireless Network
```yaml
waveshare_relay:
  - host: 192.168.1.100
    timeout: 8
    max_retries: 4
    retry_delay: 1.5
    poll_interval: 45
```

#### Unreliable Network
```yaml
waveshare_relay:
  - host: 192.168.1.100
    timeout: 15
    max_retries: 5
    retry_delay: 3.0
    poll_interval: 120
    circuit_breaker_threshold: 2
    circuit_breaker_timeout: 90.0
```

## Entity Configuration

### Light Entities

Configure relays as lights for appropriate controls:

```yaml
waveshare_relay:
  - host: 192.168.1.100
    name: "Lighting Hub"
    
    lights:
      - name: "Kitchen Ceiling"
        address: 1
      - name: "Kitchen Under Cabinet"
        address: 2
      - name: "Dining Room Chandelier"
        address: 3
      - name: "Living Room Floor Lamp"
        address: 4
      - name: "Outdoor Front Porch"
        address: 5
      - name: "Outdoor Back Patio"
        address: 6
```

### Switch Entities

Configure relays as switches for non-lighting loads:

```yaml
waveshare_relay:
  - host: 192.168.1.100
    name: "Automation Hub"
    
    switches:
      - name: "Water Pump"
        address: 1
      - name: "Irrigation Zone 1"
        address: 2
      - name: "Irrigation Zone 2"
        address: 3
      - name: "Pool Pump"
        address: 4
      - name: "Hot Tub Heater"
        address: 5
      - name: "Garage Door Opener"
        address: 6
      - name: "Security System"
        address: 7
      - name: "Backup Generator"
        address: 8
```

### Mixed Configuration

You can mix lights and switches on the same hub:

```yaml
waveshare_relay:
  - host: 192.168.1.100
    name: "Mixed Hub"
    
    lights:
      - name: "Workshop Lights"
        address: 1
      - name: "Storage Room Light"
        address: 2
        
    switches:
      - name: "Workshop Ventilation"
        address: 3
      - name: "Storage Room Heater"
        address: 4
      - name: "Tool Compressor"
        address: 5
```

## Performance Tuning

### Optimizing for Different Use Cases

#### High-Frequency Control
For applications requiring frequent relay switching:

```yaml
waveshare_relay:
  - host: 192.168.1.100
    poll_interval: 10
    timeout: 3
    max_retries: 2
```

#### Background Monitoring
For applications that rarely change state:

```yaml
waveshare_relay:
  - host: 192.168.1.100
    poll_interval: 300  # 5 minutes
    timeout: 10
    max_retries: 3
```

#### Critical Applications
For mission-critical systems requiring maximum reliability:

```yaml
waveshare_relay:
  - host: 192.168.1.100
    timeout: 10
    max_retries: 5
    retry_delay: 2.0
    circuit_breaker_threshold: 2
    circuit_breaker_timeout: 120.0
    poll_interval: 30
```

### Multiple Hubs

When using multiple relay hubs, configure each with appropriate settings:

```yaml
waveshare_relay:
  # Main house hub - stable network
  - host: 192.168.1.100
    name: "Main House"
    poll_interval: 30
    timeout: 5
    
    lights:
      - name: "Living Room"
        address: 1
      - name: "Kitchen"
        address: 2
        
  # Garage hub - potentially unreliable WiFi
  - host: 192.168.1.101
    name: "Garage"
    poll_interval: 60
    timeout: 10
    max_retries: 4
    
    switches:
      - name: "Garage Door"
        address: 1
      - name: "Workshop Lights"
        address: 2
        
  # Pool house hub - long cable run
  - host: 192.168.1.102
    name: "Pool House"
    poll_interval: 45
    timeout: 8
    retry_delay: 2.0
    
    switches:
      - name: "Pool Pump"
        address: 1
      - name: "Pool Heater"
        address: 2
```

## Monitoring Configuration

### Enable Detailed Logging

For troubleshooting and monitoring:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.waveshare_relay: debug
    custom_components.waveshare_relay.hub: info
    custom_components.waveshare_relay.coordinator: info
```

### Performance Sensors

Create sensors to monitor hub performance:

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Relay Hub Success Rate"
        state: >
          {% set stats = state_attr('switch.water_pump', 'connection_stats') %}
          {% if stats and stats.total_commands > 0 %}
            {{ ((stats.successful_commands / stats.total_commands) * 100) | round(1) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "%"
        icon: mdi:check-network
        
      - name: "Relay Hub Response Time"
        state: >
          {% set stats = state_attr('switch.water_pump', 'connection_stats') %}
          {% if stats %}
            {{ (stats.average_response_time * 1000) | round(1) }}
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "ms"
        icon: mdi:timer-outline
        
      - name: "Relay Hub Status"
        state: >
          {% set stats = state_attr('switch.water_pump', 'connection_stats') %}
          {% if stats %}
            {% if stats.circuit_breaker_open %}
              Circuit Breaker Open
            {% elif stats.connection_state == 'connected' %}
              Connected
            {% else %}
              {{ stats.connection_state | title }}
            {% endif %}
          {% else %}
            Unknown
          {% endif %}
        icon: >
          {% set stats = state_attr('switch.water_pump', 'connection_stats') %}
          {% if stats and stats.circuit_breaker_open %}
            mdi:alert-circle
          {% elif stats and stats.connection_state == 'connected' %}
            mdi:check-circle
          {% else %}
            mdi:help-circle
          {% endif %}
```

## Troubleshooting

### Common Configuration Issues

#### Issue: Entities not appearing
```yaml
# Check that relay addresses are within range
waveshare_relay:
  - host: 192.168.1.100
    num_relays: 32  # Must be >= highest address used
    
    lights:
      - name: "Light 1"
        address: 1    # Must be between 1 and num_relays
```

#### Issue: Slow response times
```yaml
# Reduce polling interval and timeout
waveshare_relay:
  - host: 192.168.1.100
    poll_interval: 15   # Faster updates
    timeout: 3          # Shorter timeout
    max_retries: 2      # Fewer retries
```

#### Issue: Frequent connection failures
```yaml
# Increase tolerance for network issues
waveshare_relay:
  - host: 192.168.1.100
    timeout: 10         # Longer timeout
    max_retries: 5      # More retries
    retry_delay: 2.0    # Longer delays
    circuit_breaker_threshold: 3  # More tolerance
```

### Validation

The integration validates your configuration and will show errors if:

- Host is not a valid IP address
- Port is outside valid range (1-65535)
- Device address is outside valid range (1-255)
- Relay addresses exceed num_relays
- Duplicate relay addresses are used
- Invalid timeout or retry values

### Testing Configuration

Test your configuration with this automation:

```yaml
# automation.yaml
automation:
  - alias: "Test Relay Hub Configuration"
    trigger:
      platform: time_pattern
      minutes: "/5"  # Every 5 minutes
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.test_relay
      - delay: "00:00:01"
      - service: switch.turn_off
        target:
          entity_id: switch.test_relay
```

This will test connectivity and command execution every 5 minutes.

## Best Practices

1. **Use meaningful names** for hubs and entities
2. **Group related relays** on the same hub when possible
3. **Monitor performance** using built-in statistics
4. **Test configuration** in development before production
5. **Use appropriate timeouts** for your network conditions
6. **Enable logging** during initial setup and troubleshooting
7. **Document your configuration** for future reference

For more specific troubleshooting help, see the [Troubleshooting Guide](troubleshooting.md).