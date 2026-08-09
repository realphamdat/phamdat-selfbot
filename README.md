<p align="center">
  <img src="assets/banner.png" alt="Phamdat Selfbot">
</p>

## Previews

<table align="center">
  <tr>
    <td align="center"><img src="assets/previews/terminal.png" alt="Terminal"><br>Terminal</td>
    <td align="center"><img src="assets/previews/data.png" alt="Data"><br>Data</td>
  </tr>
  <tr>
    <td align="center"><img src="assets/previews/captcha.png" alt="Captcha"><br>Captcha</td>
    <td align="center"><img src="assets/previews/solve.png" alt="Solve"><br>Solve</td>
  </tr>
</table>

## About
| | |
|---|---|
| **GitHub** | [github.com/realphamdat/phamdat-selfbot](https://github.com/realphamdat/phamdat-selfbot) |
| **Profile** | [realphamdat.github.io](https://realphamdat.github.io) |
| **Discord** | [discord.gg/GhfuaDTWQY](https://discord.gg/GhfuaDTWQY) |
| **Youtube** | [youtu.be/gqtXxDjQlhg](https://youtu.be/gqtXxDjQlhg) |

---

## Installation

**Requirements:** Python 3.10+ (64-bit), Git.

```bash
# 1. Get the project
git clone https://github.com/realphamdat/phamdat-selfbot.git
cd phamdat-selfbot
# (or download & extract the ZIP)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Put your tokens into data/ — see Configuration below
# 4. Run
python main.py
```

That's it — add your tokens, run, done.

---

## JSON Essentials

All configuration lives in JSON files. JSON stores data as text using just two structures:

- **Object** `{ }` — a set of `"key": value` pairs.
- **Array** `[ ]` — an ordered list of values.

A value can be a **string** `"owo"`, a **number** `50`, a **boolean** `true` / `false`, `null`, another object, or another array.

```json
{
    "daily": true,
    "spam": {
        "hunt": true,
        "delay": {"min": 0.5, "max": 1}
    }
}
```

The only rules that matter:

1. Keys are always double-quoted strings: `"daily"`.
2. Entries are comma-separated, and there is **no trailing comma** after the last one.
3. No comments allowed inside JSON (only `data/quest.txt` accepts `#` lines).

**The one pattern that unlocks everything:** every JSON file in `data/` is a top-level object where each **key is a Discord account token** and each **value is that account's own config**.

```json
{
    "YOUR_TOKEN": {"channels_id": [1]},
    "SECOND_TOKEN": {"channels_id": [2]}
}
```

So adding an account = adding one more token key, and removing an account = removing its token key. Everything else follows from there.

---

## Configuration

### OwO Bot — `data/owo.json`

Runs the full OwO macro for each account. A config with just the essentials:

```json
{
    "YOUR_TOKEN": {
        "channels_id": [123456789]
    }
}
```

Everything you don't write falls back to its default — and defaults are mostly **enabled**, so the minimal config above already runs daily, quests, spam and friends.

<details>
<summary><b>Full property reference</b> — every <code>owo.json</code> key</summary>

**Top level**

| Property | Type | Default | What it does |
|---|---|---|---|
| `prefix` | string | `owo` | OwO command prefix (default `owo` — so `{prefix}h` sends `owoh`) |
| `check_status` | bool | `true` | Probes OWO every 60 s; pauses the account 5–10 min if OWO stops replying |
| `channels_id` | array of int | `[]` | Channels the account may work in — one is picked randomly at startup |
| `changing_channel` | object | — | Channel-rotation behavior (see below) |
| `daily` | bool | `true` | Auto-claim `{prefix}daily`, waits exactly the duration OWO reports |
| `quest` | bool | `true` | Auto-read, claim & complete OWO quests |
| `huntbot` | bool | `true` | Claim huntbot rewards and submit huntbot passwords |
| `giveaway` | bool | `true` | Auto-join `New Giveaway` messages |
| `boss` | bool | `true` | Join guild boss battles |
| `spam` | object | — | XP-farming command loop (see below) |
| `gem` | object | — | Gem usage & inventory handling (see below) |
| `gamble` | object | — | Gambling games — slot, coinflip, blackjack, highlow, lottery (see below) |

**`changing_channel`** — when the account switches channels. Requires `channels_id` to have **more than one** ID; with a single ID nothing rotates.

| Property | Type | Default | What it does |
|---|---|---|---|
| `when_mentioned` | bool | `true` | Switch channel when the account gets mentioned |
| `when_challenge` | bool | `true` | Switch channel after accepting a battle challenge |
| `after_elapsed_time.min` | int | `300` | Minimum seconds before an automatic rotation |
| `after_elapsed_time.max` | int | `600` | Maximum seconds before an automatic rotation |

**`spam`** — the XP loop: one cycle of commands, then a random `cooldown` sleep, repeat.

| Property | Type | Default | What it does |
|---|---|---|---|
| `hunt` | bool | `true` | Send `{prefix}h` |
| `battle` | bool | `true` | Send `{prefix}b` (auto-skipped during "battle a friend" quests) |
| `owo/uwu` | bool | `true` | Send a plain `owo` or `uwu` |
| `delay.min` | number | `0.5` | Minimum random delay (s) between commands inside one cycle |
| `delay.max` | number | `1` | Maximum random delay (s) between commands inside one cycle |
| `cooldown.min` | int | `15` | Minimum random sleep (s) after a full cycle |
| `cooldown.max` | int | `20` | Maximum random sleep (s) after a full cycle |

**`gem`**

| Property | Type | Default | What it does |
|---|---|---|---|
| `use` | bool | `false` | Auto-use a gem when the account *gains* one (event-driven — reacts to OWO "gained" messages) |
| `couple` | bool | `true` | Use the 5-gem couple combo when OWO says "spent 5 cowoncy and caught a…" |
| `best` | bool | `false` | `false` = use the lowest-tier gem, `true` = use the highest |
| `star` | bool | `false` | Also use the star gem when an active special pet exists |
| `glitch` | bool | `true` | Check the double-time glitch (`{prefix}dt`) every 10 min — runs even with `use: false` |
| `openning.box` | bool | `true` | Open lootboxes (`{prefix}lb all`) when one is in the inventory |
| `openning.crate` | bool | `true` | Open crates (`{prefix}wc all`) when one is in the inventory |
| `openning.flootbox` | bool | `true` | Open flootboxes (`{prefix}lb f`) when one is in the inventory |

**`gamble`** — each game has `mode` (off by default). `delay`/`cooldown` are shared by all games.

| Game | Settings | Defaults | What it does |
|---|---|---|---|
| `lottery` | `mode`, `amount` | `false`, `1` | One `{prefix}lottery <amount>` submission per daily reset |
| `slot` | `mode`, `bet`, `rate`, `max` | `false`, `1`, `2`, `250000` | `{prefix}s <bet>` |
| `coinflip` | `mode`, `bet`, `rate`, `max` | `false`, `1`, `2`, `250000` | `{prefix}cf <bet>` |
| `blackjack` | `mode`, `bet`, `rate`, `max` | `false`, `1`, `2`, `250000` | `{prefix}bj <bet>` — plays via reactions: 👊 hit while points ≤ 17, 🛑 stand otherwise |
| `highlow` | `mode`, `bet`, `rate`, `max` | `false`, `10`, `2`, `250000` | `{prefix}hl <bet>` — guesses Higher/Lower via buttons, cashes out at ×2 (bet is forced to minimum 10) |
| `delay.min` / `delay.max` | number | `0.5` / `1` | Random delay (s) between games inside one cycle |
| `cooldown.min` / `cooldown.max` | int | `60` / `120` | Random sleep (s) after a full gamble cycle |

Martingale rules for all games: a loss multiplies the next bet by `rate`, a win resets it to `bet`, and hitting `max` also resets it to `bet`.

</details>

**Tips for `owo.json`**

- Want everything off? Write the keys explicitly as `false` — omitting a key means *use the default*, which is usually on.
- **Multiple accounts:** add another token key, each with its own config. The bot staggers logins by 2 s. With 2+ accounts, friend quests (battle, cookie, pray, curse, action) get solved by the other accounts.
- **Multiple channels:** put more channel IDs into `channels_id` and the account rotates between them automatically.

---

### Chat — `data/chat.json`

Sends messages from `assets/messages.txt` (one message per line) into the channels you pick. A random channel and a random message are chosen for every send.

```json
{
    "YOUR_TOKEN": {
        "chat_channel_id": [123456789, 987654321],
        "cooldown": {"min": 60, "max": 120},
        "exist": false
    }
}
```

| Property | Type | Default | What it does |
|---|---|---|---|
| `chat_channel_id` | array of int | `[]` | Channels to send in (random pick per message). Empty → the account is skipped |
| `cooldown.min` / `cooldown.max` | int | `60` / `120` | Random seconds between messages |
| `exist` | bool | `false` | `false` = send then instantly delete (ghost message). `true` = leave it in the channel |

Add more accounts the same way — one token key each. If `assets/messages.txt` is missing or empty, nothing is sent.

---

### Voice — `data/voice.json`

Connects each account to a voice channel and keeps it there — every 60 s it checks the connection and reconnects if it dropped.

```json
{
    "YOUR_TOKEN": 123456789
}
```

The value is the voice channel ID. Add one token key per account; remove the key to disable.

---

### Quest Autocompleter — `data/quest.txt`

A plain-text file, **one token per line**. Lines starting with `#` are ignored.

```
# one token per line
TOKEN_A
TOKEN_B
```

Uses Discord's HTTP API directly (no gateway). Every 5 minutes it fetches available quests, auto-accepts eligible ones, then completes supported task types — watch-video progress and desktop play/stream time are driven by the quest API, and rate limits (429) are respected automatically. Up to 100 quests are processed in parallel.

Remove a token line to disable that account.

---

## Tips

1. **JSON breaks on one typo** — a missing comma or double quote makes the whole file fail to load. Keep the last entry in each `{ }` / `[ ]` comma-free.
2. **Minimal config is fine** — every property you omit silently uses its default. Write only what you want to change.
3. **Defaults are mostly on** — to turn something *off*, write `false` explicitly. Deleting a key just re-enables it.
4. **One account = one token key** — duplicate the token key to add an account; each account keeps its own config. For quest-chaining, configure 2+ OwO accounts together.
5. **Channels rotate on their own** — more than one ID in `channels_id` and the account hops between them on a timer.
6. **Edit `owo.json` while it's stopped** — it reloads automatically in the background a few seconds after you save; chat, voice and quest read their files only at startup, so edit those before launching.
7. **Captchas pause the account** — it resumes only once the captcha is handled through the web UI. An optional webhook in `data/settings.json` (→ `discord_webhook.url`) pings you when one is detected.
8. **Keep the OwO DM open** — the bot opens it automatically; daily, quest and captcha flows need it.

---

## License

This project is licensed under the **Phamdat Selfbot — Educational License**. See [LICENSE](LICENSE) for details.

- Educational use only.
- Selling or commercial use is strictly prohibited.
- Credit required when referencing or borrowing code.
- Provided "as is" — the author assumes no liability for misuse or any consequences arising from use.
