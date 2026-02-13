"""Costanti protocollo e builder comandi JSON per centralina ProAir."""

import json
from datetime import datetime

# --- Comandi protocollo ---
CMD_STATO = "stato"
CMD_STATO_R = "stato_r"
CMD_STATO_ZONA = "stato_zona"
CMD_STATO_SYNC = "stato_sync"
CMD_UPD_CU = "upd_cu"
CMD_UPD_ZONA = "upd_zona"
CMD_UPD_DATE = "upd_date"
CMD_UPD_FASCE = "upd_fasce"
CMD_CHECK_PIN = "check_pin"
CMD_CONFIG = "config"
CMD_GET_FASCE = "get_fasce"
CMD_SCAN_WIFI = "scan_wifi"

# --- Codici risposta ---
RES_OK = 1
RES_ERROR_PIN = 2
RES_CMD_NOT_FOUND = 4

# --- Campi JSON ---
JSON_C = "c"
JSON_PIN = "pin"
JSON_RES = "res"
JSON_IS_OFF = "is_off"
JSON_IS_COOL = "is_cool"
JSON_COOL_MOD = "cool_mod"
JSON_T_CAN = "t_can"
JSON_F_INV = "f_inv"
JSON_F_EST = "f_est"
JSON_ID_ZONA = "id_zona"
JSON_NAME = "name"
JSON_T = "t"
JSON_T_SET = "t_set"
JSON_FAN = "fan"
JSON_FAN_SET = "fan_set"
JSON_SHU = "shu"
JSON_SHU_SET = "shu_set"
JSON_EV = "EV"
JSON_IS_CRONO = "is_crono"
JSON_CRONO_ON = "crono_on"
JSON_UMD = "u"
JSON_UMD_SET = "u_set"
JSON_C_WIN = "c_win"
JSON_C_BADGE = "c_badge"
JSON_ERR = "err"
JSON_ERR_CU = "err_cu"
JSON_MASTER_NR = "master_nr"
JSON_IR_PRESENT = "ir_present"
JSON_ZONE = "zone"

# --- Valori fancoil/serranda ---
FAN_CLOSED = 0
FAN_SPEED_1 = 1
FAN_SPEED_2 = 2
FAN_SPEED_3 = 3
FAN_AUTO = 7
FAN_AUTO_WIRE = 16  # Valore 7 (AUTO) viene inviato come 16 sul protocollo

# --- Valori modalità operativa ---
OPERATING_COOLING = 1
OPERATING_DEHUMIDIFY = 2
OPERATING_VENTILATION = 3

# --- Rete ---
DEFAULT_IP = "10.0.0.1"
DEFAULT_PORT = 1235
DEFAULT_PIN = "2909"


def _fan_to_wire(value: int) -> int:
    """Converte valore fancoil/serranda per il protocollo (7 -> 16)."""
    return FAN_AUTO_WIRE if value == FAN_AUTO else value


def build_check_pin(pin: str = DEFAULT_PIN) -> str:
    """Costruisce comando check_pin."""
    return json.dumps({"c": CMD_CHECK_PIN, "pin": pin})


def build_get_stato(pin: str = DEFAULT_PIN) -> str:
    """Costruisce comando per leggere lo stato completo della centralina."""
    return json.dumps({"c": CMD_STATO, "pin": pin})


def build_get_stato_zona(pin: str = DEFAULT_PIN, zone_id: int = 1) -> str:
    """Costruisce comando per leggere lo stato di una zona."""
    return json.dumps({"c": CMD_STATO_ZONA, "pin": pin, "id_zona": zone_id})


def build_upd_cu(
    pin: str,
    is_off: bool,
    is_cooling: bool,
    operating_mode: int,
    t_can: float = 0.0,
    f_inv: int = 0,
    f_est: int = 0,
) -> str:
    """Costruisce comando upd_cu per aggiornare lo stato della centralina."""
    return json.dumps({
        "c": CMD_UPD_CU,
        "pin": pin,
        "is_off": 1 if is_off else 0,
        "is_cool": 1 if is_cooling else 0,
        "cool_mod": operating_mode,
        "t_can": int(t_can * 10),
        "f_inv": f_inv,
        "f_est": f_est,
    })


def build_upd_zona(
    pin: str,
    zone_id: int,
    name: str,
    is_off: bool,
    set_temp: float,
    fan_set: int,
    shu_set: int,
    is_crono: bool = False,
) -> str:
    """Costruisce comando upd_zona per aggiornare una zona."""
    return json.dumps({
        "c": CMD_UPD_ZONA,
        "pin": pin,
        "id_zona": zone_id,
        "name": name,
        "is_off": 1 if is_off else 0,
        "t_set": str(int(set_temp * 10)),
        "fan_set": _fan_to_wire(fan_set),
        "shu_set": _fan_to_wire(shu_set),
        "is_crono": 1 if is_crono else 0,
    })


def build_upd_date(pin: str, dt: datetime | None = None) -> str:
    """Costruisce comando upd_date per sincronizzare l'orologio."""
    if dt is None:
        dt = datetime.now()

    return json.dumps({
        "c": CMD_UPD_DATE,
        "pin": pin,
        "h24": 1,
        "day": dt.isoweekday(),
        "hour": dt.hour,
        "minute": dt.minute,
    })
