import os
import logging
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger("hydrocontrol.ha_client")

class HomeAssistantClient:
    def __init__(self):
        # In Home Assistant Add-ons with homeassistant_api: true,
        # SUPERVISOR_TOKEN provides direct authenticated access to the Core API
        self.token = os.environ.get("SUPERVISOR_TOKEN") or os.environ.get("HASSIO_TOKEN") or ""
        self.base_url = "http://supervisor/core/api" if self.token else "http://localhost:8123/api"
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        if not entity_id or not self.token:
            return None
        session = await self.get_session()
        url = f"{self.base_url}/states/{entity_id}"
        try:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("Failed to fetch state for %s: HTTP %s", entity_id, resp.status)
        except Exception as e:
            logger.debug("Error querying Home Assistant for entity %s: %s", entity_id, e)
        return None

    async def call_service(self, domain: str, service: str, service_data: Dict[str, Any]) -> bool:
        if not self.token:
            logger.info("Dry-run: Call service %s.%s with data %s (No token)", domain, service, service_data)
            return True
        session = await self.get_session()
        url = f"{self.base_url}/services/{domain}/{service}"
        try:
            async with session.post(url, json=service_data, timeout=5) as resp:
                if resp.status in (200, 201):
                    logger.info("Successfully called %s.%s: %s", domain, service, service_data)
                    return True
                logger.error("Service call %s.%s failed: HTTP %s", domain, service, resp.status)
        except Exception as e:
            logger.error("Error calling service %s.%s: %s", domain, service, e)
        return False
