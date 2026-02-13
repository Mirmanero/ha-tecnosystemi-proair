from __future__ import annotations
from dataclasses import dataclass, field

from .zone import Zone


# Costanti modalità operative
MODE_HEATING = 0        # Riscaldamento (is_cool=0)
MODE_COOLING = 1        # Raffrescamento (is_cool=1, cool_mod=1)
MODE_DEHUMIDIFY = 2     # Deumidificazione (is_cool=1, cool_mod=2)
MODE_VENTILATION = 3    # Ventilazione (is_cool=1, cool_mod=3)


@dataclass
class ControlUnit:
    """Modello della centralina ProAir."""

    serial: str = ""
    name: str = ""
    fw_ver: str = ""
    is_off: bool = False
    is_cooling: bool = False
    operating_mode: int = 0    # 0=risc, 1=raff, 2=deum, 3=vent
    ip: str = ""
    port: int = 1235
    pin: str = ""
    temp_can: float = 0.0     # Temperatura canale (°C)
    ir_present: bool = False
    f_inv: int = 0             # Frequenza invernale
    f_est: int = 0             # Frequenza estiva
    error_cu: int = 0          # Bitmask errori centralina
    master_nr: int = 0
    zones: list[Zone] = field(default_factory=list)

    @classmethod
    def from_status_json(cls, data: dict) -> ControlUnit:
        """Parsea la centralina dalla risposta JSON dello stato.

        Supporta sia il formato completo (stato) che ridotto (stato_r).
        """
        cu = cls()

        # Determina se è formato ridotto
        cmd = data.get("c", "")
        is_reduced = cmd == "stato_r"

        if is_reduced:
            cu.is_off = bool(data.get("off", 0))
            cu.is_cooling = bool(data.get("cl", 0))
            cu.operating_mode = data.get("cl_m", 0)
            cu.master_nr = data.get("m_nr", 0)
            cu.ir_present = bool(data.get("ir", 0))
            cu.temp_can = data.get("tc", 0) / 10.0
            cu.f_est = data.get("fe", 0)
            cu.f_inv = data.get("fi", 0)
        else:
            cu.is_off = bool(data.get("is_off", 0))
            cu.is_cooling = bool(data.get("is_cool", 0))
            cu.operating_mode = data.get("cool_mod", 0)
            cu.master_nr = data.get("master_nr", 0)
            cu.ir_present = bool(data.get("ir_present", 0))
            cu.temp_can = data.get("t_can", 0) / 10.0
            cu.f_est = data.get("f_est", 0)
            cu.f_inv = data.get("f_inv", 0)

        cu.error_cu = data.get("err_cu", 0)

        # Parse zone
        zones_data = data.get("zone", [])
        cu.zones = [Zone.from_status_json(z) for z in zones_data]

        return cu

    @property
    def mode_description(self) -> str:
        if self.is_off:
            return "SPENTA"
        if not self.is_cooling:
            return "RISCALDAMENTO"
        mode_map = {1: "RAFFRESCAMENTO", 2: "DEUMIDIFICAZIONE", 3: "VENTILAZIONE"}
        return mode_map.get(self.operating_mode, f"SCONOSCIUTO({self.operating_mode})")

    def __str__(self) -> str:
        status = "OFF" if self.is_off else "ON"
        lines = [
            f"Centralina [{status}] - Modo: {self.mode_description}",
            f"  T canale: {self.temp_can:.1f}°C | F.inv: {self.f_inv} | F.est: {self.f_est}",
            f"  IR: {'Si' if self.ir_present else 'No'} | Errori CU: {self.error_cu}",
            f"  Zone ({len(self.zones)}):",
        ]
        for z in self.zones:
            lines.append(f"    {z.short_str()}")
        return "\n".join(lines)
