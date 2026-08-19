"""Async client for the Music Assistant HTTP RPC API (party provider)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import aiohttp

from .const import DEFAULT_TIMEOUT, PARTY_PROVIDER_DOMAIN, PARTY_PROVIDER_INSTANCE_ID


class MusicAssistantApiError(Exception):
    """Base error talking to the Music Assistant API."""


class MusicAssistantConnectionError(MusicAssistantApiError):
    """Could not reach the Music Assistant server."""


class MusicAssistantAuthError(MusicAssistantApiError):
    """Token was rejected by the Music Assistant server."""


class MusicAssistantCommandError(MusicAssistantApiError):
    """The server rejected the command (4xx/5xx with an error message)."""


class MusicAssistantPartyClient:
    """Minimal Music Assistant API client focused on the party provider.

    Uses the HTTP RPC endpoint (POST {base_url}/api with a JSON command)
    rather than the websocket, which keeps the integration dependency-free.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the client."""
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._session = session

    @property
    def base_url(self) -> str:
        """Return the server base URL."""
        return self._base_url

    async def async_get_server_info(self) -> dict[str, Any]:
        """Return server info (unauthenticated GET /info)."""
        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                resp = await self._session.get(f"{self._base_url}/info")
                if resp.status >= 400:
                    raise MusicAssistantCommandError(
                        f"GET /info failed with HTTP {resp.status}"
                    )
                data = await resp.json(content_type=None)
        except (TimeoutError, aiohttp.ClientError) as err:
            raise MusicAssistantConnectionError(
                f"Cannot connect to Music Assistant at {self._base_url}: {err}"
            ) from err
        if not isinstance(data, dict) or "server_id" not in data:
            raise MusicAssistantCommandError(
                f"{self._base_url}/info did not return Music Assistant server info"
            )
        return data

    async def async_command(self, command: str, **args: Any) -> Any:
        """Execute a single RPC command and return its result."""
        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                resp = await self._session.post(
                    f"{self._base_url}/api",
                    headers={"Authorization": f"Bearer {self._token}"},
                    json={"command": command, "args": args},
                )
                body = await resp.text()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise MusicAssistantConnectionError(
                f"Cannot connect to Music Assistant at {self._base_url}: {err}"
            ) from err

        if resp.status in (401, 403):
            raise MusicAssistantAuthError(
                f"Music Assistant rejected the token: {body.strip() or resp.status}"
            )
        if resp.status >= 400:
            raise MusicAssistantCommandError(
                f"Command {command} failed (HTTP {resp.status}): {body.strip()}"
            )

        if not body:
            return None
        try:
            return json.loads(body)
        except ValueError as err:
            raise MusicAssistantCommandError(
                f"Command {command} returned invalid JSON: {body[:200]}"
            ) from err

    # --- Party provider configuration -------------------------------------

    async def async_get_provider_config(self) -> dict[str, Any]:
        """Return the stored party provider config (values include entry metadata)."""
        result = await self.async_command(
            "config/providers/get", instance_id=PARTY_PROVIDER_INSTANCE_ID
        )
        if not isinstance(result, dict):
            raise MusicAssistantCommandError(
                "Unexpected response for config/providers/get"
            )
        return result

    async def async_save_provider_values(
        self, values: dict[str, Any]
    ) -> dict[str, Any]:
        """Save one or more party provider config values (partial update)."""
        result = await self.async_command(
            "config/providers/save",
            provider_domain=PARTY_PROVIDER_DOMAIN,
            instance_id=PARTY_PROVIDER_INSTANCE_ID,
            values=values,
        )
        return result if isinstance(result, dict) else {}

    # --- Party runtime state ----------------------------------------------

    async def async_get_party_config(self) -> dict[str, Any]:
        """Return the effective party configuration (party/config)."""
        result = await self.async_command("party/config")
        if not isinstance(result, dict):
            raise MusicAssistantCommandError("Unexpected response for party/config")
        return result

    async def async_get_party_url(self) -> str | None:
        """Return the guest access URL, or None if not available."""
        try:
            result = await self.async_command("party/url")
        except MusicAssistantCommandError:
            # No active party / guest access disabled.
            return None
        return result if isinstance(result, str) and result else None

    async def async_get_party_player(self) -> str | None:
        """Return the resolved party player/queue id, or None if not available."""
        try:
            result = await self.async_command("party/player")
        except MusicAssistantCommandError:
            return None
        return result if isinstance(result, str) and result else None

    # --- Party actions ----------------------------------------------------

    async def async_skip(self) -> Any:
        """Skip the currently playing track on the party queue."""
        return await self.async_command("party/skip")

    async def async_add_to_queue(self, uri: str, boost: bool = False) -> Any:
        """Add a media item to the party queue."""
        return await self.async_command("party/add_to_queue", uri=uri, boost=boost)

    async def async_boost_queue_item(self, queue_item_id: str) -> Any:
        """Boost an existing queue item to the priority section."""
        return await self.async_command(
            "party/boost_queue_item", queue_item_id=queue_item_id
        )
