"""Sensor для статуса сервисов."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from .const import DOMAIN, CONF_SERVICES  # Добавлен импорт CONF_SERVICES

async def async_setup_entry(hass, entry, async_add_entities):
    
    coordinator = hass.data[DOMAIN][entry.entry_id]
    services = entry.data.get(CONF_SERVICES, [])
    
    async_add_entities([
        KeeneticServiceSensor(coordinator, service["id"], service["name"])
        for service in services
    ])

class KeeneticServiceSensor(SensorEntity):

    def __init__(self, coordinator, service_id, service_name):
        
        self.coordinator = coordinator
        self._service_id = service_id
        self._service_name = service_name
        self._attr_name = f"Keenetic {service_name} Status"
        self._attr_unique_id = f"keenetic_{service_id}_status"

    @property
    def state(self):
        
        data = self.coordinator.data.get(self._service_id, {})
        return data.get("status", "unknown")

    @property
    def available(self):
        
        data = self.coordinator.data.get(self._service_id, {})
        return data.get("available", False)

    @callback
    def _handle_coordinator_update(self):
        
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )