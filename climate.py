"""Climate platform for Tecnosystemi ProAir zones."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ProAirConfigEntry
from .const import (
    DAMPER_TO_HA_FAN,
    DOMAIN,
    FAN_MODE_AUTO,
    FAN_MODE_HIGH,
    FAN_MODE_LOW,
    FAN_MODE_MEDIUM,
    HA_FAN_TO_DAMPER,
)
from .coordinator import ProAirCoordinator
from .proair_lib.models.control_unit import (
    MODE_COOLING,
    MODE_DEHUMIDIFY,
    MODE_HEATING,
    MODE_VENTILATION,
)

_LOGGER = logging.getLogger(__name__)

# Mappatura modalità CU -> HVACMode
CU_MODE_TO_HVAC = {
    MODE_HEATING: HVACMode.HEAT,
    MODE_COOLING: HVACMode.COOL,
    MODE_DEHUMIDIFY: HVACMode.DRY,
    MODE_VENTILATION: HVACMode.FAN_ONLY,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ProAirConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ProAir climate entities."""
    coordinator = entry.runtime_data
    cu = coordinator.data

    entities = [
        ProAirClimate(coordinator, entry, zone.zone_id)
        for zone in cu.zones
    ]
    async_add_entities(entities)


class ProAirClimate(CoordinatorEntity[ProAirCoordinator], ClimateEntity):
    """Climate entity for a ProAir zone."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 10.0
    _attr_max_temp = 35.0
    _attr_target_temperature_step = 0.5
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = [FAN_MODE_AUTO, FAN_MODE_LOW, FAN_MODE_MEDIUM, FAN_MODE_HIGH]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _enable_turn_on_off_backwards_compat = False

    def __init__(
        self,
        coordinator: ProAirCoordinator,
        entry: ProAirConfigEntry,
        zone_id: int,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._attr_unique_id = f"{entry.data['host']}_{zone_id}_climate"
        self._attr_translation_key = "zone_climate"

    @property
    def _zone(self):
        """Get the zone data from coordinator."""
        for z in self.coordinator.data.zones:
            if z.zone_id == self._zone_id:
                return z
        return None

    @property
    def _cu(self):
        """Get the control unit data from coordinator."""
        return self.coordinator.data

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        zone = self._zone
        if zone:
            return zone.name
        return f"Zone {self._zone_id}"

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
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        zone = self._zone
        cu = self._cu
        if not zone or not cu:
            return HVACMode.OFF
        if cu.is_off or zone.is_off:
            return HVACMode.OFF
        return CU_MODE_TO_HVAC.get(cu.operating_mode, HVACMode.HEAT)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        zone = self._zone
        return zone.temp if zone else None

    @property
    def current_humidity(self) -> float | None:
        """Return the current humidity."""
        zone = self._zone
        return zone.umd if zone and zone.umd > 0 else None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        zone = self._zone
        return zone.set_temp if zone else None

    @property
    def fan_mode(self) -> str | None:
        """Return the current fan mode based on damper setting."""
        zone = self._zone
        if not zone:
            return None
        return DAMPER_TO_HA_FAN.get(zone.serranda_set, FAN_MODE_AUTO)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        await self.hass.async_add_executor_job(
            self.coordinator.proair.set_zone_temperature, self._zone_id, temp
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        proair = self.coordinator.proair

        if hvac_mode == HVACMode.OFF:
            await self.hass.async_add_executor_job(
                proair.set_zone_off, self._zone_id
            )
        elif hvac_mode == HVACMode.HEAT:
            # Accendi zona + CU + imposta riscaldamento
            await self.hass.async_add_executor_job(proair.set_heating_mode)
            await self.hass.async_add_executor_job(proair.set_cu_on)
            await self.hass.async_add_executor_job(
                proair.set_zone_on, self._zone_id
            )
        elif hvac_mode == HVACMode.COOL:
            await self.hass.async_add_executor_job(proair.set_cooling_mode, 1)
            await self.hass.async_add_executor_job(proair.set_cu_on)
            await self.hass.async_add_executor_job(
                proair.set_zone_on, self._zone_id
            )
        elif hvac_mode == HVACMode.DRY:
            await self.hass.async_add_executor_job(proair.set_cooling_mode, 2)
            await self.hass.async_add_executor_job(proair.set_cu_on)
            await self.hass.async_add_executor_job(
                proair.set_zone_on, self._zone_id
            )
        elif hvac_mode == HVACMode.FAN_ONLY:
            await self.hass.async_add_executor_job(proair.set_cooling_mode, 3)
            await self.hass.async_add_executor_job(proair.set_cu_on)
            await self.hass.async_add_executor_job(
                proair.set_zone_on, self._zone_id
            )

        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode (maps to damper opening)."""
        damper_value = HA_FAN_TO_DAMPER.get(fan_mode, 7)
        await self.hass.async_add_executor_job(
            self.coordinator.proair.set_zone_damper, self._zone_id, damper_value
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the zone on."""
        await self.hass.async_add_executor_job(
            self.coordinator.proair.set_zone_on, self._zone_id
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the zone off."""
        await self.hass.async_add_executor_job(
            self.coordinator.proair.set_zone_off, self._zone_id
        )
        await self.coordinator.async_request_refresh()
