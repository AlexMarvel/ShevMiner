"""Button platform for ShevMiner integration."""
from __future__ import annotations

import logging
from collections.abc import Callable, Awaitable

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ShevMinerCoordinator
from .entity import ShevMinerEntity
from .xminer_client import XMinerError

_LOGGER = logging.getLogger(__name__)


class ShevMinerButton(ShevMinerEntity, ButtonEntity):
    """Button entity for ShevMiner actions."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: ShevMinerCoordinator,
        entry_id: str,
        key: str,
        translation_key: str,
        action: Callable[[], None],
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_translation_key = translation_key
        self._action = action

    async def async_press(self) -> None:
        """Press the button."""
        try:
            await self.hass.async_add_executor_job(self._action)
            await self.coordinator.async_request_refresh()
        except XMinerError as exc:
            _LOGGER.error("Button action failed: %s", exc)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ShevMiner buttons."""
    coordinator: ShevMinerCoordinator = hass.data[DOMAIN][entry.entry_id]
    client = coordinator.client

    async_add_entities([
        ShevMinerButton(
            coordinator, entry.entry_id,
            key="mining_restart",
            translation_key="mining_restart",
            action=client.mining_restart,
        ),
        ShevMinerButton(
            coordinator, entry.entry_id,
            key="mining_pause",
            translation_key="mining_pause",
            action=client.mining_pause,
        ),
        ShevMinerButton(
            coordinator, entry.entry_id,
            key="mining_resume",
            translation_key="mining_resume",
            action=client.mining_resume,
        ),
        ShevMinerButton(
            coordinator, entry.entry_id,
            key="reboot_miner",
            translation_key="reboot_miner",
            action=client.system_reboot,
        ),
    ])
