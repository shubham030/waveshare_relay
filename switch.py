from homeassistant.components.switch import SwitchEntity
from . import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    device_name = entry.data.get("device_name", "waveshare")
    switches = [
        WaveshareRelaySwitch(hub, relay_num, device_name)
        for relay_num in range(1, hub._num_relays + 1)
    ]
    async_add_entities(switches, True)

class WaveshareRelaySwitch(SwitchEntity):
    def __init__(self, hub, relay_number,device_name):
        self._hub = hub
        self._relay_number = relay_number
        self._attr_name = f"{device_name} Relay {relay_number}"
        self._attr_unique_id = f"{device_name}_relay_{relay_number}"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs):
        if await self._hub.set_relay_state(self._relay_number, True):
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        if await self._hub.set_relay_state(self._relay_number, False):
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_update(self):
        await self._hub.read_relay_status()
        self._attr_is_on = self._hub._relay_states[self._relay_number - 1]