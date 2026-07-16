"""Sensor platform for ShevMiner integration."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfTemperature, UnitOfInformation, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ShevMinerCoordinator
from .entity import ShevMinerEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ShevMinerSensorDescription(SensorEntityDescription):
    """Describe ShevMiner sensor entity."""
    value_fn: Callable[[dict[str, Any]], Any]


MAIN_SENSORS: list[ShevMinerSensorDescription] = [
    ShevMinerSensorDescription(
        key="hashrate_realtime",
        translation_key="hashrate_realtime",
        native_unit_of_measurement="TH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: _gh_to_th(_get_miner(data, "hr_realtime")),
    ),
    ShevMinerSensorDescription(
        key="hashrate_average",
        translation_key="hashrate_average",
        native_unit_of_measurement="TH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: _gh_to_th(_get_miner(data, "hr_average")),
    ),
    ShevMinerSensorDescription(
        key="hashrate_nominal",
        translation_key="hashrate_nominal",
        native_unit_of_measurement="TH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: _gh_to_th(_get_miner(data, "hr_nominal")),
    ),
    ShevMinerSensorDescription(
        key="power_consumption",
        translation_key="power_consumption",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _get_miner(data, "power_consumption"),
    ),
    ShevMinerSensorDescription(
        key="power_efficiency",
        translation_key="power_efficiency",
        native_unit_of_measurement="J/TH",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: _get_miner(data, "power_efficiency"),
    ),
    ShevMinerSensorDescription(
        key="hw_errors",
        translation_key="hw_errors",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: _get_miner(data, "hw_errors"),
    ),
    ShevMinerSensorDescription(
        key="hw_errors_percent",
        translation_key="hw_errors_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _get_miner(data, "hw_errors_percent"),
    ),
    ShevMinerSensorDescription(
        key="chip_temp",
        translation_key="chip_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _get_temp_max(data, "chip_temp"),
    ),
    ShevMinerSensorDescription(
        key="pcb_temp",
        translation_key="pcb_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _get_temp_max(data, "pcb_temp"),
    ),
    ShevMinerSensorDescription(
        key="fan_duty",
        translation_key="fan_duty",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _get_cooling(data, "fan_duty"),
    ),
    ShevMinerSensorDescription(
        key="restart_count",
        translation_key="restart_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: _get_miner(data, "restart_count"),
    ),
    ShevMinerSensorDescription(
        key="miner_state",
        translation_key="miner_state",
        value_fn=lambda data: _get_status(data, "miner_state"),
    ),
]


def _gh_to_th(value: Any) -> Any:
    if value is None:
        return None
    return round(value / 1000)


def _get_miner(data: dict[str, Any], attr: str) -> Any:
    summary = data.get("summary")
    if summary and summary.miner:
        return getattr(summary.miner, attr, None)
    return None


def _get_status(data: dict[str, Any], attr: str) -> Any:
    status = data.get("status")
    if status:
        return getattr(status, attr, None)
    return None


def _get_temp_max(data: dict[str, Any], attr: str) -> Any:
    summary = data.get("summary")
    if summary and summary.miner:
        temp_range = getattr(summary.miner, attr, None)
        if temp_range:
            return temp_range.max
    return None


def _get_cooling(data: dict[str, Any], attr: str) -> Any:
    summary = data.get("summary")
    if summary and summary.miner and summary.miner.cooling:
        return getattr(summary.miner.cooling, attr, None)
    return None


class ShevMinerSensor(ShevMinerEntity, SensorEntity):
    """ShevMiner sensor entity."""

    def __init__(
        self,
        coordinator: ShevMinerCoordinator,
        entry_id: str,
        description: ShevMinerSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return None
        info = self.coordinator.data.get("info")
        summary = self.coordinator.data.get("summary")
        attrs: dict[str, Any] = {}
        if info:
            attrs["firmware"] = info.fw_version
            attrs["model"] = info.model
            attrs["serial"] = info.serial
            attrs["ip"] = info.system.network_status.ip if info.system else None
            attrs["hostname"] = info.system.network_status.hostname if info.system else None
            attrs["uptime"] = info.system.uptime if info.system else None
        if summary and summary.miner:
            m = summary.miner
            if m.miner_status:
                attrs["throttled"] = m.miner_status.throttled
                attrs["description"] = m.miner_status.description
            attrs["miner_type"] = m.miner_type
            if m.chip_temp:
                attrs["chip_temp_min"] = m.chip_temp.min
                attrs["chip_temp_max"] = m.chip_temp.max
            if m.pcb_temp:
                attrs["pcb_temp_min"] = m.pcb_temp.min
                attrs["pcb_temp_max"] = m.pcb_temp.max
            if m.cooling:
                attrs["fans"] = [
                    {"id": f.id, "rpm": f.rpm, "status": f.status}
                    for f in m.cooling.fans
                ]
        return attrs


class ShevMinerFanSensor(ShevMinerEntity, SensorEntity):
    """Individual fan RPM sensor."""

    def __init__(self, coordinator: ShevMinerCoordinator, entry_id: str, fan_index: int) -> None:
        """Initialize the fan sensor."""
        super().__init__(coordinator, entry_id)
        self._fan_index = fan_index
        self._attr_unique_id = f"{entry_id}_fan_{fan_index}_rpm"
        self._attr_name = f"Fan {fan_index} RPM"
        self._attr_native_unit_of_measurement = "RPM"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Any:
        """Return fan RPM."""
        if not self.coordinator.data:
            return None
        summary = self.coordinator.data.get("summary")
        if summary and summary.miner and summary.miner.cooling:
            fans = summary.miner.cooling.fans
            for fan in fans:
                if fan.id == self._fan_index:
                    return fan.rpm
        return None


class ShevMinerPoolSensor(ShevMinerEntity, SensorEntity):
    """Pool stats sensor."""

    def __init__(
        self,
        coordinator: ShevMinerCoordinator,
        entry_id: str,
        pool_id: int,
        stat_type: str,
    ) -> None:
        """Initialize the pool sensor."""
        super().__init__(coordinator, entry_id)
        self._pool_id = pool_id
        self._stat_type = stat_type
        self._attr_unique_id = f"{entry_id}_pool_{pool_id}_{stat_type}"
        stat_label = stat_type.capitalize()
        self._attr_name = f"Pool {pool_id} {stat_label}"

        if stat_type == "accepted" or stat_type == "rejected" or stat_type == "stale":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> Any:
        """Return pool stat."""
        if not self.coordinator.data:
            return None
        summary = self.coordinator.data.get("summary")
        if summary and summary.miner:
            for pool in summary.miner.pools:
                if pool.id == self._pool_id:
                    return getattr(pool, self._stat_type, None)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return pool attributes."""
        if not self.coordinator.data:
            return None
        summary = self.coordinator.data.get("summary")
        if summary and summary.miner:
            for pool in summary.miner.pools:
                if pool.id == self._pool_id:
                    return {
                        "url": pool.url,
                        "user": pool.user,
                        "status": pool.status,
                        "accepted": pool.accepted,
                        "rejected": pool.rejected,
                        "stale": pool.stale,
                        "diff": pool.diff,
                        "ping": pool.ping,
                    }
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ShevMiner sensors."""
    coordinator: ShevMinerCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ShevMinerSensor | ShevMinerFanSensor | ShevMinerPoolSensor] = []

    for description in MAIN_SENSORS:
        entities.append(ShevMinerSensor(coordinator, entry.entry_id, description))

    if coordinator.data and coordinator.data.get("summary"):
        summary = coordinator.data["summary"]
        if summary.miner and summary.miner.cooling:
            for fan in summary.miner.cooling.fans:
                entities.append(ShevMinerFanSensor(coordinator, entry.entry_id, fan.id))

        if summary.miner and summary.miner.pools:
            for pool in summary.miner.pools:
                for stat_type in ("accepted", "rejected", "stale", "status"):
                    entities.append(
                        ShevMinerPoolSensor(coordinator, entry.entry_id, pool.id, stat_type)
                    )

    async_add_entities(entities)
