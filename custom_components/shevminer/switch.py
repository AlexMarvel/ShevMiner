"""Switch platform for ShevMiner integration."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ShevMinerCoordinator
from .entity import ShevMinerEntity
from .xminer_client import XMinerError

_LOGGER = logging.getLogger(__name__)


class ShevMinerMiningSwitch(ShevMinerEntity, SwitchEntity):
    """Switch to control mining on/off."""

    _attr_translation_key = "mining"

    def __init__(self, coordinator: ShevMinerCoordinator, entry_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_mining"

    @property
    def is_on(self) -> bool | None:
        """Return true if mining is active."""
        status = self.coordinator.data.get("status") if self.coordinator.data else None
        if status:
            return status.miner_state == "mining"
        return None

    async def async_turn_on(self) -> None:
        """Start mining."""
        try:
            await self.hass.async_add_executor_job(self.coordinator.client.mining_start)
            await self.coordinator.async_request_refresh()
        except XMinerError as exc:
            _LOGGER.error("Failed to start mining: %s", exc)

    async def async_turn_off(self) -> None:
        """Stop mining."""
        try:
            await self.hass.async_add_executor_job(self.coordinator.client.mining_stop)
            await self.coordinator.async_request_refresh()
        except XMinerError as exc:
            _LOGGER.error("Failed to stop mining: %s", exc)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ShevMiner switch."""
    coordinator: ShevMinerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ShevMinerMiningSwitch(coordinator, entry.entry_id)])
