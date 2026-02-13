from __future__ import annotations
from dataclasses import dataclass, field

_POSITION_DEGREES = {0: "0°", 1: "30°", 2: "60°", 3: "90°"}


def _decode_actual(value: int) -> str:
    """Decodifica il valore attuale di serranda/fancoil.
    In auto il firmware aggiunge +16 ai valori (0→0, 1→17, 2→18, 3→19).
    """
    if value >= 16:
        base = value - 16
        deg = _POSITION_DEGREES.get(base, f"{base}")
        return f"{deg} [AUTO]"
    deg = _POSITION_DEGREES.get(value, f"{value}")
    return deg


def _set_label(value: int) -> str:
    if value == 0:
        return "AUTO"
    return f"Fisso {_POSITION_DEGREES.get(value, str(value))}"


@dataclass
class Zone:
    """Modello di una zona della centralina ProAir."""

    zone_id: int = 0
    name: str = ""
    is_off: bool = False
    temp: float = 0.0          # Temperatura attuale (°C)
    set_temp: float = 0.0      # Temperatura impostata (°C)
    serranda: int = 0          # Apertura serranda attuale
    serranda_set: int = 0      # Apertura serranda impostata
    fancoil: int = 0           # Velocità fancoil attuale
    fancoil_set: int = 0       # Velocità fancoil impostata
    ev: int = 0                # Stato elettrovalvola (-1=non presente, 0=off, 1=on)
    is_crono_mode: bool = False
    is_crono_active: bool = False
    umd: float = 0.0           # Umidità attuale (%)
    set_umd: float = 0.0      # Umidità impostata (%)
    c_win: int = 0             # Contatto finestra
    c_badge: int = 0           # Contatto badge
    c_off: int = 0             # Cut-off
    error: int = 0             # Bitmask errori

    @classmethod
    def from_status_json(cls, data: dict) -> Zone:
        """Parsea una zona dalla risposta JSON dello stato.

        Supporta sia il formato completo (stato) che ridotto (stato_r).
        """
        zone = cls()

        # Zone ID: "id_zona" in full, "nr" also present
        zone.zone_id = data.get("id_zona", data.get("nr", 0))

        # Name: "name" in full, "n" in reduced
        zone.name = data.get("name", data.get("n", ""))

        # Is off: "is_off" in full, "off" in reduced
        is_off_val = data.get("is_off", data.get("off", 0))
        zone.is_off = bool(is_off_val)

        # Temperature: always "t", value is x10
        zone.temp = data.get("t", 0) / 10.0

        # Set temperature: "t_set" in full, "ts" in reduced, value is x10
        zone.set_temp = data.get("t_set", data.get("ts", 0)) / 10.0

        # Fancoil
        zone.fancoil = data.get("fan", 0)
        zone.fancoil_set = data.get("fan_set", 0)

        # Serranda (shutter)
        zone.serranda = data.get("shu", 0)
        zone.serranda_set = data.get("shu_set", 0)

        # Elettrovalvola
        zone.ev = data.get("EV", 0)

        # Crono
        zone.is_crono_mode = bool(data.get("is_crono", 0))
        zone.is_crono_active = bool(data.get("crono_on", 0))

        # Umidità: "u" in full, "u" in reduced — valore x10
        raw_umd = data.get("u", 0)
        zone.umd = int(raw_umd) / 10.0 if raw_umd else 0.0
        # Umidità set: "u_set" in full, "us" in reduced — valore x10
        raw_umd_set = data.get("u_set", data.get("us", 0))
        zone.set_umd = int(raw_umd_set) / 10.0 if raw_umd_set else 0.0

        # Contatti: "c_win" in full, "w" in reduced
        zone.c_win = data.get("c_win", data.get("w", 0))
        # Badge: "c_badge" in full, "b" in reduced
        zone.c_badge = data.get("c_badge", data.get("b", 0))

        # Cut-off: only in reduced as "co"
        zone.c_off = data.get("co", 0)

        # Error
        zone.error = data.get("err", 0)

        return zone

    def short_str(self) -> str:
        """Rappresentazione compatta (per elenco da stato centralina).
        Mostra solo i dati affidabili: nome, on/off, temperature.
        """
        status = "OFF" if self.is_off else "ON"
        return (
            f"Zona {self.zone_id}: {self.name} [{status}] "
            f"T={self.temp:.1f}°C (set: {self.set_temp:.1f}°C)"
        )

    def __str__(self) -> str:
        """Rappresentazione completa (da stato_zona con dati reali)."""
        status = "OFF" if self.is_off else "ON"
        parts = [
            f"Zona {self.zone_id}: {self.name} [{status}]",
            f"  Temperatura: {self.temp:.1f}°C (set: {self.set_temp:.1f}°C)",
        ]
        if self.fancoil != -1:
            fan_mode = _set_label(self.fancoil_set)
            fan_actual = _decode_actual(self.fancoil)
            parts.append(f"  Fancoil: {fan_mode} (attuale: {fan_actual})")
        if self.serranda != -1:
            shu_mode = _set_label(self.serranda_set)
            shu_actual = _decode_actual(self.serranda)
            parts.append(f"  Serranda: {shu_mode} (attuale: {shu_actual})")
        if self.ev != -1:
            ev_label = {0: "OFF", 1: "ON"}.get(self.ev, str(self.ev))
            parts.append(f"  Elettrovalvola: {ev_label}")
        if self.umd > 0:
            umd_set_str = f" (set: {self.set_umd:.1f}%)" if self.set_umd > 0 else ""
            parts.append(f"  Umidita': {self.umd:.1f}%{umd_set_str}")
        if self.is_crono_mode:
            crono_st = "attivo" if self.is_crono_active else "inattivo"
            parts.append(f"  Crono: {crono_st}")
        if self.error:
            parts.append(f"  Errori: {self.error}")
        return "\n".join(parts)
