"""Switch platform for Music Assistant Party Mode."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    KEY_ANTI_BURN_IN,
    KEY_ENABLE_ADD_QUEUE,
    KEY_ENABLE_BOOST,
    KEY_ENABLE_GUEST_ACCESS,
    KEY_ENABLE_RATE_LIMITING,
    KEY_ENABLE_SKIP_SONG,
    KEY_HIDE_BACK_BUTTON,
    KEY_HIGHLIGHT_AHEAD,
    KEY_KARAOKE_MODE,
    KEY_PREVENT_DUPLICATE_TRACKS,
    KEY_SHOW_PROGRESS_BAR,
)
from .coordinator import MusicAssistantPartyConfigEntry
from .entity import MusicAssistantPartySettingEntity

# The master party mode switch is intentionally not a config-category entity:
# it is the main control of this integration.
MASTER_SWITCH = SwitchEntityDescription(
    key=KEY_ENABLE_GUEST_ACCESS,
    translation_key="party_mode",
)

SETTING_SWITCHES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key=KEY_ENABLE_ADD_QUEUE,
        translation_key="enable_add_queue",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key=KEY_ENABLE_BOOST,
        translation_key="enable_boost",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key=KEY_ENABLE_SKIP_SONG,
        translation_key="enable_skip_song",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key=KEY_ENABLE_RATE_LIMITING,
        translation_key="enable_rate_limiting",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key=KEY_PREVENT_DUPLICATE_TRACKS,
        translation_key="prevent_duplicate_tracks",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key=KEY_KARAOKE_MODE,
        translation_key="karaoke_mode",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key=KEY_HIGHLIGHT_AHEAD,
        translation_key="highlight_ahead",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key=KEY_ANTI_BURN_IN,
        translation_key="anti_burn_in",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key=KEY_HIDE_BACK_BUTTON,
        translation_key="hide_back_button",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key=KEY_SHOW_PROGRESS_BAR,
        translation_key="show_progress_bar",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MusicAssistantPartyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            MusicAssistantPartySwitch(coordinator, MASTER_SWITCH),
            *(
                MusicAssistantPartySwitch(coordinator, description)
                for description in SETTING_SWITCHES
            ),
        ]
    )


class MusicAssistantPartySwitch(MusicAssistantPartySettingEntity, SwitchEntity):
    """A switch backed by a boolean party provider setting."""

    @property
    def is_on(self) -> bool | None:
        """Return the current value."""
        value = self.coordinator.data.settings.get(self.entity_description.key)
        return bool(value) if value is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the setting."""
        await self._async_save(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the setting."""
        await self._async_save(False)
