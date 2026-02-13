"""Classe facade ProAir per comunicazione locale con centralina Tecnosystemi.

Fornisce un'API ad alto livello per controllare la centralina via TCP socket locale.
"""

import logging
from datetime import datetime

from .models import ControlUnit, Zone
from .protocol.commands import (
    DEFAULT_PIN,
    DEFAULT_PORT,
    RES_OK,
    build_check_pin,
    build_get_stato,
    build_get_stato_zona,
    build_upd_cu,
    build_upd_date,
    build_upd_zona,
)
from .protocol.socket_client import SocketClient, SocketError

logger = logging.getLogger(__name__)


class ProAirError(Exception):
    """Errore nella comunicazione con la centralina ProAir."""
    pass


class ProAir:
    """Interfaccia ad alto livello per la centralina ProAir."""

    def __init__(self, host: str, port: int = DEFAULT_PORT, pin: str = DEFAULT_PIN):
        self.host = host
        self.port = port
        self.pin = pin
        self._client = SocketClient(host, port)
        self._last_status: ControlUnit | None = None

    def check_pin(self) -> bool:
        """Verifica che il PIN sia corretto."""
        cmd = build_check_pin(self.pin)
        try:
            resp = self._client.send_command(cmd)
            return resp.get("res") == RES_OK
        except SocketError:
            return False

    def get_status(self) -> ControlUnit:
        """Legge lo stato completo della centralina e di tutte le zone."""
        cmd = build_get_stato(self.pin)
        resp = self._client.send_command(cmd)
        cu = ControlUnit.from_status_json(resp)
        cu.pin = self.pin
        cu.ip = self.host
        cu.port = self.port
        self._last_status = cu
        return cu

    def get_zone_status(self, zone_id: int) -> Zone:
        """Legge lo stato di una singola zona."""
        cmd = build_get_stato_zona(self.pin, zone_id)
        resp = self._client.send_command(cmd)

        if "zone" in resp:
            zones = resp["zone"]
            if zones:
                return Zone.from_status_json(zones[0])
        return Zone.from_status_json(resp)

    def _send_and_check(self, cmd: str) -> dict:
        """Invia un comando e verifica che res == 1."""
        resp = self._client.send_command(cmd)
        if resp.get("res") != RES_OK:
            raise ProAirError(
                f"Comando fallito: res={resp.get('res')} - risposta: {resp}"
            )
        return resp

    def _get_current_status(self) -> ControlUnit:
        """Ritorna l'ultimo stato noto, o lo legge se non disponibile."""
        if self._last_status is None:
            self._last_status = self.get_status()
        return self._last_status

    # --- Comandi centralina ---

    def set_cu_on(self) -> None:
        """Accende la centralina."""
        cu = self._get_current_status()
        cmd = build_upd_cu(
            pin=self.pin,
            is_off=False,
            is_cooling=cu.is_cooling,
            operating_mode=cu.operating_mode,
            t_can=cu.temp_can,
            f_inv=cu.f_inv,
            f_est=cu.f_est,
        )
        self._send_and_check(cmd)
        self._last_status = None

    def set_cu_off(self) -> None:
        """Spegne la centralina."""
        cu = self._get_current_status()
        cmd = build_upd_cu(
            pin=self.pin,
            is_off=True,
            is_cooling=cu.is_cooling,
            operating_mode=cu.operating_mode,
            t_can=cu.temp_can,
            f_inv=cu.f_inv,
            f_est=cu.f_est,
        )
        self._send_and_check(cmd)
        self._last_status = None

    def set_canal_temperature(self, temp_celsius: float) -> None:
        """Imposta la temperatura del canale."""
        cu = self._get_current_status()
        cmd = build_upd_cu(
            pin=self.pin,
            is_off=cu.is_off,
            is_cooling=cu.is_cooling,
            operating_mode=cu.operating_mode,
            t_can=temp_celsius,
            f_inv=cu.f_inv,
            f_est=cu.f_est,
        )
        self._send_and_check(cmd)
        self._last_status = None

    def set_cooling_mode(self, mode: int) -> None:
        """Imposta la modalità estiva (1=raff, 2=deum, 3=vent)."""
        if mode not in (1, 2, 3):
            raise ValueError("Modalità non valida: usa 1=raff, 2=deum, 3=vent")
        cu = self._get_current_status()
        cmd = build_upd_cu(
            pin=self.pin,
            is_off=cu.is_off,
            is_cooling=True,
            operating_mode=mode,
            t_can=cu.temp_can,
            f_inv=cu.f_inv,
            f_est=cu.f_est,
        )
        self._send_and_check(cmd)
        self._last_status = None

    def set_heating_mode(self) -> None:
        """Imposta la modalità riscaldamento (invernale)."""
        cu = self._get_current_status()
        cmd = build_upd_cu(
            pin=self.pin,
            is_off=cu.is_off,
            is_cooling=False,
            operating_mode=0,
            t_can=cu.temp_can,
            f_inv=cu.f_inv,
            f_est=cu.f_est,
        )
        self._send_and_check(cmd)
        self._last_status = None

    # --- Comandi zona ---

    def _get_zone_from_status(self, zone_id: int) -> Zone:
        """Trova una zona nello stato corrente della centralina."""
        cu = self._get_current_status()
        for z in cu.zones:
            if z.zone_id == zone_id:
                return z
        raise ProAirError(f"Zona {zone_id} non trovata")

    def _update_zone(self, zone: Zone, **overrides) -> None:
        """Invia upd_zona con i valori della zona, sovrascrivendo quelli specificati."""
        params = {
            "pin": self.pin,
            "zone_id": zone.zone_id,
            "name": zone.name,
            "is_off": zone.is_off,
            "set_temp": zone.set_temp,
            "fan_set": zone.fancoil_set,
            "shu_set": zone.serranda_set,
            "is_crono": zone.is_crono_mode,
        }
        params.update(overrides)
        cmd = build_upd_zona(**params)
        self._send_and_check(cmd)
        self._last_status = None

    def set_zone_temperature(self, zone_id: int, temp_celsius: float) -> None:
        """Imposta la temperatura target di una zona."""
        zone = self._get_zone_from_status(zone_id)
        self._update_zone(zone, set_temp=temp_celsius)

    def set_zone_on(self, zone_id: int) -> None:
        """Accende una zona."""
        zone = self._get_zone_from_status(zone_id)
        self._update_zone(zone, is_off=False)

    def set_zone_off(self, zone_id: int) -> None:
        """Spegne una zona."""
        zone = self._get_zone_from_status(zone_id)
        self._update_zone(zone, is_off=True)

    def set_zone_fancoil(self, zone_id: int, speed: int) -> None:
        """Imposta la velocità del fancoil di una zona (0, 1, 2, 3, 7=auto)."""
        if speed not in (0, 1, 2, 3, 7):
            raise ValueError("Velocità fancoil non valida: usa 0, 1, 2, 3 o 7(auto)")
        zone = self._get_zone_from_status(zone_id)
        self._update_zone(zone, fan_set=speed)

    def set_zone_damper(self, zone_id: int, opening: int) -> None:
        """Imposta l'apertura della serranda di una zona (0, 1, 2, 3, 7=auto)."""
        if opening not in (0, 1, 2, 3, 7):
            raise ValueError("Apertura serranda non valida: usa 0, 1, 2, 3 o 7(auto)")
        zone = self._get_zone_from_status(zone_id)
        self._update_zone(zone, shu_set=opening)

    def update_datetime(self, dt: datetime | None = None) -> None:
        """Sincronizza l'orologio della centralina."""
        cmd = build_upd_date(self.pin, dt)
        self._send_and_check(cmd)
