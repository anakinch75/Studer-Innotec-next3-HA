"""Tests for the config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.studer_next3.const import DOMAIN

USER_INPUT = {"host": "192.168.1.1", "port": 502, "scan_interval": 15}


async def test_form_shown_on_init(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_success_creates_entry(hass: HomeAssistant):
    with patch(
        "custom_components.studer_next3.config_flow._test_connection", return_value=None
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Studer Next3 (192.168.1.1)"
    assert result["data"] == USER_INPUT


async def test_cannot_connect_shows_error(hass: HomeAssistant):
    with patch(
        "custom_components.studer_next3.config_flow._test_connection",
        return_value="cannot_connect",
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_duplicate_entry_aborts(hass: HomeAssistant):
    with patch(
        "custom_components.studer_next3.config_flow._test_connection", return_value=None
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    with patch(
        "custom_components.studer_next3.config_flow._test_connection", return_value=None
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
