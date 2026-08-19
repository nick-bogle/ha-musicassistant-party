"""Text platform for Music Assistant Party Mode."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import KEY_PARTY_NAME, KEY_QR_TEXT
from .coordinator import MusicAssistantPartyConfigEntry
from .entity import MusicAssistantPartySettingEntity

TEXTS: tuple[TextEntityDescription, ...] = (
    TextEntityDescription(
        key=KEY_PARTY_NAME,
        translation_key="party_name",
        entity_category=EntityCategory.CONFIG,
    ),
    TextEntityDescription(
        key=KEY_QR_TEXT,
        translation_key="qr_text",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MusicAssistantPartyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up text entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        MusicAssistantPartyText(coordinator, description) for description in TEXTS
    )


class MusicAssistantPartyText(MusicAssistantPartySettingEntity, TextEntity):
    """A text entity backed by a string party provider setting."""

    _attr_native_max = 255

    @property
    def native_value(self) -> str | None:
        """Return the current value (empty string shows as empty, not unknown)."""
        value = self.coordinator.data.settings.get(self.entity_description.key)
        return str(value) if value is not None else ""

    async def async_set_value(self, value: str) -> None:
        """Save a new value."""
        await self._async_save(value)
