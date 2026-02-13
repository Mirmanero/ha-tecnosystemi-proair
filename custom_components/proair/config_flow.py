"""Config flow for Tecnosystemi ProAir integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import CONF_PIN, DEFAULT_PIN, DEFAULT_PORT, DOMAIN
from .proair_lib import ProAir
from .proair_lib.protocol.socket_client import SocketError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_PIN, default=DEFAULT_PIN): str,
    }
)


class ProAirConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ProAir."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            pin = user_input[CONF_PIN]

            # Unique ID basato su host (la centralina non ritorna un serial)
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            # Tenta connessione e verifica PIN
            proair = ProAir(host, port, pin)
            try:
                pin_ok = await self.hass.async_add_executor_job(proair.check_pin)
            except SocketError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                if not pin_ok:
                    errors["base"] = "invalid_auth"
                else:
                    return self.async_create_entry(
                        title=f"ProAir ({host})",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
