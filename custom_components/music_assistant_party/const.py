"""Constants for the Music Assistant Party Mode integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "music_assistant_party"

CONF_BASE_URL = "base_url"
CONF_TOKEN = "token"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 5
DEFAULT_TIMEOUT = 15

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# The Music Assistant provider instance that implements party mode.
PARTY_PROVIDER_DOMAIN = "party"
PARTY_PROVIDER_INSTANCE_ID = "party"

# Provider config keys (from config/providers/get_entries for the party provider)
KEY_ENABLE_GUEST_ACCESS = "enable_guest_access"
KEY_MODE = "mode"
KEY_PLAYER = "player"
KEY_PARTY_NAME = "party_name"
KEY_PARTY_DURATION = "party_duration"
KEY_QR_TEXT = "qr_text"
KEY_HIDE_BACK_BUTTON = "hide_back_button"
KEY_SHOW_PROGRESS_BAR = "show_progress_bar"
KEY_KARAOKE_MODE = "karaoke_mode"
KEY_HIGHLIGHT_AHEAD = "highlight_ahead"
KEY_ANTI_BURN_IN = "anti_burn_in"
KEY_ENABLE_RATE_LIMITING = "enable_rate_limiting"
KEY_ENABLE_ADD_QUEUE = "enable_add_queue"
KEY_PREVENT_DUPLICATE_TRACKS = "prevent_duplicate_tracks"
KEY_ADD_QUEUE_LIMIT = "add_queue_limit"
KEY_ADD_QUEUE_REFILL_MINUTES = "add_queue_refill_minutes"
KEY_ENABLE_BOOST = "enable_boost"
KEY_BOOST_LIMIT = "boost_limit"
KEY_BOOST_REFILL_MINUTES = "boost_refill_minutes"
KEY_ENABLE_SKIP_SONG = "enable_skip_song"
KEY_SKIP_SONG_LIMIT = "skip_song_limit"
KEY_SKIP_SONG_REFILL_MINUTES = "skip_song_refill_minutes"
KEY_REQUEST_BADGE_COLOR = "request_badge_color"
KEY_BOOST_BADGE_COLOR = "boost_badge_color"

# Sentinel used by the party provider for "auto" player selection.
PLAYER_AUTO = "__auto__"

# Services
SERVICE_ADD_TO_QUEUE = "add_to_queue"
SERVICE_BOOST_QUEUE_ITEM = "boost_queue_item"
ATTR_URI = "uri"
ATTR_BOOST = "boost"
ATTR_QUEUE_ITEM_ID = "queue_item_id"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
