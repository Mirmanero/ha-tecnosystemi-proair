"""Select platform for Tecnosystemi ProAir operating mode."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ProAirConfigEntry
from .const import (
    CU_MODE_COOLING,
    CU_MODE_DEHUMIDIFY,
    CU_MODE_HEATING,
    CU_MODE_VENTILATION,
    DOMAIN,
)
from .coordinator import ProAirCoordinator
from .proair_lib.models.control_unit import (
    MODE_COOLING,
    MODE_DEHUMIDIFY,
    MODE_HEATING,
    MODE_VENTILATION,
)

_LOGGER = logging.getLogger(__name__)

# Mappatura opzione select -> (is_cooling, operating_mode)
SELECT_TO_CU = {
    CU_MODE_HEATING: (False, MODE_HEATING),
    CU_MODE_COOLING: (True, MODE_COOLING),
    CU_MODE_DEHUMIDIFY: (True, MODE_DEHUMIDIFY),
    CU_MODE_VENTILATION: (True, MODE_VENTILATION),
}

# Mappatura inversa: operating_mode -> opzione select
CU_TO_SELECT = {
    MODE_HEATING: CU_MODE_HEATING,
    MODE_COOLING: CU_MODE_COOLING,
    MODE_DEHUMIDIFY: CU_MODE_DEHUMIDIFY,
    MODE_VENTILATION: CU_MODE_VENTILATION,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ProAirConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ProAir select entities."""
    coordinator = entry.runtime_data
    async_add_entities([ProAirModeSelect(coordinator, entry)])


class ProAirModeSelect(CoordinatorEntity[ProAirCoordinator], SelectEntity):
    """Select entity for the CU operating mode."""

    _attr_has_entity_name = True
    _attr_options = [
        CU_MODE_HEATING,
        CU_MODE_COOLING,
        CU_MODE_DEHUMIDIFY,
        CU_MODE_VENTILATION,
    ]
    _attr_translation_key = "operating_mode"

    def __init__(
        self,
        coordinator: ProAirCoordinator,
        entry: ProAirConfigEntry,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        host = entry.data["host"]
        self._attr_unique_id = f"{host}_mode"
        self._attr_name = "Operating mode"

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
    def current_option(self) -> str | None:
        """Return the current operating mode."""
        cu = self.coordinator.data
        if cu.is_off:
            # Se spenta, ritorna comunque la modalità impostata
            if not cu.is_cooling:
                return CU_MODE_HEATING
            return CU_TO_SELECT.get(cu.operating_mode, CU_MODE_HEATING)
        if not cu.is_cooling:
            return CU_MODE_HEATING
        return CU_TO_SELECT.get(cu.operating_mode, CU_MODE_COOLING)

    async def async_select_option(self, option: str) -> None:
        """Set the operating mode."""
        proair = self.coordinator.proair

        if option == CU_MODE_HEATING:
            await self.hass.async_add_executor_job(proair.set_heating_mode)
        elif option == CU_MODE_COOLING:
            await self.hass.async_add_executor_job(proair.set_cooling_mode, 1)
        elif option == CU_MODE_DEHUMIDIFY:
            await self.hass.async_add_executor_job(proair.set_cooling_mode, 2)
        elif option == CU_MODE_VENTILATION:
            await self.hass.async_add_executor_job(proair.set_cooling_mode, 3)

        await self.coordinator.async_request_refresh()
