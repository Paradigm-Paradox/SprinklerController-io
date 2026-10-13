import os
import aiohttp
from typing import Optional, Dict, Any

SUPERVISOR_URL = os.environ.get("SUPERVISOR_URL", "http://supervisor/core/api")
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")

class HomeAssistantClient:
    def __init__(self, token: Optional[str] = None, base_url: Optional[str] = None):
        self.token = token or SUPERVISOR_TOKEN
        self.base_url = (base_url or SUPERVISOR_URL).rstrip("/")

    @property
    def is_connected(self) -> bool:
        return bool(self.token)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def get_entity_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected or not entity_id:
            return None

        url = f"{self.base_url}/states/{entity_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers(), timeout=5) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            print(f"Error fetching state for {entity_id}: {e}")
        return None

    async def call_service(self, domain: str, service: str, data: Dict[str, Any]) -> bool:
        if not self.is_connected:
            return False

        url = f"{self.base_url}/services/{domain}/{service}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers(), json=data, timeout=5) as resp:
                    return resp.status in (200, 201)
        except Exception as e:
            print(f"Error calling service {domain}.{service}: {e}")
            return False
