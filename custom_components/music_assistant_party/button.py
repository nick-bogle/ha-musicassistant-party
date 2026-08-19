"""Button platform for Music Assistant Party Mode."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import MusicAssistantApiError
from .coordinator import MusicAssistantPartyConfigEntry
from .entity import MusicAssistantPartyEntity

SKIP_DESCRIPTION = ButtonEntityDescription(
    key="skip_track",
    translation_key="skip_track",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MusicAssistantPartyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up buttons."""
    async_add_entities(
        [MusicAssistantPartySkipButton(entry.runtime_data, SKIP_DESCRIPTION)]
    )


class MusicAssistantPartySkipButton(MusicAssistantPartyEntity, ButtonEntity):
    """Skips the currently playing track on the party queue."""

    async def async_press(self) -> None:
        """Skip the current track."""
        try:
            await self.coordinator.client.async_skip()
        except MusicAssistantApiError as err:
            raise HomeAssistantError(f"Failed to skip track: {err}") from err
