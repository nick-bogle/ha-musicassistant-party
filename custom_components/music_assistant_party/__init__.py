"""The Music Assistant Party Mode integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import (
    MusicAssistantApiError,
    MusicAssistantAuthError,
    MusicAssistantPartyClient,
)
from .const import (
    ATTR_BOOST,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_QUEUE_ITEM_ID,
    ATTR_URI,
    CONF_BASE_URL,
    CONF_TOKEN,
    DOMAIN,
    SERVICE_ADD_TO_QUEUE,
    SERVICE_BOOST_QUEUE_ITEM,
)
from .coordinator import MusicAssistantPartyConfigEntry, MusicAssistantPartyCoordinator

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_ADD_TO_QUEUE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_URI): cv.string,
        vol.Optional(ATTR_BOOST, default=False): cv.boolean,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)

SERVICE_BOOST_QUEUE_ITEM_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_QUEUE_ITEM_ID): cv.string,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)


def _resolve_coordinator(
    hass: HomeAssistant, call: ServiceCall
) -> MusicAssistantPartyCoordinator:
    """Find the coordinator targeted by a service call."""
    entries: list[MusicAssistantPartyConfigEntry] = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if entry_id := call.data.get(ATTR_CONFIG_ENTRY_ID):
        for entry in entries:
            if entry.entry_id == entry_id:
                return entry.runtime_data
        raise ServiceValidationError(
            f"No loaded {DOMAIN} config entry with id {entry_id}"
        )
    if not entries:
        raise ServiceValidationError(
            "Music Assistant Party Mode is not set up"
        )
    if len(entries) > 1:
        raise ServiceValidationError(
            "Multiple Music Assistant servers are configured; "
            f"pass {ATTR_CONFIG_ENTRY_ID} to select one"
        )
    return entries[0].runtime_data


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register domain services."""

    async def _handle_add_to_queue(call: ServiceCall) -> ServiceResponse:
        coordinator = _resolve_coordinator(hass, call)
        try:
            result = await coordinator.client.async_add_to_queue(
                call.data[ATTR_URI], call.data[ATTR_BOOST]
            )
        except MusicAssistantApiError as err:
            raise HomeAssistantError(str(err)) from err
        if call.return_response:
            return result if isinstance(result, dict) else {"result": result}
        return None

    async def _handle_boost_queue_item(call: ServiceCall) -> ServiceResponse:
        coordinator = _resolve_coordinator(hass, call)
        try:
            result = await coordinator.client.async_boost_queue_item(
                call.data[ATTR_QUEUE_ITEM_ID]
            )
        except MusicAssistantApiError as err:
            raise HomeAssistantError(str(err)) from err
        if call.return_response:
            return result if isinstance(result, dict) else {"result": result}
        return None

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TO_QUEUE,
        _handle_add_to_queue,
        schema=SERVICE_ADD_TO_QUEUE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BOOST_QUEUE_ITEM,
        _handle_boost_queue_item,
        schema=SERVICE_BOOST_QUEUE_ITEM_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: MusicAssistantPartyConfigEntry
) -> bool:
    """Set up Music Assistant Party Mode from a config entry."""
    client = MusicAssistantPartyClient(
        entry.data[CONF_BASE_URL],
        entry.data[CONF_TOKEN],
        async_get_clientsession(hass),
    )

    try:
        server_info = await client.async_get_server_info()
        # Verify the token and the party provider in one call.
        await client.async_get_party_config()
    except MusicAssistantAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except MusicAssistantApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = MusicAssistantPartyCoordinator(hass, entry, client, server_info)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: MusicAssistantPartyConfigEntry
) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: MusicAssistantPartyConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
