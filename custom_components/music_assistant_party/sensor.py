"""Sensor platform for Music Assistant Party Mode."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import KEY_MODE, KEY_PLAYER
from .coordinator import MusicAssistantPartyConfigEntry
from .entity import MusicAssistantPartyEntity

PARTY_URL_DESCRIPTION = SensorEntityDescription(
    key="party_url",
    translation_key="party_url",
)

PARTY_PLAYER_DESCRIPTION = SensorEntityDescription(
    key="party_player",
    translation_key="party_player",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MusicAssistantPartyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            MusicAssistantPartyUrlSensor(coordinator, PARTY_URL_DESCRIPTION),
            MusicAssistantPartyPlayerSensor(coordinator, PARTY_PLAYER_DESCRIPTION),
        ]
    )


class MusicAssistantPartyUrlSensor(MusicAssistantPartyEntity, SensorEntity):
    """Exposes the guest access URL for the party."""

    @property
    def native_value(self) -> str | None:
        """Return the guest URL (None while guest access is off)."""
        return self.coordinator.data.party_url

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the join code and party context."""
        data = self.coordinator.data
        join_code: str | None = None
        if data.party_url:
            query = parse_qs(urlparse(data.party_url).query)
            join_code = (query.get("join") or [None])[0]
        return {
            "join_code": join_code,
            "guest_access_enabled": data.guest_access_enabled,
            "party_mode": data.settings.get(KEY_MODE),
            "party_name": data.settings.get("party_name") or None,
        }


class MusicAssistantPartyPlayerSensor(MusicAssistantPartyEntity, SensorEntity):
    """Shows which player/queue currently backs the party."""

    @property
    def native_value(self) -> str | None:
        """Return the friendly name of the active party player."""
        data = self.coordinator.data
        if not data.party_player_id:
            return None
        titles = data.option_titles(KEY_PLAYER)
        return titles.get(data.party_player_id, data.party_player_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the raw ids behind the friendly name."""
        data = self.coordinator.data
        return {
            "player_id": data.party_player_id,
            "configured_player": data.settings.get(KEY_PLAYER),
        }
