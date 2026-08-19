"""Number platform for Music Assistant Party Mode (limits and durations)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    KEY_ADD_QUEUE_LIMIT,
    KEY_ADD_QUEUE_REFILL_MINUTES,
    KEY_BOOST_LIMIT,
    KEY_BOOST_REFILL_MINUTES,
    KEY_PARTY_DURATION,
    KEY_SKIP_SONG_LIMIT,
    KEY_SKIP_SONG_REFILL_MINUTES,
)
from .coordinator import MusicAssistantPartyConfigEntry
from .entity import MusicAssistantPartySettingEntity


@dataclass(frozen=True, kw_only=True)
class PartyNumberDescription(NumberEntityDescription):
    """Number description with fallback bounds.

    The server reports the authoritative range per config entry; these
    fallbacks match the party provider defaults in case it does not.
    """

    fallback_min: float = 1
    fallback_max: float = 100


NUMBERS: tuple[PartyNumberDescription, ...] = (
    PartyNumberDescription(
        key=KEY_PARTY_DURATION,
        translation_key="party_duration",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.HOURS,
        fallback_min=1,
        fallback_max=168,
    ),
    PartyNumberDescription(
        key=KEY_ADD_QUEUE_LIMIT,
        translation_key="add_queue_limit",
        entity_category=EntityCategory.CONFIG,
        fallback_min=5,
        fallback_max=50,
    ),
    PartyNumberDescription(
        key=KEY_ADD_QUEUE_REFILL_MINUTES,
        translation_key="add_queue_refill_minutes",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        fallback_min=1,
        fallback_max=30,
    ),
    PartyNumberDescription(
        key=KEY_BOOST_LIMIT,
        translation_key="boost_limit",
        entity_category=EntityCategory.CONFIG,
        fallback_min=1,
        fallback_max=10,
    ),
    PartyNumberDescription(
        key=KEY_BOOST_REFILL_MINUTES,
        translation_key="boost_refill_minutes",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        fallback_min=5,
        fallback_max=120,
    ),
    PartyNumberDescription(
        key=KEY_SKIP_SONG_LIMIT,
        translation_key="skip_song_limit",
        entity_category=EntityCategory.CONFIG,
        fallback_min=1,
        fallback_max=5,
    ),
    PartyNumberDescription(
        key=KEY_SKIP_SONG_REFILL_MINUTES,
        translation_key="skip_song_refill_minutes",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        fallback_min=15,
        fallback_max=180,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MusicAssistantPartyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up numbers."""
    coordinator = entry.runtime_data
    async_add_entities(
        MusicAssistantPartyNumber(coordinator, description)
        for description in NUMBERS
    )


class MusicAssistantPartyNumber(MusicAssistantPartySettingEntity, NumberEntity):
    """A number backed by an integer party provider setting."""

    entity_description: PartyNumberDescription
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1

    def _server_range(self) -> tuple[float, float] | None:
        """Return the (min, max) range the server reports, if any."""
        entry = self.coordinator.data.entries.get(self.entity_description.key) or {}
        value_range = entry.get("range")
        if (
            isinstance(value_range, (list, tuple))
            and len(value_range) == 2
            and all(isinstance(v, (int, float)) for v in value_range)
        ):
            return float(value_range[0]), float(value_range[1])
        return None

    @property
    def native_min_value(self) -> float:
        """Return the minimum, preferring the server-reported range."""
        if server_range := self._server_range():
            return server_range[0]
        return self.entity_description.fallback_min

    @property
    def native_max_value(self) -> float:
        """Return the maximum, preferring the server-reported range."""
        if server_range := self._server_range():
            return server_range[1]
        return self.entity_description.fallback_max

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        value = self.coordinator.data.settings.get(self.entity_description.key)
        return float(value) if isinstance(value, (int, float)) else None

    async def async_set_native_value(self, value: float) -> None:
        """Save a new value."""
        await self._async_save(int(value))
