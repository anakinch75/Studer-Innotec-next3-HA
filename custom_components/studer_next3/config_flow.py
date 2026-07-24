"""Config flow for Studer Next1/Next3."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    CONF_MODEL,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODEL_DISPLAY_NAMES,
    MODEL_NEXT1,
    MODEL_NEXT3,
)
from .modbus_client import ModbusTcpClient, ModbusTcpError

_LOGGER = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 10

_MODEL_OPTIONS = [
    {"value": MODEL_NEXT3, "label": "Next3 (three-phase)"},
    {"value": MODEL_NEXT1, "label": "Next1 (single-phase)"},
]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MODEL, default=MODEL_NEXT3): SelectSelector(
            SelectSelectorConfig(options=_MODEL_OPTIONS, translation_key="model")
        ),
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=300)
        ),
    }
)


async def _test_connection(host: str, port: int) -> str | None:
    """Try to connect to the device. Return an error key or None if OK."""
    client = ModbusTcpClient(host, port, timeout=_CONNECT_TIMEOUT)
    try:
        ok = await client.connect()
        if not ok:
            return "cannot_connect"
        # Sanity read: battery SOC register on slave 1
        await client.read_holding_registers(8426, 2, 1)
        return None
    except ModbusTcpError:
        return "invalid_response"
    except (OSError, TimeoutError, asyncio.TimeoutError):
        return "cannot_connect"
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error testing connection to %s:%s", host, port)
        return "unknown"
    finally:
        client.close()


class StuderNext3ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup dialog."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the form and validate input."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            try:
                error = await _test_connection(host, port)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Config flow error for %s:%s", host, port)
                errors["base"] = "unknown"
            else:
                if error:
                    errors["base"] = error
                else:
                    model = user_input[CONF_MODEL]
                    model_label = MODEL_DISPLAY_NAMES[model]
                    return self.async_create_entry(
                        title=f"Studer {model_label} ({host})",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
