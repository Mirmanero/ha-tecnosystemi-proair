"""Constants for the Tecnosystemi ProAir integration."""

DOMAIN = "proair"
DEFAULT_PORT = 1235
DEFAULT_PIN = "0000"

CONF_PIN = "pin"

# Mappatura fan_mode HA <-> valore serranda
FAN_MODE_AUTO = "auto"
FAN_MODE_LOW = "low"
FAN_MODE_MEDIUM = "medium"
FAN_MODE_HIGH = "high"

HA_FAN_TO_DAMPER = {
    FAN_MODE_AUTO: 7,
    FAN_MODE_LOW: 1,
    FAN_MODE_MEDIUM: 2,
    FAN_MODE_HIGH: 3,
}

# Mappatura lettura: shu_set -> fan_mode HA
DAMPER_TO_HA_FAN = {
    0: FAN_MODE_AUTO,
    1: FAN_MODE_LOW,
    2: FAN_MODE_MEDIUM,
    3: FAN_MODE_HIGH,
}

# Modalità operative CU per il select
CU_MODE_HEATING = "heating"
CU_MODE_COOLING = "cooling"
CU_MODE_DEHUMIDIFY = "dehumidify"
CU_MODE_VENTILATION = "ventilation"
