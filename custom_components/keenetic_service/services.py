SERVICES = {
    "nfqws": {
        "id": "nfqws",
        "name": "NFQWS",
        "type": "script",
        "script": "S51nfqws",
        "status_cmd": "/opt/etc/init.d/S51nfqws status",
        "start_cmd": "/opt/etc/init.d/S51nfqws start",
        "stop_cmd": "/opt/etc/init.d/S51nfqws stop"
    },
    "xkeen": {
        "id": "xkeen",
        "name": "XRay Client",
        "type": "command",
        "start_cmd": "CONFDIR=/opt/etc/xray /opt/sbin/xkeen -start",
        "stop_cmd": "xkeen -stop",
        "status_cmd": "echo dynamic"  # Обрабатывается в координаторе
    }
}

AVAILABLE_SERVICES = {k: v["name"] for k, v in SERVICES.items()}