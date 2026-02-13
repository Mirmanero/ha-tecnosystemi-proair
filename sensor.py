"""Sensor platform for Tecnosystemi ProAir."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ProAirConfigEntry
from .const import DOMAIN
from .coordinator import ProAirCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ProAirConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ProAir sensor entities."""
    coordinator = entry.runtime_data
    cu = coordinator.data
    host = entry.data["host"]

    entities: list[SensorEntity] = []

    # Sensore temperatura canale (CU)
    entities.append(ProAirCanalTempSensor(coordinator, entry))

    # Sensori per ogni zona
    for zone in cu.zones:
        entities.append(ProAirZoneTempSensor(coordinator, entry, zone.zone_id))
        entities.append(ProAirZoneHumiditySensor(coordinator, entry, zone.zone_id))

    async_add_entities(entities)


class ProAirCanalTempSensor(CoordinatorEntity[ProAirCoordinator], SensorEntity):
    """Sensor for canal temperature of the control unit."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_translation_key = "canal_temperature"

    def __init__(
        self,
        coordinator: ProAirCoordinator,
        entry: ProAirConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        host = entry.data["host"]
        self._attr_unique_id = f"{host}_canal_temp"
        self._attr_name = "Canal temperature"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for the control unit."""
        host = self.coordinator.proair.host
        return DeviceInfo(
            identifiers={(DOMAIN, host)},
            name="ProAir Centralina",
            manufacturer="Tecnosystemi",
            model="ProAir",
        )

    @property
    def native_value(self) -> float | None:
        """Return the canal temperature."""
        return self.coordinator.data.temp_can


class ProAirZoneTempSensor(CoordinatorEntity[ProAirCoordinator], SensorEntity):
    """Sensor for zone temperature."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_translation_key = "zone_temperature"

    def __init__(
        self,
        coordinator: ProAirCoordinator,
        entry: ProAirConfigEntry,
        zone_id: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        host = entry.data["host"]
        self._zone_id = zone_id
        self._attr_unique_id = f"{host}_{zone_id}_temp"
        self._attr_name = "Temperature"

    @property
    def _zone(self):
        """Get the zone data from coordinator."""
        for z in self.coordinator.data.zones:
            if z.zone_id == self._zone_id:
                return z
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this zone."""
        host = self.coordinator.proair.host
        zone = self._zone
        zone_name = zone.name if zone else f"Zone {self._zone_id}"
        return DeviceInfo(
            identifiers={(DOMAIN, f"{host}_zone_{self._zone_id}")},
            name=f"ProAir {zone_name}",
            manufacturer="Tecnosystemi",
            model="ProAir Zone",
            via_device=(DOMAIN, host),
        )

    @property
    def native_value(self) -> float | None:
        """Return the zone temperature."""
        zone = self._zone
        return zone.temp if zone else None


class ProAirZoneHumiditySensor(CoordinatorEntity[ProAirCoordinator], SensorEntity):
    """Sensor for zone humidity."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_translation_key = "zone_humidity"

    def __init__(
        self,
        coordinator: ProAirCoordinator,
        entry: ProAirConfigEntry,
        zone_id: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        host = entry.data["host"]
        self._zone_id = zone_id
        self._attr_unique_id = f"{host}_{zone_id}_humidity"
        self._attr_name = "Humidity"

    @property
    def _zone(self):
        """Get the zone data from coordinator."""
        for z in self.coordinator.data.zones:
            if z.zone_id == self._zone_id:
                return z
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this zone."""
        host = self.coordinator.proair.host
        zone = self._zone
        zone_name = zone.name if zone else f"Zone {self._zone_id}"
        return DeviceInfo(
            identifiers={(DOMAIN, f"{host}_zone_{self._zone_id}")},
            name=f"ProAir {zone_name}",
            manufacturer="Tecnosystemi",
            model="ProAir Zone",
            via_device=(DOMAIN, host),
        )

    @property
    def native_value(self) -> float | None:
        """Return the zone humidity."""
        zone = self._zone
        if zone and zone.umd > 0:
            return zone.umd
        return None
