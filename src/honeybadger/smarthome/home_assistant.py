import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from honeybadger.config import HOME_ASSISTANT_TOKEN, HOME_ASSISTANT_URL

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    def __init__(self, url: Optional[str] = None, token: Optional[str] = None) -> None:
        self.base_url = (url or HOME_ASSISTANT_URL).rstrip("/")
        self.token = token or HOME_ASSISTANT_TOKEN
        if not self.token:
            raise RuntimeError("Home Assistant token must be configured.")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def connect(self) -> bool:
        response = requests.get(f"{self.base_url}/api/", headers=self.headers, timeout=15)
        return response.status_code == 200

    def _call_service(self, domain: str, service: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/services/{domain}/{service}"
        response = requests.post(url, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def control_lights(
        self,
        action: str = "toggle",
        entity_id: Optional[str] = None,
        brightness: Optional[int] = None,
    ) -> Dict[str, Any]:
        if action not in {"on", "off", "toggle"}:
            raise ValueError("action must be 'on', 'off', or 'toggle'.")

        if action == "toggle" and not entity_id:
            raise ValueError("entity_id is required for toggle action.")

        if action == "toggle":
            service = "toggle"
            service_data = {"entity_id": entity_id}
        elif action == "on":
            service = "turn_on"
            service_data = {"entity_id": entity_id}
            if brightness is not None:
                service_data["brightness"] = brightness
        else:
            service = "turn_off"
            service_data = {"entity_id": entity_id}

        return self._call_service("light", service, service_data)

    def control_climate(
        self,
        action: str = "set_temperature",
        entity_id: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not entity_id:
            raise ValueError("entity_id is required for climate control.")

        if action == "set_temperature":
            if temperature is None:
                raise ValueError("temperature is required for set_temperature action.")
            return self._call_service(
                "climate",
                "set_temperature",
                {"entity_id": entity_id, "temperature": temperature},
            )

        if action == "turn_on":
            return self._call_service("climate", "turn_on", {"entity_id": entity_id})

        if action == "turn_off":
            return self._call_service("climate", "turn_off", {"entity_id": entity_id})

        raise ValueError("Unsupported climate action.")
