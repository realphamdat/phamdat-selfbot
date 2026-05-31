# PHAMDAT SELFBOT

> **A modular, multi‑account Discord selfbot framework with web dashboard, captcha solving, and extensible bot support (OWO, Karuta, Pokemeow, and more).**

[![License](https://img.shields.io/badge/License-AGPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-py--self-5865F2)](https://github.com/dolfies/discord.py-self)

---

## Table of Contents

- [About the Project](#about-the-project)
- [Legal & License](#legal--license)
- [Disclaimer](#disclaimer)
- [User Guide](#user-guide)
  - [Installation](#installation)
  - [Configuration Files](#configuration-files)
    - [Bot Configuration (owo.json)](#bot-configuration-owojson)
    - [Discord Quest Tokens (discord_quest.txt)](#discord-quest-tokens-discord_questtxt)
    - [Webhook Settings (settings.json)](#webhook-settings-settingsjson)
    - [Cache File (caches.json)](#cache-file-cachesjson)
  - [Getting Your Discord Token](#getting-your-discord-token)
  - [Running the Bot](#running-the-bot)
  - [Using the Web Dashboard](#using-the-web-dashboard)
    - [Dashboard (Control & Logs)](#dashboard-control--logs)
    - [Captcha Manager](#captcha-manager)
    - [Data File Editor](#data-file-editor)
  - [Multi‑Account & Multi‑Channel Setup](#multi-account--multi-channel-setup)
  - [Troubleshooting](#troubleshooting)
- [Contributing & Support](#contributing--support)

---

## About the Project

This tool is a **self‑hosted Discord selfbot** designed to automate interactions with various Discord game bots (OWO, Karuta, Pokemeow, etc.). It provides:

- **Multi‑account support** – run several Discord accounts simultaneously.
- **Web dashboard** – real‑time logs, captcha solving, and configuration editor.
- **Modular design** – easily add new bots via the extension system.
- **Automatic captcha handling** – image, hCaptcha, audio, iframe, and external link captchas.
- **Built‑in features for OWO** – daily, quests, huntbot, gambling, gems, giveaways, channel switching, and spam protection.

> **Important**: This project is constantly evolving. Future updates will introduce support for additional bots (Karuta, Pokemeow, etc.) and extensions (top.gg, etc.). The documentation focuses on the **core concepts** that remain valid regardless of which bot you configure.

---

## Legal & License

- **License**: This project is released under the **GNU Affero General Public License v3 (AGPLv3)**.  
  You may copy, modify, and distribute the code **only if** you make your modifications available under the same license and disclose the source code when you provide a service over a network.
- **Attribution**: Any public use (including modified versions) **must** give appropriate credit to the original author (`realphamdat`) and include a link to the original repository: [https://github.com/realphamdat/phamdat-selfbot](https://github.com/realphamdat/phamdat-selfbot).
- **Commercial use**: Selling this software or using it in a paid service is strictly prohibited without explicit permission.

---

## Disclaimer

**This software is provided for educational and personal use only.**  
By using this tool, you acknowledge and agree that:

- You are solely responsible for any consequences arising from its use.
- Automating user actions on Discord violates Discord’s Terms of Service. Your accounts **may be banned** if detected.
- The author assumes **no liability** for account suspensions, data loss, or any other damages.
- You will not use this software for malicious purposes (spam, harassment, attacks, etc.).

**Using this tool means you accept full responsibility.**  
Proceed at your own risk.

---

# User Guide

This section is written for **non‑programmers**. Every step is explained in plain language.

## Installation

### 1. Install Python

- Go to [python.org](https://python.org) and download **Python 3.9 or higher** (3.10, 3.11, or 3.12 recommended).
- During installation, **check the box** “Add Python to PATH”.
- Verify installation: open a **Command Prompt (Windows)** or **Terminal (Mac/Linux)** and type:
  ```bash
  python --version
  ```
  You should see something like `Python 3.10.11`.

### 2. Download the Project

Two ways:

- **Using Git** (recommended for updates):
  ```bash
  git clone https://github.com/realphamdat/phamdat-selfbot.git
  cd phamdat-selfbot
  ```

- **Manual ZIP**:
  - Go to [https://github.com/realphamdat/phamdat-selfbot](https://github.com/realphamdat/phamdat-selfbot)
  - Click the green “Code” button → “Download ZIP”
  - Extract the ZIP file to a folder of your choice.

### 3. Install Required Libraries

The project needs several Python packages. Open a terminal inside the project folder (where `main.py` is located) and run:

```bash
pip install -r requirements.txt
```

If you encounter errors, you can install them manually:

```bash
pip install discord.py-self flask flask-socketio pillow numpy requests aiohttp
```

<details>
<summary>Click to see common installation issues</summary>

- **`pip` not recognized**: Reinstall Python and enable “Add to PATH”.
- **Permission errors**: On Linux/Mac, try `pip install --user ...` or use `sudo` (not recommended).
- **Discord.py-self conflicts**: Uninstall any existing `discord.py` first (`pip uninstall discord.py`).

</details>

### 4. Prepare the Data Folder

Inside the project folder, create a subfolder named `data` (if not already present).  
This folder will store all your configuration and token files.

---

## Configuration Files

All configuration files are located inside the `data/` folder.  
The bot reads them when it starts. You can edit them with any text editor (Notepad, VS Code, etc.) **or** use the built‑in web editor (explained later).

### Bot Configuration (`owo.json`)

This file contains the settings for **OWO bot accounts**.  
The format is:

```json
{
  "YOUR_DISCORD_TOKEN_HERE": {
    // settings for this account
  },
  "ANOTHER_TOKEN_HERE": {
    // settings for second account
  }
}
```

Each token is a key, and its value is a JSON object with the configuration options.

**Default configuration** (you only need to specify values you want to change – missing keys will use built‑in defaults):

<details>
<summary>Click to view full default settings</summary>

```json
{
  "channels_id": [],
  "changing_channel": {
    "when_mentioned": true,
    "when_challenge": true,
    "after_elapsed_time": {"min": 300, "max": 600}
  },
  "daily": true,
  "quest": true,
  "huntbot": true,
  "giveaway": true,
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
```
</details>

**Explanation of common options** (alphabetical order):

| Option | Type | Description |
|--------|------|-------------|
| `channels_id` | array of numbers | List of text channel IDs where the bot will operate. The bot picks a random one at start and may switch later. |
| `changing_channel.when_mentioned` | boolean | If `true`, switches channel when someone mentions the bot. |
| `changing_channel.when_challenge` | boolean | If `true`, switches channel when challenged to a battle. |
| `changing_channel.after_elapsed_time` | object(min,max) | Switch channel automatically after a random interval (seconds). Set both to `0` to disable. |
| `daily` | boolean | Claim daily reward automatically. |
| `quest` | boolean | Automatically pick and complete quests. |
| `huntbot` | boolean | Automatically claim and submit huntbot passwords. |
| `giveaway` | boolean | Join giveaways automatically. |
| `spam.hunt` / `spam.battle` / `spam.owo/uwu` | boolean | Send hunt, battle, or owo/uwu messages. |
| `spam.delay` | object(min,max) | Random delay in seconds between each command inside a spam cycle. |
| `spam.cooldown` | object(min,max) | Random cooldown in seconds between full spam cycles. |
| `gem.use` | boolean | Automatically use gems to upgrade pets. |
| `gem.couple` | boolean | Use couple gems (requires `gem.use` true). |
| `gem.best` | boolean | Use highest‑tier gem available instead of the first. |
| `gem.star` | boolean | Use star gems (requires special pet). |
| `gem.glitch` | boolean | Check and claim gem glitch (`owo dt`). |
| `gem.openning.box` / `.crate` / `.flootbox` | boolean | Automatically open boxes, crates, or flootboxes when inventory is checked. |
| `gamble.lottery.mode` | boolean | Buy lottery tickets (amount set by `amount`). |
| `gamble.slot.mode` | boolean | Play slot machine. |
| `gamble.slot.bet` | number | Starting bet amount. |
| `gamble.slot.rate` | number | Multiplier when you lose (e.g., `2` doubles the next bet). |
| `gamble.slot.max` | number | Maximum bet allowed. |
| `gamble.cooldown` | object(min,max) | Random cooldown between gamble cycles. |

**Example minimal configuration** for one account (all other options will use defaults):

```json
{
  "PASTE_YOUR_TOKEN_HERE": {
    "channels_id": [123456789012345678, 987654321098765432],
    "daily": true,
    "spam": {
      "hunt": true,
      "battle": false
    }
  }
}
```

**Note**: The token must be a **Discord user token** (not a bot token). See “Getting Your Discord Token” below.

### Discord Quest Tokens (`discord_quest.txt`)

A separate module that automatically completes Discord quests (watching videos, playing games, etc.).  
Place **one token per line** (no quotes, no extra spaces). Example:

```
Nz... (first token)
ND... (second token)
```

Only tokens that you want to run the quest module should be listed here. This file is optional – if empty, the quest module does nothing.

### Webhook Settings (`settings.json`)

When a captcha is detected, the bot can send a notification to a Discord webhook.  
Example:

```json
{
  "discord_webhook": {
    "url": "https://discord.com/api/webhooks/...",
    "content": "@everyone @here <@&role_id> <@user_id>"
  }
}
```

- `url`: Your Discord webhook URL.
- `content`: The message content (supports mentions). Remove this line if you don’t want extra text.

If you don’t need webhook notifications, delete the `discord_webhook` section or leave the file empty `{}`.

### Cache File (`caches.json`)

**Do not edit this file manually.**  
It stores pending captchas and is managed automatically by the bot. If you delete it, the bot will recreate it.

---

## Getting Your Discord Token

**Warning:** Your Discord token is like a password. **Never share it with anyone.** Treat it with the same care as your login credentials.

Follow these steps to obtain your user token:

1. Open Discord in your **browser** (not the desktop app).
2. Press `F12` (or `Ctrl+Shift+I` on Windows/Linux, `Cmd+Option+I` on Mac) to open Developer Tools.
3. Go to the **Application** tab (Chrome/Edge) or **Storage** tab (Firefox).
4. In the left sidebar, expand **Cookies** and select `https://discord.com`.
5. Look for a cookie named `token`.
6. Copy its **Value** (a long string of letters and numbers).

<details>
<summary>Alternative method (if you cannot find the cookie)</summary>

- Go to the **Network** tab.
- Reload the page (`F5`).
- Click on any request (e.g., `science`).
- Look under **Request Headers** for `Authorization`. The value is your token.
</details>

Paste this token into the configuration files as described above (without any quotes inside the string itself – the JSON file requires quotes around the **key**, but the token value is a string and must be inside double quotes as well).

**Correct:**

```json
{
  "Nz...token...": {}
}
```

**Incorrect:**

```json
{
  Nz...token...: {}
}
```

---

## Running the Bot

1. Open a terminal inside the project folder.
2. Run the main script:
   ```bash
   python main.py
   ```
3. You will see a message like:
   ```
   Website: http://192.168.1.10:2010
   ```
   This is the address of the web dashboard. Open it in your browser.

**To stop the bot**, press `Ctrl+C` in the terminal **or** click the “Stop” button on the web dashboard.

**Note:** The bot runs a web server on port `2010` by default. If you need to change the port, edit `main.py` (find `port=2010` and change the number). No other code modifications are required.

---

## Using the Web Dashboard

The dashboard is the main control center. It has three pages: **Dashboard**, **Captcha**, and **Data**.

### Dashboard (Control & Logs)

- **Start/Stop button** – starts or stops all bot accounts.
- **Runtime counter** – shows how long the bot has been running.
- **Live terminal** – displays all logs from the bot (info, warnings, errors). You can:
  - Clear the terminal.
  - Toggle auto‑scroll (locks scrolling).
- **Captcha badge** – shows the number of pending captchas (also visible in the sidebar).

### Captcha Manager

When any bot account encounters a captcha (image, hCaptcha, audio, or external link), it appears here.

For each captcha you can:

- **Solve** – opens a modal with the appropriate interface:
  - **Image captcha**: Shows the image, an input field to type the answer.
  - **Audio captcha**: Plays the audio, input field for the answer.
  - **hCaptcha / reCAPTCHA / Turnstile**: Loads the widget automatically – solving it sends the token to the bot.
  - **Iframe**: Embeds a website where you solve the captcha.
  - **External link**: Opens a new tab to solve; click “Done” after solving.
- **Jump** – opens the Discord message that contains the captcha (for context).
- **Delete** – removes the captcha and resumes the bot (useful for false positives).

When you successfully solve a captcha, the bot automatically resumes its activities. If the bot is not running, the answer is saved and the bot will start automatically when you press “Start”.

### Data File Editor

This page lets you edit any text/JSON file inside the `data/` folder directly from your browser.

- **File list** on the left – click a file to open it.
- **Editor** with line numbers and syntax highlighting for JSON.
- **Save** (or `Ctrl+S`) – saves changes back to disk.
- **Cancel** – discards changes.
- **View** – shows a diff (what changed) before saving.

**Important:** Always validate your JSON syntax. The editor will warn you if you introduce errors.

---

## Multi‑Account & Multi‑Channel Setup

### Multiple Accounts

Simply add more entries to the bot configuration file (e.g., `owo.json`). Example:

```json
{
  "FIRST_TOKEN": { "channels_id": [123] },
  "SECOND_TOKEN": { "channels_id": [456] },
  "THIRD_TOKEN": { "channels_id": [789], "daily": false }
}
```

Each account runs independently – they can have different settings.

### Multiple Channels

Inside an account’s configuration, `channels_id` accepts an array of channel IDs. The bot will randomly select one channel at startup and may switch channels based on rules.

**How to get a channel ID:**
- Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode).
- Right‑click any text channel → “Copy ID”.

**Example** – account that switches between three channels:
```json
{
  "YOUR_TOKEN": {
    "channels_id": [111111111111111111, 222222222222222222, 333333333333333333]
  }
}
```

### Channel Switching Rules

- `when_mentioned`: If someone mentions the bot, it switches to another channel from the list.
- `when_challenge`: If someone challenges the bot to a battle, it switches channel.
- `after_elapsed_time`: The bot will switch channel after a random interval between `min` and `max` seconds.

Set any rule to `false` or remove it to disable.

---

## Troubleshooting

### “No accounts configured for bot: owo”

- Ensure `data/owo.json` exists and contains at least one valid token entry.
- Check that the token is inside double quotes and the JSON syntax is correct (use a JSON validator like [jsonlint.com](https://jsonlint.com)).

### Bot starts but does nothing

- Verify the bot is in a server that has the OWO bot (or the intended bot) and that the channel ID is correct.
- Check the logs in the web dashboard – there may be error messages.
- Make sure the token is valid (try logging into Discord with that token via a browser? Not recommended; use a token checker tool).

### Captcha not showing in the web dashboard

- The bot automatically sends captchas to the dashboard. Wait a few seconds.
- If using hCaptcha, make sure the bot can access `owobot.com` (no firewall blocking).

### “ModuleNotFoundError: No module named ‘discord’”

- You installed the wrong library. Run:
  ```bash
  pip uninstall discord.py discord.py-self
  pip install discord.py-self
  ```

### Web interface not accessible

- Make sure the bot is running (`python main.py`).
- The URL shown in the terminal is correct. If you are on the same machine, try `http://localhost:2010`.
- Check firewall settings – port 2010 must be open.

### I want to add support for a different bot (Karuta, etc.)

This framework is extensible. Future versions will include built‑in modules for other bots. For now, you can write your own extension (advanced). Contact the author for guidance.

---

## Contributing & Support

- **Issues & feature requests**: Open an issue on [GitHub](https://github.com/realphamdat/phamdat-selfbot/issues).
- **Discussions**: Use GitHub Discussions for questions.
- **Contributions**: Pull requests are welcome if you follow the AGPLv3 license.

**Do not** ask for help with stealing tokens, mass DM spam, or any malicious activity. Such requests will be ignored.

---

## Final Notes

This documentation will **not** be updated frequently. The bot continues to evolve, but the core principles (multi‑account, web dashboard, captcha handling) remain the same. For the latest changes, check the repository’s commit history.

**Thank you for using PHAMDAT SELFBOT.**  
Use it responsibly and respect Discord’s Terms of Service.

---

*Documentation version 1.0 – Last updated 2026-05-31*