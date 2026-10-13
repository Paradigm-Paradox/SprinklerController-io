import os
import logging
from typing import Any, Dict, Optional
import aiohttp

logger = logging.getLogger("WasteControl.HAClient")

class HAClient:
    def __init__(self):
        self.token = os.environ.get("SUPERVISOR_TOKEN", "")
        self.base_url = "http://supervisor/core/api"
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        if not entity_id or not self.token:
            return None
        url = f"{self.base_url}/states/{entity_id}"
        try:
            session = await self._get_session()
            async with session.get(url, timeout=5.0) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    logger.warning(f"Entity not found in HA: {entity_id}")
                else:
                    logger.warning(f"Failed to fetch state for {entity_id}: HTTP {resp.status}")
        except Exception as e:
            logger.debug(f"Error fetching state for {entity_id}: {e}")
        return None

    async def call_service(self, domain: str, service: str, service_data: Dict[str, Any]) -> bool:
        if not self.token:
            return False
        url = f"{self.base_url}/services/{domain}/{service}"
        try:
            session = await self._get_session()
            async with session.post(url, json=service_data, timeout=5.0) as resp:
                if resp.status in (200, 201):
                    return True
                logger.warning(f"Failed service call {domain}.{service}: HTTP {resp.status}")
        except Exception as e:
            logger.error(f"Error calling service {domain}.{service}: {e}")
        return False

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
