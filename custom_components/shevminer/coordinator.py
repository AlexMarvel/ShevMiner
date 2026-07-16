"""DataUpdateCoordinator for ShevMiner integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_API_KEY, CONF_PASSWORD, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN
from .xminer_client import XMinerClient, XMinerError

_LOGGER = logging.getLogger(__name__)


class ShevMinerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to poll data from the miner."""

    def __init__(self, hass: HomeAssistant, entry_data: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = XMinerClient(
            host=entry_data["host"],
            port=entry_data.get("port", DEFAULT_PORT),
            api_key=entry_data.get(CONF_API_KEY),
        )
        self._password = entry_data.get(CONF_PASSWORD)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the miner."""
        if self._password and not self.client._token:
            try:
                await self.hass.async_add_executor_job(self.client.unlock, self._password)
            except XMinerError:
                _LOGGER.warning("Failed to unlock miner with password")

        data: dict[str, Any] = {}

        try:
            data["info"] = await self.hass.async_add_executor_job(self.client.get_info)
        except XMinerError as exc:
            _LOGGER.debug("Error fetching info: %s", exc)

        try:
            data["status"] = await self.hass.async_add_executor_job(self.client.get_status)
        except XMinerError as exc:
            _LOGGER.debug("Error fetching status: %s", exc)

        try:
            data["summary"] = await self.hass.async_add_executor_job(self.client.get_summary)
        except XMinerError as exc:
            _LOGGER.debug("Error fetching summary: %s", exc)

        try:
            data["presets"] = await self.hass.async_add_executor_job(self.client.get_autotune_presets)
        except XMinerError as exc:
            _LOGGER.debug("Error fetching presets: %s", exc)

        try:
            data["perf"] = await self.hass.async_add_executor_job(self.client.get_perf_summary)
        except XMinerError as exc:
            _LOGGER.debug("Error fetching perf summary: %s", exc)

        if not data.get("info") and not data.get("status") and not data.get("summary"):
            raise UpdateFailed("Miner is not reachable")

        return data
