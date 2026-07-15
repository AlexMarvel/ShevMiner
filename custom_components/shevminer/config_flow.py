"""Config flow for ShevMiner integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_API_KEY, CONF_PASSWORD, DEFAULT_PORT, DOMAIN
from .xminer_client import XMinerClient, XMinerError

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_PASSWORD): str,
        vol.Optional(CONF_API_KEY): str,
    }
)


async def _test_connection(hass, data: dict[str, Any]) -> bool:
    """Test connection to the miner."""
    client = XMinerClient(
        host=data[CONF_HOST],
        port=data.get(CONF_PORT, DEFAULT_PORT),
        api_key=data.get(CONF_API_KEY),
    )
    if data.get(CONF_PASSWORD):
        try:
            await hass.async_add_executor_job(client.unlock, data[CONF_PASSWORD])
        except XMinerError:
            pass
    try:
        await hass.async_add_executor_job(client.get_info)
    except XMinerError as exc:
        if exc.status_code in (401, 403):
            raise XMinerError("auth_failed", exc.status_code)
        raise
    return True


class ShevMinerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ShevMiner."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors: dict[str, str] = {}

        try:
            await _test_connection(self.hass, user_input)
        except XMinerError as exc:
            if "auth" in str(exc).lower() or exc.status_code in (401, 403):
                errors["base"] = "auth_failed"
            else:
                errors["base"] = "cannot_connect"
        except Exception:
            errors["base"] = "cannot_connect"
        else:
            host = user_input[CONF_HOST]
            await self.async_set_unique_id(f"{host}:{user_input.get(CONF_PORT, DEFAULT_PORT)}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"ShevMiner ({host})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
