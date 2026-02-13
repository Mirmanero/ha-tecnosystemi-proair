"""Switch platform for Tecnosystemi ProAir control unit."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
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
    """Set up ProAir switch entities."""
    coordinator = entry.runtime_data
    async_add_entities([ProAirPowerSwitch(coordinator, entry)])


class ProAirPowerSwitch(CoordinatorEntity[ProAirCoordinator], SwitchEntity):
    """Switch to turn the ProAir control unit on/off."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_translation_key = "power"

    def __init__(
        self,
        coordinator: ProAirCoordinator,
        entry: ProAirConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        host = entry.data["host"]
        self._attr_unique_id = f"{host}_power"
        self._attr_name = "Power"

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
    def is_on(self) -> bool:
        """Return true if the CU is on."""
        return not self.coordinator.data.is_off

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the CU on."""
        await self.hass.async_add_executor_job(self.coordinator.proair.set_cu_on)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the CU off."""
        await self.hass.async_add_executor_job(self.coordinator.proair.set_cu_off)
        await self.coordinator.async_request_refresh()
