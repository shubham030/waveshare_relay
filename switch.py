from homeassistant.components.switch import SwitchEntity
from . import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(WaveshareRelaySwitch(hub, i + 1) for i in range(hub._num_relays))

class WaveshareRelaySwitch(SwitchEntity):
    def __init__(self, hub, relay_number):
        self._hub = hub
        self._relay_number = relay_number
        self._attr_name = f"Relay {relay_number}"
        self._attr_is_on = hub._relay_states[relay_number - 1]

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