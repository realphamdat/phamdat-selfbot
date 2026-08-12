<p align="center">
  <img src="assets/banner.png" alt="Phamdat Selfbot">
</p>

## PREVIEW

<details>
<summary><b>Terminal</b></summary>

<p align="center">
  <img src="assets/previews/terminal.png" alt="Terminal">
</p>

</details>

<details>
<summary><b>Data</b></summary>

<p align="center">
  <img src="assets/previews/data.png" alt="Data">
</p>

</details>

<details>
<summary><b>Captcha</b></summary>

<p align="center">
  <img src="assets/previews/captcha.png" alt="Captcha">
</p>

</details>

## ABOUT

| | |
|---|---|
| **GitHub** | [github.com/realphamdat/phamdat-selfbot](https://github.com/realphamdat/phamdat-selfbot) |
| **Profile** | [realphamdat.github.io](https://realphamdat.github.io) |
| **Discord** | [discord.gg/GhfuaDTWQY](https://discord.gg/GhfuaDTWQY) |
| **Youtube** | [youtu.be/gqtXxDjQlhg](https://youtu.be/gqtXxDjQlhg) |
| **Render** | [youtu.be/9LdrSc7xH-o](https://youtu.be/9LdrSc7xH-o) |

---

## INSTALLATION

**Requirements:**
[Python](https://www.python.org/downloads/), [Git](https://git-scm.com/install/windows)

```bash
pip install -r requirements.txt
python main.py
```

---

## Configuration

Each config file is a JSON object where every **key is a Discord token** — one account per key, handled separately. Add a token key → add an account; remove it → remove the account.

<details>
<summary><b>owo.json</b> — OwO bot macro</summary>

Runs the full OwO macro per account: hunt, battle, daily, quests, huntbot, giveaways, guild boss, gems and gambling.

```json
{
    "YOUR_TOKEN": {
        "channels_id": [123456789]
    }
}
```

**Top level**

| Property | Type | Default | What it does |
|---|---|---|---|
| `prefix` | string | `owo` | OwO command prefix — `{prefix}h` sends `owoh` |
| `check_status` | bool | `true` | Probes OWO every 60 s; pauses the account 5–10 min if OWO stops replying |
| `channels_id` | array of int | `[]` | Channels the account may work in — one is picked randomly at startup |
| `changing_channel` | object | — | Channel-rotation behavior (below) |
| `daily` | bool | `true` | Auto-claim `{prefix}daily`, waits exactly the duration OWO reports |
| `quest` | bool | `true` | Auto-read, claim & complete OWO quests |
| `huntbot` | bool | `true` | Claim huntbot rewards and submit huntbot passwords |
| `giveaway` | bool | `true` | Auto-join `New Giveaway` messages |
| `boss` | bool | `true` | Join guild boss battles |
| `spam` | object | — | XP-farming command loop (below) |
| `gem` | object | — | Gem usage & inventory handling (below) |
| `gamble` | object | — | Slot, coinflip, blackjack, highlow, lottery (below) |

**`changing_channel`** — needs more than one ID in `channels_id`; a single ID means no rotation at all.

| Property | Type | Default | What it does |
|---|---|---|---|
| `when_mentioned` | bool | `true` | Switch channel when the account gets mentioned |
| `when_challenge` | bool | `true` | Switch channel after accepting a battle challenge |
| `after_elapsed_time.min` | int | `300` | Minimum seconds between automatic rotations |
| `after_elapsed_time.max` | int | `600` | Maximum seconds between automatic rotations |

**`spam`** — the XP loop: one cycle of commands, then a random `cooldown` sleep, repeat.

| Property | Type | Default | What it does |
|---|---|---|---|
| `hunt` | bool | `true` | Send `{prefix}h` |
| `battle` | bool | `true` | Send `{prefix}b` (auto-skipped during "battle a friend" quests) |
| `owo/uwu` | bool | `true` | Send a plain `owo` or `uwu` |
| `delay.min` | number | `0.5` | Min random delay (s) between commands in a cycle |
| `delay.max` | number | `1` | Max random delay (s) between commands in a cycle |
| `cooldown.min` | int | `15` | Min random sleep (s) after a full cycle |
| `cooldown.max` | int | `20` | Max random sleep (s) after a full cycle |

**`gem`**

| Property | Type | Default | What it does |
|---|---|---|---|
| `use` | bool | `false` | Auto-use a gem when the account gains one (reacts to OWO "gained" messages) |
| `couple` | bool | `true` | Use the 5-gem couple combo when OWO says "spent 5 cowoncy and caught a…" |
| `best` | bool | `false` | `false` = lowest-tier gem, `true` = highest |
| `star` | bool | `false` | Also use the star gem when an active special pet exists |
| `glitch` | bool | `true` | Check the double-time glitch (`{prefix}dt`) every 10 min — runs even with `use: false` |
| `openning.box` | bool | `true` | Open lootboxes (`{prefix}lb all`) when in inventory |
| `openning.crate` | bool | `true` | Open crates (`{prefix}wc all`) when in inventory |
| `openning.flootbox` | bool | `true` | Open flootboxes (`{prefix}lb f`) when in inventory |

**`gamble`** — every game has `mode`, all off by default. `delay` / `cooldown` are shared.

| Game | Settings | Defaults | What it does |
|---|---|---|---|
| `lottery` | `mode`, `amount` | `false`, `1` | One `{prefix}lottery <amount>` submission per daily reset |
| `slot` | `mode`, `bet`, `rate`, `max` | `false`, `1`, `2`, `250000` | `{prefix}s <bet>` |
| `coinflip` | `mode`, `bet`, `rate`, `max` | `false`, `1`, `2`, `250000` | `{prefix}cf <bet>` |
| `blackjack` | `mode`, `bet`, `rate`, `max` | `false`, `1`, `2`, `250000` | `{prefix}bj <bet>` — reacts 👊 (hit) while points ≤ 17, 🛑 (stand) above |
| `highlow` | `mode`, `bet`, `rate`, `max` | `false`, `10`, `2`, `250000` | `{prefix}hl <bet>` — guesses Higher/Lower via buttons, cashes out at ×2 (min bet 10) |
| `delay.min` / `delay.max` | number | `0.5` / `1` | Random delay (s) between games in a cycle |
| `cooldown.min` / `cooldown.max` | int | `60` / `120` | Random sleep (s) after a full gamble cycle |

Martingale for all games: a loss multiplies the next bet by `rate`, a win (or hitting `max`) resets it to `bet`.

With 2+ accounts configured, friend quests (battle, cookie, pray, curse, action) are solved by the other accounts.

</details>

<details>
<summary><b>quest.txt</b> — Discord quests autocompleter</summary>

Plain text, **one token per line**. Lines starting with `#` are ignored — the only config file that isn't JSON.

```
# one token per line
TOKEN_A
TOKEN_B
```

Uses Discord's HTTP API directly. Every 5 minutes it fetches available quests, auto-accepts eligible ones and completes the supported types (watch video, play on desktop, stream, play activity), respects rate limits, and processes up to 100 quests in parallel.

</details>

<details>
<summary><b>chat.json</b> — auto-chat</summary>

Sends messages from `assets/messages.txt` (one message per line) into the channels you list — a random channel and a random message every time.

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
| `chat_channel_id` | array of int | `[]` | Channels to send in (random pick per message). Empty → account skipped |
| `cooldown.min` / `cooldown.max` | int | `60` / `120` | Random seconds between messages |
| `exist` | bool | `false` | `false` = send then instantly delete (ghost). `true` = leave the message |

</details>

<details>
<summary><b>voice.json</b> — voice keep-connected</summary>

Keeps each account connected to a voice channel; every 60 s it checks the connection and reconnects if it dropped.

```json
{
    "YOUR_TOKEN": 123456789
}
```

The key is the account token, the value is the voice channel ID (a number — no quotes).

</details>

---

## IMPORTANCE

### Tips

- **Open the web UI from another device** on the same network: `http://<IP printed in terminal>:2010`.
- **Avoid using overly short or generic names** such as "bear", "pink", ".,;:?!@#$%^&*" or similar. These names are highly likely to overlap with other players, which can confuse the system during message recognition and may even cause serious errors. Choose a distinct, clear, and uncommon name instead. A name like "Phamdat" can still work if it is not commonly used, because the system relies on the name to accurately match bot replies.
- **Do not attach too many accounts to the same channel**. Doing so can flood the message flow, reduce efficiency, and make the system less reliable. If it is unavoidable, proceed with caution and only when absolutely necessary.

### OwO

- **Do not let the inventory become too large**. An overloaded inventory can trigger excessive message overflow, and the system may only recognize the first inventory message while later ones are skipped. This prevents important information from being scanned correctly. Avoid buying large quantities of rings, stacking thousands of boxes, crates, and other bulk inventory items.
- **Quest features require the correct OWO settings**. To make quests work properly, you must configure the settings from the `owobs` command, as shown in the image at [assets/tips/owo_settings.png](assets/tips/owo_settings.png). Without this setup, the quest system may not function correctly.

---

## License

This project is licensed under the **Phamdat Selfbot - Educational License**. See [LICENSE](LICENSE) for details.

- Educational use only.
- Selling or commercial use is strictly prohibited.
- Credit required when referencing or borrowing code.
- Provided "as is" - the author assumes no liability for misuse or any consequences arising from use.
