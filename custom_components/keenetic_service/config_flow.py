"""Config flow for keenetic_service."""
from homeassistant import config_entries
import voluptuous as vol
from .const import (
    DOMAIN, CONF_HOST, CONF_PORT, CONF_USERNAME, 
    CONF_PASSWORD, CONF_KEY_FILE, CONF_SERVICES,
    DEFAULT_PORT, DEFAULT_UPDATE_INTERVAL
)
from .services import AVAILABLE_SERVICES, SERVICES
import homeassistant.helpers.config_validation as cv

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Exclusive(CONF_PASSWORD, "auth"): cv.string,
    vol.Exclusive(CONF_KEY_FILE, "auth"): cv.string,
    vol.Optional(CONF_SERVICES, default=list(AVAILABLE_SERVICES.keys())): 
        cv.multi_select(AVAILABLE_SERVICES),
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
        
            selected_services = [
                SERVICES[svc_id] 
                for svc_id in user_input[CONF_SERVICES] 
                if svc_id in SERVICES
            ]
            user_input[CONF_SERVICES] = selected_services

            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Keenetic {user_input[CONF_HOST]}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlow(config_entry)

class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            selected_services = [
                SERVICES[svc_id] 
                for svc_id in user_input[CONF_SERVICES] 
                if svc_id in SERVICES
            ]
            user_input[CONF_SERVICES] = selected_services
            return self.async_create_entry(title="", data=user_input)

        current_services = [svc["id"] for svc in self.config_entry.data.get(CONF_SERVICES, [])]
        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_SERVICES, default=current_services): 
                    cv.multi_select(AVAILABLE_SERVICES),
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=current_interval,
                ): cv.positive_int,
            }),
        )