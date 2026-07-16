"""Select platform for ShevMiner integration."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ShevMinerCoordinator
from .entity import ShevMinerEntity
from .xminer_client import XMinerError

_LOGGER = logging.getLogger(__name__)


class ShevMinerPresetSelect(ShevMinerEntity, SelectEntity):
    """Select entity for autotune presets."""

    _attr_translation_key = "preset"

    def __init__(self, coordinator: ShevMinerCoordinator, entry_id: str) -> None:
        """Initialize the select."""
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_preset"
        self._attr_options: list[str] = []

    @property
    def options(self) -> list[str]:
        """Return available presets."""
        if self.coordinator.data and self.coordinator.data.get("presets"):
            return [p.name for p in self.coordinator.data["presets"]]
        return []

    @property
    def current_option(self) -> str | None:
        """Return the current preset."""
        if self.coordinator.data:
            perf = self.coordinator.data.get("perf")
            if perf and perf.current_preset:
                return perf.current_preset.name
        return None

    async def async_select_option(self, option: str) -> None:
        """Select a preset."""
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.client.save_settings,
                {"miner": {"overclock": {"preset": option}}},
            )
            await self.coordinator.async_request_refresh()
        except XMinerError as exc:
            _LOGGER.error("Failed to set preset %s: %s", option, exc)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ShevMiner select."""
    coordinator: ShevMinerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ShevMinerPresetSelect(coordinator, entry.entry_id)])
