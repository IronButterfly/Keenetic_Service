from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from .const import DOMAIN, CONF_SERVICES
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):

    coordinator = hass.data[DOMAIN][entry.entry_id]
    services = entry.data.get(CONF_SERVICES, [])
    
    entities = [
        KeeneticServiceSwitch(coordinator, service)
        for service in services
    ]
    
    async_add_entities(entities)

class KeeneticServiceSwitch(SwitchEntity):
    

    def __init__(self, coordinator, service):
        
        self.coordinator = coordinator
        self._service = service
        self._attr_name = f"Keenetic {service['name']}"
        self._attr_unique_id = f"keenetic_{service['id']}_switch"

    @property
    def is_on(self):
        
        data = self.coordinator.data.get(self._service["id"])
        return data.get("status") == "running" if data else False

    @property
    def available(self):
        
        data = self.coordinator.data.get(self._service["id"])
        return data.get("available", False) if data else False

    async def async_turn_on(self, **kwargs):
        
        cmd = self._service.get("start_cmd")
        if not cmd:
            _LOGGER.error("Нет команды для включения %s", self._service["name"])
            return
        
        result = await self.coordinator.async_run_command(cmd)
        if result["success"]:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Ошибка включения %s: %s", 
                         self._service["name"], result.get("stderr"))

    async def async_turn_off(self, **kwargs):
        
        cmd = self._service.get("stop_cmd")
        if not cmd:
            _LOGGER.error("Нет команды для выключения %s", self._service["name"])
            return
        
        result = await self.coordinator.async_run_command(cmd)
        if result["success"]:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Ошибка выключения %s: %s", 
                         self._service["name"], result.get("stderr"))

    @callback
    def _handle_coordinator_update(self):
        
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )