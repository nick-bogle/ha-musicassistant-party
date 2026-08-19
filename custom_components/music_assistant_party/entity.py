"""Base entity for Music Assistant Party Mode."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import MusicAssistantApiError
from .const import DOMAIN
from .coordinator import MusicAssistantPartyCoordinator


class MusicAssistantPartyEntity(CoordinatorEntity[MusicAssistantPartyCoordinator]):
    """Common base for all party entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MusicAssistantPartyCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Music Assistant",
            model="Party plugin",
            sw_version=coordinator.server_info.get("server_version"),
            configuration_url=coordinator.client.base_url,
        )

    @property
    def available(self) -> bool:
        """Available while the coordinator updates and the provider is loaded."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.provider_status == "loaded"
        )


class MusicAssistantPartySettingEntity(MusicAssistantPartyEntity):
    """Base for entities backed by a single provider config value."""

    @property
    def available(self) -> bool:
        """Also require the backing setting to exist on the server."""
        return (
            super().available
            and self.entity_description.key in self.coordinator.data.settings
        )

    async def _async_save(self, value: object) -> None:
        """Persist a new value for this entity's config key."""
        try:
            await self.coordinator.async_set_setting(
                self.entity_description.key, value
            )
        except MusicAssistantApiError as err:
            raise HomeAssistantError(
                f"Failed to update {self.entity_description.key}: {err}"
            ) from err
