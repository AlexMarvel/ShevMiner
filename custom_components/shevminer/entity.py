"""Common entity classes for ShevMiner integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ShevMinerCoordinator


class ShevMinerEntity(CoordinatorEntity[ShevMinerCoordinator]):
    """Base entity for ShevMiner."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ShevMinerCoordinator, entry_id: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        info = coordinator.data.get("info") if coordinator.data else None
        serial = info.serial if info else "unknown"
        model = info.model if info else "ShevMiner"
        name = info.system.miner_name if info and info.system else "ShevMiner"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=name,
            manufacturer="Antminer / Vnish",
            model=model,
            sw_version=info.fw_version if info else None,
        )
        self._entry_id = entry_id
