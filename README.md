# Music Assistant Party Mode

[![hacs][hacs-badge]][hacs-url]
[![release][release-badge]][release-url]
[![validate][validate-badge]][validate-url]

A Home Assistant custom integration for the **Party plugin** of a
[Music Assistant](https://music-assistant.io) server.

Flip party mode on from a dashboard, automation, or NFC tag; expose the guest
join URL as an entity (ideal for a QR code on a wall tablet); and control every
guest setting — rate limits, permissions, karaoke mode, badge colors — without
leaving Home Assistant.

---

## Highlights

- **The join URL as a real entity.** `sensor.music_assistant_party_url` holds
  the full guest link, with the bare `join_code` as an attribute.
- **Complete configuration coverage.** All 24 party settings surface as native
  switches, selects, numbers, and text entities.
- **Options come from the server.** The player dropdown lists your actual
  speakers and sync groups; numeric ranges match the server's own limits. No
  hardcoded lists to drift out of date.
- **No extra dependencies.** Talks to Music Assistant's HTTP RPC API directly.

## Requirements

- **Music Assistant 2.10+** (API schema 28+, where API auth is mandatory) with
  the **Party** plugin enabled.
- A **long-lived API token**: Music Assistant → Settings → Users → your user →
  create token.
- **Home Assistant 2024.12** or newer.

## Installation

### HACS (recommended)

This is not (yet) in the HACS default store, so add it as a custom repository:

1. Open **HACS** in Home Assistant.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Paste the repository URL:
   ```
   https://github.com/nick-bogle/ha-musicassistant-party
   ```
4. Choose type **Integration**, then click **Add**.
5. Search HACS for **Music Assistant Party Mode** and click **Download**.
6. **Restart Home Assistant.**

### Manual

1. Copy the `custom_components/music_assistant_party/` folder into your Home
   Assistant `config/custom_components/` directory, so you end up with
   `config/custom_components/music_assistant_party/manifest.json`.
2. **Restart Home Assistant.**

## Setup

1. **Settings → Devices & Services → + Add Integration**.
2. Search for **Music Assistant Party Mode**.
3. Enter your server URL and API token:

   | Field | Example |
   | --- | --- |
   | Server URL | `https://music.example.net` or `http://192.168.1.10:8095` |
   | API token | the long-lived token from Music Assistant |

The setup step verifies that the server is reachable, that the token is
accepted, and that the Party plugin is actually loaded — so a typo or a
disabled plugin fails immediately with a clear message instead of a broken
integration.

Each Music Assistant server becomes one device, identified by its server ID, so
adding the same server twice is rejected. If a token is later revoked or
expires, Home Assistant prompts you to re-authenticate rather than silently
going unavailable.

**Poll interval:** defaults to 30 seconds. Change it via **Configure** on the
integration. Changes you make from Home Assistant apply immediately and update
the UI optimistically — the poll interval only governs how fast changes made
*elsewhere* (the Music Assistant UI, a guest's phone) show up here.

## Entities

One device per server (named after the server, defaulting to "Music
Assistant"):

| Entity | Type | Description |
| --- | --- | --- |
| **Party mode** | `switch` | Master switch. Enables guest access and the join link; turning it off ends the party and withdraws access. |
| **Party URL** | `sensor` | The guest join URL, e.g. `https://music.example.net/?join=ABC123`. `unknown` when no party is active. |
| **Active party player** | `sensor` | Which player or sync group is currently backing the party. |
| Audio mode | `select` | *Venue* (plays out loud on a speaker) or *Remote* (silent-disco; guests listen on their own devices). |
| Party player | `select` | Which player/sync group hosts the party, including *Auto*. Options pulled live from the server. |
| Party name | `text` | Name shown to guests on the party dashboard. |
| QR code text | `text` | Caption shown beneath the join QR code. |
| Party duration | `number` | Hours a generated join link stays valid (1–168). Applies to newly created links. |
| Guests can add to queue | `switch` | Allow guests to queue tracks. |
| Guests can boost tracks | `switch` | Allow guests to bump a track up the queue. |
| Guests can skip tracks | `switch` | Allow guests to skip the current track. |
| Guest rate limiting | `switch` | Master toggle for the token-bucket limits below. |
| Add to queue limit / refill time | `number` | Token allowance and refill rate for queueing. |
| Boost limit / refill time | `number` | Token allowance and refill rate for boosting. |
| Skip limit / refill time | `number` | Token allowance and refill rate for skipping. |
| Prevent duplicate tracks | `switch` | Reject a track already in the queue. |
| Karaoke mode | `switch` | Show lyrics on the party dashboard. |
| Highlight lyrics ahead | `switch` | Highlight upcoming lyrics early. |
| Show progress bar | `switch` | Show playback progress on the dashboard. |
| Anti burn-in | `switch` | Shift the display periodically to protect always-on screens. |
| Hide back button | `switch` | Hide the back button in fullscreen mode. |
| Request / Boost badge color | `select` | Badge colors for guest-added and boosted items. |
| **Skip current track** | `button` | Skip the track playing on the party queue. |

Everything except the party mode switch, the two sensors, and the skip button
is a `config`-category entity, so settings live on the device page instead of
cluttering your dashboards.

Entity IDs follow the device name — for the default they are
`sensor.music_assistant_party_url`, `switch.music_assistant_party_mode`,
`select.music_assistant_party_player`, and so on.

### Party URL attributes

```yaml
join_code: ABC123           # just the code, for manual entry
guest_access_enabled: true  # mirrors the party mode switch
party_mode: venue           # venue | remote
party_name: Nick's Party    # null when unset
```

## Actions

### `music_assistant_party.add_to_queue`

Adds a media item to the party queue, exactly as a guest request would.

| Field | Required | Description |
| --- | --- | --- |
| `uri` | yes | Media URI, e.g. `spotify://track/xxx` or `library://track/123`. |
| `boost` | no | `true` inserts at the front of the guest section (play next). |
| `config_entry_id` | no | Target server. Only needed with multiple servers configured. |

### `music_assistant_party.boost_queue_item`

Moves an existing queue item into the boosted priority section.

| Field | Required | Description |
| --- | --- | --- |
| `queue_item_id` | yes | The `queue_item_id` of the item to boost. |
| `config_entry_id` | no | Target server. Only needed with multiple servers configured. |

Both actions can return response data if you request it.

## Examples

### Show the join link on a dashboard

```yaml
type: markdown
content: >-
  {% set url = states('sensor.music_assistant_party_url') %}
  {% if url not in ('unknown', 'unavailable') %}
  ## 🎉 {{ state_attr('sensor.music_assistant_party_url', 'party_name') or 'Party' }}
  **[Tap to join the party]({{ url }})**

  Join code: `{{ state_attr('sensor.music_assistant_party_url', 'join_code') }}`
  {% else %}
  No party right now — flip the Party mode switch to start one.
  {% endif %}
```

For a scannable QR code, feed the sensor state into any Lovelace QR card that
accepts a template.

### Start the party and broadcast the link

```yaml
automation:
  - alias: "Party time"
    triggers:
      - trigger: state
        entity_id: input_boolean.party_scene
        to: "on"
    actions:
      - action: switch.turn_on
        target:
          entity_id: switch.music_assistant_party_mode
      # Give the server a moment to mint the join link.
      - delay: "00:00:05"
      - action: notify.family
        data:
          message: >-
            Party is live! Join: {{ states('sensor.music_assistant_party_url') }}
```

### Queue a hype track from an NFC tag

```yaml
automation:
  - alias: "Hype track"
    triggers:
      - trigger: tag
        tag_id: hype-tag
    actions:
      - action: music_assistant_party.add_to_queue
        data:
          uri: "spotify://track/4uLU6hMCjMI75M1A2tKUQC"
          boost: true
```

### Lock things down late at night

```yaml
automation:
  - alias: "Quiet hours"
    triggers:
      - trigger: time
        at: "23:00:00"
    actions:
      - action: switch.turn_off
        target:
          entity_id: switch.music_assistant_party_guests_can_skip_tracks
      - action: number.set_value
        target:
          entity_id: number.music_assistant_add_to_queue_limit
        data:
          value: 5
```

## How it works

The integration uses Music Assistant's HTTP RPC API (`POST /api`) with a bearer
token, which keeps it dependency-free. On each poll it calls:

- `config/providers/get` — party settings, plus the option lists and numeric
  ranges that drive the selects and numbers
- `party/url` — the guest join URL
- `party/player` — the resolved active player

Writes go through `config/providers/save` as partial updates, so changing one
setting never disturbs the others. The skip button and the two actions map to
`party/skip`, `party/add_to_queue`, and `party/boost_queue_item`.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| *"Connected, but the Party plugin is not enabled"* | Enable the Party provider in Music Assistant → Settings → Providers. |
| *"The server rejected the token"* | Token expired or revoked. Create a new one and complete the re-auth prompt. |
| *"The URL does not appear to be a Music Assistant server"* | The URL must point at the server root — the one that answers `GET /info`. |
| Party URL is `unknown` | Normal when guest access is off. Turn on the party mode switch. |
| Entities show *unavailable* | The Party provider isn't loaded on the server; check its status in Music Assistant. |

For deeper detail, enable debug logging:

```yaml
logger:
  logs:
    custom_components.music_assistant_party: debug
```

## Contributing

Issues and pull requests are welcome at
[nick-bogle/ha-musicassistant-party](https://github.com/nick-bogle/ha-musicassistant-party).

## License

[MIT](LICENSE)

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/v/release/nick-bogle/ha-musicassistant-party?display_name=tag
[release-url]: https://github.com/nick-bogle/ha-musicassistant-party/releases
[validate-badge]: https://github.com/nick-bogle/ha-musicassistant-party/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/nick-bogle/ha-musicassistant-party/actions/workflows/validate.yml
