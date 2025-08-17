"""Coordinator для опроса сервисов."""
import asyncio
import asyncssh
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import (
    DOMAIN, CONF_HOST, CONF_PORT, CONF_USERNAME, 
    CONF_PASSWORD, CONF_KEY_FILE, CONF_SERVICES,
    CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL,
    DEFAULT_PORT
)

_LOGGER = logging.getLogger(__name__)

class KeeneticServiceCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, config_entry):
        
        self.hass = hass
        self.config_entry = config_entry
        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data.get(CONF_PORT, DEFAULT_PORT)
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data.get(CONF_PASSWORD)
        self.key_file = config_entry.data.get(CONF_KEY_FILE)
        self.services = config_entry.data.get(CONF_SERVICES, [])
        self._ssh_conn = None

        update_interval = timedelta(
            seconds=config_entry.options.get(
                CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
            )
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _ensure_ssh_connection(self):
        
        try:
            if self._ssh_conn is None or getattr(self._ssh_conn, '_conn', None) is None:
                self._ssh_conn = await asyncssh.connect(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    client_keys=[self.key_file] if self.key_file else None,
                    known_hosts=None,
                    connect_timeout=10
                )
            return self._ssh_conn
        except Exception as ex:
            _LOGGER.error("Ошибка подключения SSH: %s", ex)
            raise

    async def _async_ssh_close(self):
        
        if self._ssh_conn:
            try:
                self._ssh_conn.close()
            except:
                pass
            finally:
                self._ssh_conn = None

    async def _async_update_data(self):
        
        statuses = {}
        try:
            conn = await self._ensure_ssh_connection()
            for service in self.services:
                status = await self._get_service_status(conn, service)
                statuses[service["id"]] = {
                    "status": status,
                    "available": status != "unknown"
                }
        except Exception as ex:
            _LOGGER.error("Ошибка обновления данных: %s", ex)
            for service in self.services:
                statuses[service["id"]] = {
                    "status": "unknown",
                    "available": False
                }
        finally:
            await self._async_ssh_close()
        
        return statuses

    async def _get_service_status(self, conn, service):
        
        try:
            if service["type"] == "script":
                result = await conn.run(service["status_cmd"], check=False)
                return "running" if "running" in result.stdout.lower() else "stopped"
            
            elif service["type"] == "command":
                engine = await self._detect_engine(conn)
                if engine == "mihomo":
                    cmd = "ps w | grep -v grep | grep -q 'mihomo' && echo running || echo stopped"
                elif engine == "xray":
                    cmd = "ps w | grep -v grep | grep -q 'xray run' && echo running || echo stopped"
                else:
                    return "stopped"
                
                result = await conn.run(cmd, check=False)
                return result.stdout.strip()
            
            return "unknown"
        except Exception as ex:
            _LOGGER.error("Ошибка проверки статуса %s: %s", service["name"], ex)
            return "unknown"

    async def _detect_engine(self, conn):
        
        try:
            result = await conn.run(
                "ps w | grep -E '[x]ray run|mihomo' | awk '{print $5}'",
                check=False
            )
            for line in result.stdout.strip().splitlines():
                if "mihomo" in line:
                    return "mihomo"
                elif "xray" in line:
                    return "xray"
            return None
        except Exception as ex:
            _LOGGER.warning("Ошибка определения движка: %s", ex)
            return None

    async def async_run_command(self, command):
        
        try:
            conn = await self._ensure_ssh_connection()
            result = await conn.run(command, check=False)
            return {
                "success": result.exit_status == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as ex:
            _LOGGER.error("Ошибка выполнения команды: %s", ex)
            return {"success": False, "error": str(ex)}
        finally:
            await self._async_ssh_close()