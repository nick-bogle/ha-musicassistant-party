"""Config flow for the Music Assistant Party Mode integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    MusicAssistantApiError,
    MusicAssistantAuthError,
    MusicAssistantCommandError,
    MusicAssistantConnectionError,
    MusicAssistantPartyClient,
)
from .const import (
    CONF_BASE_URL,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL): str,
        vol.Required(CONF_TOKEN): str,
    }
)


def _normalize_url(raw: str) -> str:
    """Normalize a user-supplied server URL."""
    url = raw.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


class MusicAssistantPartyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    async def _async_validate(
        self, base_url: str, token: str
    ) -> tuple[dict[str, str], dict[str, Any] | None]:
        """Validate connectivity, auth, and the party provider.

        Returns (errors, server_info).
        """
        client = MusicAssistantPartyClient(
            base_url, token, async_get_clientsession(self.hass)
        )
        try:
            server_info = await client.async_get_server_info()
        except MusicAssistantConnectionError:
            return {"base": "cannot_connect"}, None
        except MusicAssistantApiError:
            return {"base": "not_music_assistant"}, None

        try:
            await client.async_get_party_config()
        except MusicAssistantAuthError:
            return {"base": "invalid_auth"}, None
        except MusicAssistantCommandError:
            # Server reachable and token valid, but party provider missing.
            return {"base": "party_provider_missing"}, None
        except MusicAssistantApiError:
            return {"base": "cannot_connect"}, None

        return {}, server_info

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = _normalize_url(user_input[CONF_BASE_URL])
            token = user_input[CONF_TOKEN].strip()
            errors, server_info = await self._async_validate(base_url, token)
            if not errors and server_info is not None:
                await self.async_set_unique_id(server_info["server_id"])
                self._abort_if_unique_id_configured(
                    updates={CONF_BASE_URL: base_url}
                )
                return self.async_create_entry(
                    # Device name prefixes every entity name, so keep it
                    # short: "Music Assistant" + "Party URL", not a doubled
                    # "Music Assistant Party" + "Party URL".
                    title=server_info.get("name") or "Music Assistant",
                    data={CONF_BASE_URL: base_url, CONF_TOKEN: token},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth when the token is rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new token."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            errors, _ = await self._async_validate(
                reauth_entry.data[CONF_BASE_URL], token
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    reauth_entry, data_updates={CONF_TOKEN: token}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            description_placeholders={
                CONF_BASE_URL: reauth_entry.data[CONF_BASE_URL]
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> MusicAssistantPartyOptionsFlow:
        """Return the options flow."""
        return MusicAssistantPartyOptionsFlow()


class MusicAssistantPartyOptionsFlow(OptionsFlow):
    """Handle options (poll interval)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
                }
            ),
        )
