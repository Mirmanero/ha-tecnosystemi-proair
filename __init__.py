"""The Tecnosystemi ProAir integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_PIN, DOMAIN
from .coordinator import ProAirCoordinator
from .proair_lib import ProAir

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]

type ProAirConfigEntry = ConfigEntry[ProAirCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ProAirConfigEntry) -> bool:
    """Set up ProAir from a config entry."""
    proair = ProAir(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        pin=entry.data[CONF_PIN],
    )

    coordinator = ProAirCoordinator(hass, proair)

    # Primo fetch dei dati
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ProAirConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
