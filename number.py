"""Number platform for Tecnosystemi ProAir canal temperature."""

from __future__ import annotations

import logging
from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
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
    """Set up ProAir number entities."""
    coordinator = entry.runtime_data
    async_add_entities([ProAirCanalTempNumber(coordinator, entry)])


class ProAirCanalTempNumber(CoordinatorEntity[ProAirCoordinator], NumberEntity):
    """Number entity to set the canal temperature."""

    _attr_has_entity_name = True
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 10.0
    _attr_native_max_value = 45.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX
    _attr_translation_key = "canal_temperature_set"

    def __init__(
        self,
        coordinator: ProAirCoordinator,
        entry: ProAirConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        host = entry.data["host"]
        self._attr_unique_id = f"{host}_canal_temp_set"
        self._attr_name = "Canal temperature setpoint"

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
        """Return the current canal temperature setpoint."""
        return self.coordinator.data.temp_can

    async def async_set_native_value(self, value: float) -> None:
        """Set the canal temperature."""
        await self.hass.async_add_executor_job(
            self.coordinator.proair.set_canal_temperature, value
        )
        await self.coordinator.async_request_refresh()
