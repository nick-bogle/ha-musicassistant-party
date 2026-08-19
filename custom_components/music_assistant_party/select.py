"""Select platform for Music Assistant Party Mode."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    KEY_BOOST_BADGE_COLOR,
    KEY_MODE,
    KEY_PLAYER,
    KEY_REQUEST_BADGE_COLOR,
)
from .coordinator import MusicAssistantPartyConfigEntry
from .entity import MusicAssistantPartySettingEntity

# Options come from the server (config entry option lists), so titles always
# match what the Music Assistant UI shows, including the live player list.
SELECTS: tuple[SelectEntityDescription, ...] = (
    SelectEntityDescription(
        key=KEY_MODE,
        translation_key="party_audio_mode",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key=KEY_PLAYER,
        translation_key="party_player",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key=KEY_REQUEST_BADGE_COLOR,
        translation_key="request_badge_color",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key=KEY_BOOST_BADGE_COLOR,
        translation_key="boost_badge_color",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MusicAssistantPartyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up selects."""
    coordinator = entry.runtime_data
    async_add_entities(
        MusicAssistantPartySelect(coordinator, description)
        for description in SELECTS
    )


class MusicAssistantPartySelect(MusicAssistantPartySettingEntity, SelectEntity):
    """A select backed by a provider setting with server-provided options."""

    @property
    def options(self) -> list[str]:
        """Return the option titles reported by the server."""
        return list(
            self.coordinator.data.option_titles(self.entity_description.key).values()
        )

    @property
    def current_option(self) -> str | None:
        """Return the title of the currently selected value."""
        data = self.coordinator.data
        value = data.settings.get(self.entity_description.key)
        if value is None:
            return None
        titles = data.option_titles(self.entity_description.key)
        # Fall back to the raw value so an out-of-list value stays visible.
        return titles.get(value, str(value))

    async def async_select_option(self, option: str) -> None:
        """Save the value whose title was selected."""
        titles = self.coordinator.data.option_titles(self.entity_description.key)
        for value, title in titles.items():
            if title == option:
                await self._async_save(value)
                return
        raise ServiceValidationError(
            f"{option} is not a valid option for {self.entity_id}"
        )
