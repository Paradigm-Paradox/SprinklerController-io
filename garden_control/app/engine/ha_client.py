import os
import logging
import aiohttp
from typing import Any, Dict, Optional

logger = logging.getLogger("gardencontrol.ha")

class HomeAssistantClient:
    """Client for interacting with Home Assistant Core via Supervisor API token."""

    def __init__(self):
        self.supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")
        self.ha_url = os.environ.get("HA_URL", "http://supervisor/core/api")
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.supervisor_token}",
                "Content-Type": "application/json"
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_entity_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Fetch current state & attributes for a specific entity."""
        if not entity_id:
            return None
        session = await self.get_session()
        url = f"{self.ha_url}/states/{entity_id}"
        try:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.debug("Entity %s returned status %d", entity_id, resp.status)
                return None
        except Exception as e:
            logger.debug("Failed fetching entity state %s: %s", entity_id, e)
            return None

    async def call_service(self, domain: str, service: str, service_data: Dict[str, Any]) -> bool:
        """Execute a service call against Home Assistant Core (e.g. switch.turn_on)."""
        session = await self.get_session()
        url = f"{self.ha_url}/services/{domain}/{service}"
        try:
            async with session.post(url, json=service_data, timeout=5) as resp:
                if resp.status in (200, 201):
                    return True
                logger.warning("Failed call service %s.%s: HTTP %d", domain, service, resp.status)
                return False
        except Exception as e:
            logger.warning("Error invoking service %s.%s: %s", domain, service, e)
            return False

    async def set_switch(self, entity_id: str, state: bool) -> bool:
        """Convenience method to turn a switch or valve on/off."""
        domain = entity_id.split(".")[0] if "." in entity_id else "switch"
        service = "turn_on" if state else "turn_off"
        return await self.call_service(domain, service, {"entity_id": entity_id})
