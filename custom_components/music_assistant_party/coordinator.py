"""Data update coordinator for Music Assistant Party Mode."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    MusicAssistantApiError,
    MusicAssistantAuthError,
    MusicAssistantPartyClient,
)
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    KEY_ENABLE_GUEST_ACCESS,
)

_LOGGER = logging.getLogger(__name__)

type MusicAssistantPartyConfigEntry = ConfigEntry[MusicAssistantPartyCoordinator]


@dataclass
class PartyData:
    """State fetched from the Music Assistant server."""

    settings: dict[str, Any] = field(default_factory=dict)
    entries: dict[str, dict[str, Any]] = field(default_factory=dict)
    party_url: str | None = None
    party_player_id: str | None = None
    provider_status: str | None = None
    provider_enabled: bool = False

    @property
    def guest_access_enabled(self) -> bool:
        """Return whether guest access (party mode) is currently on."""
        return bool(self.settings.get(KEY_ENABLE_GUEST_ACCESS))

    @classmethod
    def from_api(
        cls,
        provider_config: dict[str, Any],
        party_url: str | None,
        party_player_id: str | None,
    ) -> PartyData:
        """Build PartyData from the raw API responses."""
        entries: dict[str, dict[str, Any]] = {}
        settings: dict[str, Any] = {}
        raw_values = provider_config.get("values") or {}
        for key, entry in raw_values.items():
            if not isinstance(entry, dict):
                # Defensive: some server versions may return plain values.
                settings[key] = entry
                continue
            entries[key] = entry
            value = entry.get("value")
            if value is None:
                value = entry.get("default_value")
            settings[key] = value
        return cls(
            settings=settings,
            entries=entries,
            party_url=party_url,
            party_player_id=party_player_id,
            provider_status=provider_config.get("status"),
            provider_enabled=bool(provider_config.get("enabled")),
        )

    def option_titles(self, key: str) -> dict[str, str]:
        """Return value -> unique title mapping for a select-style entry."""
        entry = self.entries.get(key) or {}
        options = entry.get("options") or []
        titles: dict[str, str] = {}
        used: set[str] = set()
        for option in options:
            value = option.get("value")
            title = option.get("title") or str(value)
            if value is None:
                continue
            if title in used:
                title = f"{title} ({value})"
            used.add(title)
            titles[value] = title
        return titles


class MusicAssistantPartyCoordinator(DataUpdateCoordinator[PartyData]):
    """Poll the Music Assistant server for party state and settings."""

    config_entry: MusicAssistantPartyConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MusicAssistantPartyConfigEntry,
        client: MusicAssistantPartyClient,
        server_info: dict[str, Any],
    ) -> None:
        """Initialize the coordinator."""
        scan_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} ({config_entry.title})",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.server_info = server_info

    async def _async_update_data(self) -> PartyData:
        """Fetch party provider config and runtime party state."""
        try:
            provider_config, party_url, party_player_id = await asyncio.gather(
                self.client.async_get_provider_config(),
                self.client.async_get_party_url(),
                self.client.async_get_party_player(),
            )
        except MusicAssistantAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except MusicAssistantApiError as err:
            raise UpdateFailed(str(err)) from err

        return PartyData.from_api(provider_config, party_url, party_player_id)

    async def async_set_setting(self, key: str, value: Any) -> None:
        """Save one provider config value, update local state, and refresh."""
        await self.client.async_save_provider_values({key: value})
        # Optimistically reflect the change so the UI feels instant.
        if self.data is not None:
            self.data.settings[key] = value
            self.async_update_listeners()
        await self.async_request_refresh()
