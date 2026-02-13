"""DataUpdateCoordinator for Tecnosystemi ProAir."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .proair_lib import ProAir, ProAirError
from .proair_lib.models import ControlUnit, Zone
from .proair_lib.protocol.socket_client import SocketError

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class ProAirCoordinator(DataUpdateCoordinator[ControlUnit]):
    """Coordinator per il polling dello stato della centralina ProAir."""

    def __init__(self, hass: HomeAssistant, proair: ProAir) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="ProAir",
            update_interval=SCAN_INTERVAL,
        )
        self.proair = proair

    async def _async_update_data(self) -> ControlUnit:
        """Fetch data from the centralina."""
        try:
            # get_status è bloccante, lo eseguiamo nel thread pool
            cu = await self.hass.async_add_executor_job(self.proair.get_status)
        except SocketError as err:
            raise UpdateFailed(f"Errore di comunicazione: {err}") from err
        except ProAirError as err:
            # Se il PIN è errato, segnala auth failure
            if "res=2" in str(err):
                raise ConfigEntryAuthFailed("PIN errato") from err
            raise UpdateFailed(f"Errore ProAir: {err}") from err

        # Aggiorna i dati dettagliati per ogni zona
        updated_zones: list[Zone] = []
        for zone in cu.zones:
            try:
                detailed = await self.hass.async_add_executor_job(
                    self.proair.get_zone_status, zone.zone_id
                )
                updated_zones.append(detailed)
            except (SocketError, ProAirError) as err:
                _LOGGER.warning(
                    "Impossibile leggere stato zona %d: %s", zone.zone_id, err
                )
                # Usa i dati base se il dettaglio fallisce
                updated_zones.append(zone)

        cu.zones = updated_zones
        return cu
