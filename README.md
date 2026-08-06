<p align="center">
  <img src="assets/banner.png" alt="banner">
</p>

## Previews

<table align="center">
  <tr>
    <td align="center"><img src="assets/previews/terminal.png" alt="Terminal"><br>Terminal</td>
    <td align="center"><img src="assets/previews/captcha.png" alt="Captcha"><br>Captcha</td>
    <td align="center"><img src="assets/previews/data.png" alt="Data"><br>Data</td>
  </tr>
</table>

## Links

| | |
|---|---|
| GitHub | [realphamdat/phamdat-selfbot](https://github.com/realphamdat/phamdat-selfbot) |
| Profile | [realphamdat.github.io](https://realphamdat.github.io) |
| Discord | [discord.gg/GhfuaDTWQY](https://discord.gg/GhfuaDTWQY) |

---

## Table of Contents

- [Installation](#installation)
- [JSON Essentials](#json-essentials)
- [Configuration](#configuration)
  - [File Map](#file-map)
  - [data/owo.json — OWO Bot](#dataowojson--owo-bot)
  - [data/chat.json — Chat](#datachatjson--chat)
  - [data/voice.json — Voice](#datavoicejson--voice)
  - [data/quest.txt — Quest Autocompleter](#dataquesttxt--quest-autocompleter)
  - [data/settings.json — Webhook](#datasettingsjson--webhook)
  - [data/caches.json — Internal](#datacachesjson--internal)
  - [Defaults & Missing Keys](#defaults--missing-keys)
  - [Multiple Tokens & Channels](#multiple-tokens--channels)
  - [Enabling / Disabling Features](#enabling--disabling-features)
  - [Hot Reload](#hot-reload)
- [Bot Guards & Behavior](#bot-guards--behavior)
- [Web Interface](#web-interface)
- [Tips](#tips)
- [License](#license)

---

## Installation

**Requirements**

| Requirement | Notes |
|---|---|
| Python | 3.10+ (64-bit) |
| Git | Required to install `discord.py-self` from GitHub (first line of `requirements.txt`) |
| pip | Comes with Python |
| Internet | Required to download dependencies and connect to Discord |

**Steps**

1. Download the project ZIP file from the [GitHub repository](https://github.com/realphamdat/phamdat-selfbot) (`Code` → `Download ZIP`).
2. Extract the ZIP into a folder of your choice.
3. Open a terminal (Command Prompt or PowerShell) and navigate into the extracted folder.
4. *(Recommended)* Create a virtual environment to keep dependencies isolated:

   ```bash
   python -m venv venv
   ```

   Activate it:

   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

5. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Configure your tokens inside the `data/` folder (see [Configuration](#configuration)).
7. Start the program:

   ```bash
   python main.py
   ```

8. Open <http://localhost:2010> in your browser to access the web interface.

> When the terminal starts, it prints the exact URL of the website, including your LAN IP, e.g. `Website: http://192.168.1.10:2010`.

---

## JSON Essentials

All configuration is written in **JSON**, so you need to understand it before editing config files.

**What is JSON?** A text format that stores data as key/value **objects**, using **arrays** for lists. It is built from just a few building blocks:

| Type | Example | Meaning |
|---|---|---|
| Object | `{ "key": "value" }` | A collection of key/value pairs, wrapped in `{}` |
| Array | `[1, 2, 3]` | An ordered list of values, wrapped in `[]` |
| String | `"hello"` | Text, always wrapped in double quotes `"..."` |
| Number | `123` or `0.5` | Integer or decimal, no quotes |
| Boolean | `true` / `false` | Logical on/off, no quotes, lowercase |
| Null | `null` | Explicit "nothing" |

**The rules:**

1. Keys are always strings wrapped in double quotes: `"channels_id"`.
2. Values can be any of the types above, including nested objects.
3. Pairs are separated by commas: `{"a": 1, "b": 2}`.
4. Nested structures work naturally: `{"spam": {"hunt": true}}`.
5. The **last** pair in an object or array must **not** have a trailing comma.
6. Comments are **not** allowed. (Some files like `data/quest.txt` support `#` lines, but JSON files do not.)
7. Whitespace is ignored, but indentation makes it readable.

**Example config object:**

```json
{
    "daily": true,
    "spam": {
        "hunt": true,
        "delay": {"min": 0.5, "max": 1}
    }
}
```

- `daily` is a boolean.
- `spam` is an object containing a boolean and another nested object `delay`.
- `delay` holds two numbers.

Every `data/*.json` file follows this exact structure: a top-level JSON object where each **key is a user token** and each **value is that account's configuration**.

---

## Configuration

### File Map

| File | Controls | Format |
|---|---|---|
| `data/owo.json` | OWO bot (macro) per account | JSON: `token -> config` |
| `data/chat.json` | Chat extension per account | JSON: `token -> config` |
| `data/voice.json` | Voice extension per account | JSON: `token -> channel_id` |
| `data/quest.txt` | Discord Quest autocompleter | Plain text, `1 token per line` |
| `data/settings.json` | Global settings (Discord webhook) | JSON |
| `data/caches.json` | Internal captcha cache | JSON — do not edit manually |

---

### data/owo.json — OWO Bot

**Structure**

```json
{
    "YOUR_TOKEN": {
        "channels_id": [123456789, 987654321],
        "changing_channel": {
            "when_mentioned": true,
            "when_challenge": true,
            "after_elapsed_time": {"min": 300, "max": 600}
        },
        "daily": true,
        "quest": true,
        "huntbot": true,
        "giveaway": true,
        "boss": true,
        "spam": {
            "hunt": true,
            "battle": true,
            "owo/uwu": true,
            "delay": {"min": 0.5, "max": 1},
            "cooldown": {"min": 15, "max": 20}
        },
        "gem": {
            "use": false,
            "couple": true,
            "best": false,
            "star": false,
            "glitch": true,
            "openning": {"box": true, "crate": true, "flootbox": true}
        },
        "gamble": {
            "lottery": {"mode": false, "amount": 1},
            "slot": {"mode": false, "bet": 1, "rate": 2, "max": 250000},
            "coinflip": {"mode": false, "bet": 1, "rate": 2, "max": 250000},
            "blackjack": {"mode": false, "bet": 1, "rate": 2, "max": 250000},
            "delay": {"min": 0.5, "max": 1},
            "cooldown": {"min": 60, "max": 120}
        }
    }
}
```

**Top-level properties**

| Property | Type | Default | Description |
|---|---|---|---|
| `channels_id` | `array of int` | `[]` | Channel IDs the account may operate in. One is picked randomly as the working channel. |
| `changing_channel` | `object` | see below | Channel-switching behavior |
| `daily` | `bool` | `true` | Claim the OWO daily reward automatically |
| `quest` | `bool` | `true` | Auto-detect, claim, and complete OWO quests |
| `huntbot` | `bool` | `true` | Claim huntbot rewards and submit huntbot passwords |
| `giveaway` | `bool` | `true` | Auto-join OWO giveaways |
| `boss` | `bool` | `true` | Join guild boss battles |
| `spam` | `object` | see below | XP-farming command loop |
| `gem` | `object` | see below | Gem usage and double-time glitch |
| `gamble` | `object` | see below | Gambling mini-games (slot, coinflip, blackjack, lottery) |

**`channels_id` — working channels**

- Each account runs in exactly **one** channel at a time, chosen randomly from this list at startup.
- If the list contains **more than one** ID, the channel-rotation loop starts and switches to a random *different* channel every `after_elapsed_time`.
- With only one ID, no rotation happens.

**`changing_channel`**

| Property | Type | Default | Behavior |
|---|---|---|---|
| `when_mentioned` | `bool` | `true` | If someone mentions the account in the current channel, switch to another channel immediately. |
| `when_challenge` | `bool` | `true` | After accepting a battle challenge embed (`owo ab`), switch channel. |
| `after_elapsed_time.min` | `int` | `300` | Minimum seconds before an automatic channel rotation (lower bound of random range). |
| `after_elapsed_time.max` | `int` | `600` | Maximum seconds before an automatic channel rotation (upper bound). |

Each rotation waits a **random** duration between `min` and `max`.

**`spam`**

| Property | Type | Default | Behavior |
|---|---|---|---|
| `hunt` | `bool` | `true` | Send `owoh` / `owohunt` |
| `battle` | `bool` | `true` | Send `owob` / `owobattle` |
| `owo/uwu` | `bool` | `true` | Send plain `owo` or `uwu` text |
| `delay.min` | `number` | `0.5` | Minimum random delay (seconds) between each command inside one cycle |
| `delay.max` | `number` | `1` | Maximum random delay (seconds) between each command inside one cycle |
| `cooldown.min` | `int` | `15` | Minimum random sleep (seconds) after a full spam cycle |
| `cooldown.max` | `int` | `20` | Maximum random sleep (seconds) after a full spam cycle |

The spam loop performs one cycle, then sleeps a random `cooldown`, then repeats. Each command is preceded by a random `delay`. Battle is automatically skipped while a "battle with a friend" quest is active.

**`gem`**

| Property | Type | Default | Behavior |
|---|---|---|---|
| `use` | `bool` | `false` | Master switch: automatically use gems when the account "gains" a gem in a channel message. |
| `couple` | `bool` | `true` | When `use` is on, use the 5-gem couple combo (one gem per active tier at the same level) whenever OWO says "spent 5 cowoncy and caught a...". |
| `best` | `bool` | `false` | `false` = use the lowest-tier gem available; `true` = use the highest. |
| `star` | `bool` | `false` | Include the star tier in combos. The account first checks whether it owns the special pet; if not, star is skipped. |
| `glitch` | `bool` | `true` | Periodically send `owodt` to check if the double-time glitch is available, and remember the reset cooldown until it is available again. |
| `openning.box` | `bool` | `true` | Send `owolb all` when a lootbox is in the inventory. |
| `openning.crate` | `bool` | `true` | Send `owowc all` when a crate is in the inventory. |
| `openning.flootbox` | `bool` | `true` | Send `owolb f` when a flootbox is in the inventory. |

Notes:

- Gem usage is event-driven: it only triggers when a channel message from OWO shows the account gained a gem — empty inventories are remembered for 1 hour to avoid repeatedly opening the inventory.
- Even with `use: false`, the `glitch` loop still runs independently if `glitch` is `true`.

**`gamble`**

| Game | Property | Default | Behavior |
|---|---|---|---|
| `lottery` | `mode` | `false` | Send one `owolottery <amount>` submission per daily reset. |
| `lottery` | `amount` | `1` | Lottery ticket amount. |
| `slot` | `mode` | `false` | Play `owos <bet>` |
| `slot` | `bet` | `1` | Base bet when starting or after a win. |
| `slot` | `rate` | `2` | Martingale multiplier: on a loss the next bet is `bet * rate`. |
| `slot` | `max` | `250000` | Bet cap — when reached, the bet resets to the base `bet`. |
| `coinflip` | `mode` / `bet` / `rate` / `max` | `false` / `1` / `2` / `250000` | Play `owocf <bet>`. Same martingale rules as slot. |
| `blackjack` | `mode` / `bet` / `rate` / `max` | `false` / `1` / `2` / `250000` | Play `owobj <bet>`. Plays via reactions: `👊` (hit) when points ≤ 17, `🛑` (stand) otherwise. Same martingale rules. |
| `delay` | `min` / `max` | `0.5` / `1` | Random delay between each game inside one cycle. |
| `cooldown` | `min` / `max` | `60` / `120` | Random sleep after a full gamble cycle. |

Results are parsed from OWO messages: `won nothing` / `you lost` double the next bet (`rate`), wins/draws reset it to the base `bet`. Each game's messages are detected in `on_message_edit`, so they work even when OWO edits its embed after the result.

**Bot mechanics summary**

| Feature | What it actually does |
|---|---|
| Daily | Sends `owodaily`, reads the "next daily in Xh Ym Zs" response, and waits exactly that long. If not ready ("Nu"), it parses the remaining time directly. |
| Quest | Sends `owoq`, reads the quest-log embed, clicks the `quests:claim` button when a claim is available, extracts quest text, and sets internal flags that drive `spam` / `gamble` / action commands. Requires the OWO settings below — applied automatically on startup. |
| Quest settings | The bot opens OWO `owobs` and sets **Quest Display = text** and **Quest Completion Notifications = true** on first ready. These are required for quest parsing; do not change them in OWO manually. |
| Multi-account quests | With 2+ accounts configured, friend quests are solved by other configured accounts: `owob <mention>`, `owocookie <id>`, `owopray <id>`, `owocurse <id>`, action commands. Solo quests are picked when only 1 account exists. Boss quests are detected and skipped (and `boss` is force-enabled if disabled). |
| Huntbot | Sends `owohb 1d`. If a password image is returned, it solves the image locally by template matching against the letter templates in `assets/owo/huntbot/`, then sends `owohb 1d <answer>`. Handles "password will reset in X", "still hunting", and "back with" states. |
| Giveaway | Watches edited OWO messages for `New Giveaway` embeds and clicks the join button once per message. |
| Boss | Watches for `A Guild Boss Appeared!` and clicks the `guildboss_fight` button. If the account has no boss tickets, boss participation pauses until the next daily reset. |
| Offline check | Every 60 s, if no OWO message arrived in the last 60 s, the bot sends a random action command mentioning OWO. No reply within 10 s → pauses 300–600 s, then resumes. |
| Ban / no funds | A ban message or a genuine "don't have enough cowoncy" message permanently stops that account's macro. |

**Defaults & missing keys**

Every account config is merged over a built-in default set at runtime:

```
final_config = deep_merge(OWO_DEFAULT_CONFIG, your_config)
```

`deep_merge` works recursively:

- Missing top-level keys → default values are used.
- Missing nested keys → nested defaults are used.
- Keys you write override defaults (scalars replace, objects merge).
- The full default table above is therefore the exact runtime behavior of an empty config.

This means a **minimal valid config** is just:

```json
{
    "YOUR_TOKEN": {
        "channels_id": [123456789]
    }
}
```

Everything else (`daily`, `quest`, `spam`, ...) silently falls back to the defaults — in this case everything **on**. To change one feature, write only that key.

**Multiple tokens & channels**

- **Multiple tokens**: add another top-level key in `data/owo.json`. Each key is a separate Discord account with its own config:

  ```json
  {
      "TOKEN_A": {"channels_id": [111]},
      "TOKEN_B": {"channels_id": [222], "daily": false}
  }
  ```

  Accounts boot with a 2-second stagger. Adding multiple accounts enables the friend-based quest solving.

- **Multiple channels**: add more numeric channel IDs to any `channels_id` array. The account will rotate between them (randomly) if more than one exists.

**Enabling / disabling features**

| Action | How |
|---|---|
| Disable one feature for one account | Set its boolean to `false`, e.g. `"daily": false` |
| Disable a whole group | `"spam": {"hunt": false, "battle": false, "owo/uwu": false}` or `"gem": {"use": false, "glitch": false}` |
| Disable all gambling | Set every game `mode` to `false` |
| Disable an entire account | Remove its token key from the JSON (or leave the config empty `{}` — defaults produce an account with no channels, which does nothing but still connects; removal is cleaner) |

> Because defaults are mostly `true`, **disabling requires an explicit `false`**. Omitting a key means "use the default" — which is usually enabled.

---

### data/chat.json — Chat

**Structure**

```json
{
    "YOUR_TOKEN": {
        "chat_channel_id": [123456789, 987654321],
        "cooldown": {"min": 60, "max": 120},
        "exist": false
    }
}
```

| Property | Type | Default | Behavior |
|---|---|---|---|
| `chat_channel_id` | `array of int` | `[]` | Channels to send chat messages in. A random channel is picked per message. Missing or empty → the account is skipped. |
| `cooldown.min` | `int` | `60` | Minimum random seconds between messages. |
| `cooldown.max` | `int` | `120` | Maximum random seconds between messages. |
| `exist` | `bool` | `false` | `false` → send and immediately delete the message (ghost message). `true` → leave the message in the channel. |

Messages are taken from `assets/messages.txt`, **one message per line**. If the file is missing or empty, the extension does nothing.

Add multiple accounts by adding more token keys with the same shape. Disable an account by removing its token key or clearing `chat_channel_id`.

---

### data/voice.json — Voice

**Structure**

```json
{
    "YOUR_TOKEN": 123456789
}
```

| Key | Value | Behavior |
|---|---|---|
| token | numeric channel ID | The account joins this voice channel and stays connected. Every 30 seconds it verifies the connection and reconnects if dropped. |

Add more accounts with more token keys. Remove the token key to disable.

---

### data/quest.txt — Quest Autocompleter

A **plain text** file, one token per line. Lines starting with `#` are ignored.

```
# 1 token per 1 line
TOKEN_A
TOKEN_B
```

This uses Discord's HTTP API directly (not the gateway). For each token it:

1. Fetches available quests from `/quests/@me` every 60 s.
2. Auto-accepts eligible quests (enrollment).
3. Completes supported task types:

| Task type | Completion method |
|---|---|
| `WATCH_VIDEO` / `WATCH_VIDEO_ON_MOBILE` | Sends fake video-progress timestamps until the target is reached |
| `PLAY_ON_DESKTOP` / `STREAM_ON_DESKTOP` | Sends heartbeat requests with a random stream key |
| `PLAY_ACTIVITY` | Sends heartbeat requests |

Rate limits (HTTP 429) are handled with retry-after waits. Up to 10 quests are processed in parallel. Remove a token line (or delete the file) to disable.

---

### data/settings.json — Webhook

**Structure**

```json
{
    "discord_webhook": {
        "url": "https://discord.com/api/webhooks/...",
        "content": "@everyone @here <@&role_id> <@user_id>"
    }
}
```

| Property | Type | Default | Behavior |
|---|---|---|---|
| `discord_webhook.url` | `string` | *(empty)* | Webhook URL used for captcha alerts. Empty → no webhook. |
| `discord_webhook.content` | `string` | `@everyone @here` | Message sent before the captcha embed. May contain role/user mentions. |

When any captcha is detected, a `CAPTCHA DETECTED` embed is sent to this webhook with a jump link to the message. Mentions only work if the webhook has permission for them.

---

### data/caches.json — Internal

Stores pending captchas and wrong-answer history, written atomically by the program. **Do not edit manually** — all captcha operations are done through the web interface.

---

### Hot Reload

- `data/owo.json` is watched every 3 seconds.
- If it changes **while the macro is stopped**, all OWO accounts are rebuilt automatically with the new config.
- If it changes **while running**, the reload is skipped (a log line explains this). Stop the macro, edit, then start again.
- `data/chat.json`, `data/voice.json`, `data/quest.txt`, `data/settings.json` are read at extension start. After editing them, restart the extension from the web UI (Stop → Start).

---

## Bot Guards & Behavior

| Condition | Effect |
|---|---|
| Captcha detected | The account pauses all actions until solved (or deleted) from the web UI. |
| hCaptcha | Solved through an embedded hCaptcha widget in the browser. The token is verified automatically via the owobot.com API using an OAuth flow built into the bot. |
| Image captcha | An image input is shown in the browser. The answer is sent to OWO's DM; the bot then watches for a 👍 (success) or 🚫 (wrong) reaction. |
| Wrong captcha answers | Remembered per account. The bot refuses to re-send a known-wrong answer; the UI lets you retry. |
| Pending captcha after reconnect | Pending captchas are re-processed automatically on reconnect. |
| Captcha expiry | Captchas expire 10 minutes after detection and are highlighted in the UI. |

---

## Web Interface

The web UI is served at <http://localhost:2010> and has three pages (sidebar on the left):

| Page | Purpose |
|---|---|
| Terminal | Start/stop all bots, live log stream, filter by level / logger, search (smart or strict), scrollable history (last 100,000 lines) |
| Captcha | List of all pending captchas with priority sorting, solve image captchas, solve hCaptcha inline, jump to the original Discord message, delete/dismiss |
| Data | Edit every file inside `data/` with a code editor (line numbers, syntax-aware diff view, `Ctrl+S` to save, JSON validation on save) |

---

## Tips

1. **Access the web UI from other devices** — the server binds `0.0.0.0:2010`, so any device on the same network can open `http://<your-LAN-IP>:2010` (the exact IP is printed in the terminal log at startup). No port forwarding needed — just the same Wi-Fi/LAN.
2. **Use the Data page to edit configs** — it validates JSON server-side before saving, so you never corrupt a config file with a missing comma.
3. **Multiple channels** — simply add more IDs to `channels_id` (or `chat_channel_id`). Rotation is automatic and random.
4. **Multiple tokens** — one token key per account in `owo.json` / `chat.json` / `voice.json`, or one line per token in `quest.txt`.
5. **Minimal config is fine** — any missing property falls back to its default (see [Defaults & missing keys](#defaults--missing-keys)). You only ever need to write what you want to change.
6. **Disable needs explicit `false`** — because defaults are mostly `true`, removing a key re-enables it. To disable, write the boolean.
7. **Edit `owo.json` while stopped** — it hot-reloads automatically. While running, edits are ignored; stop first.
8. **Wrong captcha answers are remembered** — the bot won't burn them again; submit a different answer.
9. **OWO settings are auto-applied** — Quest Display = text and Quest Completion Notifications = true. Changing them in OWO breaks quest parsing.
10. **Multi-account quests** — friend quests (battle a friend, cookie, pray, curse, action on you) are solved only when 2+ OWO accounts are configured.
11. **The OWO DM must stay open** — the bot opens it automatically; image-captcha answers are delivered through it.
12. **Martingale protection** — every gamble game has a `max`; reaching it resets the bet to the base `bet`, preventing runaway bets.
13. **Offline detection** — if OWO stops replying, the account pauses 5–10 minutes instead of stacking messages.
14. **Terminal history** — you can scroll up indefinitely (100k-line buffer) and filter logs per logger, e.g. only see your account name or only WARNING+.

---

## License

This project is licensed under the **Phamdat Selfbot — Educational License**. See [LICENSE](LICENSE) for details.

- Educational use only.
- Selling or commercial use is strictly prohibited.
- Credit required when referencing or borrowing code.
- Provided "as is" — the author assumes no liability for misuse or any consequences arising from use.