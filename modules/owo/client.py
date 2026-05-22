"""
OWO Discord Self-bot Client.
Each token gets one OWOClient instance.
"""

import discord
import time

from modules.utils.logger import get_logger
from modules.utils.constants import MESSAGES_FILE
from modules.owo.constants import OWO_BOT_ID, OWO_ACTIONS_FILE

class OWOClient(discord.Client):
    """Discord self-bot client for OWO automation."""

    def __init__(self, clients, token, config, pending_captchas = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.clients = clients          # Shared list of all OWOClient instances
        self._token = token
        self.config = config
        self.prefix = config['prefix']
        self.owo_bot = None             # discord.User for OWO bot
        self.current_channel = None     # Current working channel
        self.current_channel_id = None
        self.nickname = ''

        # State flags
        self.selfbot_running = False
        self.captcha_pending = False
        self._on_ready_done = False

        # Cooldowns
        self.cooldown_daily = 0
        self.cooldown_quest = 0
        self.cooldown_huntbot = 0
        self.cooldown_glitch = 0
        self.cooldown_lottery = 0
        self.cooldown_reset = 0

        # Quest flags
        self.quest_flags = {
            'owo': False, 'hunt': False, 'battle': False,
            'gamble': False, 'action_someone': False,
            'battle_friend': False, 'cookie': False,
            'pray': False, 'curse': False, 'action_you': False,
        }
        self.doing_quest = False
        self.current_quest = None

        # Gamble state
        self.bet_slot = int(config['gamble']['slot']['bet'])
        self.bet_coinflip = int(config['gamble']['coinflip']['bet'])
        self.bet_blackjack = int(config['gamble']['blackjack']['bet'])

        # Misc
        self.ga_joined = set()
        self.block_battle = False
        self.block_pray_curse = False
        self.no_gem = False
        self.special_pet_available = True
        self.inventory_str = 'gem1 gem3 gem4 star'
        self.last_owo_message_time = time.time()

        # Load shared assets
        self._load_assets()

        # Sub-modules (initialized in on_ready)
        self.task_manager = None
        self.captcha_handler = None
        self.logger = None

        # Check if this account has pending captcha
        self._pending_captchas = pending_captchas or set()

    def _load_assets(self):
        """Load action list and random messages."""
        try:
            with open(OWO_ACTIONS_FILE, 'r', encoding='utf-8') as f:
                self.owo_actions = [l.strip() for l in f if l.strip()]
        except Exception:
            self.owo_actions = ['cuddle', 'hug', 'kiss', 'pat', 'poke', 'slap']

        try:
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                self.random_messages = [l.strip() for l in f if l.strip()]
        except Exception:
            self.random_messages = ['hello world']

    async def on_ready(self):
        if self._on_ready_done:
            return
        self._on_ready_done = True

        self.logger = get_logger(f'{self.user.name}')
        self.owo_bot = self.get_user(OWO_BOT_ID)

        # Create DM with OWO bot
        try:
            if self.owo_bot:
                await self.owo_bot.create_dm()
        except Exception:
            pass

        # Setup channel
        from modules.owo.channel import Channel
        self.channel_mgr = Channel(self)
        await self.channel_mgr.init_channel()

        # Setup sub-modules
        from modules.owo.captcha import CaptchaHandler
        from modules.owo.task import TaskManager

        self.captcha_handler = CaptchaHandler(self)
        self.task_manager = TaskManager(self)

        # Check if this account has pending captcha for owo
        if str(self.user.id) in self._pending_captchas:
            self.captcha_pending = True
            self.logger.warning('Has pending captcha - OWO features paused')
        else:
            self.selfbot_running = True

        self.logger.info(f'Ready in #{self.current_channel} ({self.current_channel_id})')

        # Start task loops
        await self.task_manager.start()

    async def on_message(self, message):
        if not self.owo_bot:
            return

        # Update last OWO message time
        if message.author.id == OWO_BOT_ID:
            self.last_owo_message_time = time.time()

        # Captcha detection (always active)
        if self.captcha_handler:
            await self.captcha_handler.detect(message)

        # Skip further processing if not running
        if not self.selfbot_running:
            return

        # Problem detection (ban, no cowoncy)
        from modules.owo.problem import Problem
        await Problem.check(self, message)

        # Channel: change when mentioned
        cfg_ch = self.config['changing_channel']
        if cfg_ch['when_mentioned']:
            await self.channel_mgr.change_when_mentioned(message)

        # Channel: accept challenge / change when challenge
        if cfg_ch['when_challenge'] or self.quest_flags['battle_friend']:
            await self.channel_mgr.accept_challenge(message)

        # Quest progress
        if self.config['quest']:
            from modules.owo.quest import Quest
            await Quest.quest_progress(self, message)

        # Gem check
        if self.config['gem']['use'] or self.config['gem']['glitch']:
            from modules.owo.gem import Gem
            await Gem.check_gem(self, message)

    async def on_message_edit(self, before, after):
        if not self.selfbot_running or not self.owo_bot:
            return

        # Giveaway
        if self.config['giveaway']:
            from modules.owo.giveaway import Giveaway
            await Giveaway.join(self, after)

        # Gamble checks
        gamble_cfg = self.config['gamble']
        if gamble_cfg['slot']['mode'] or self.quest_flags['gamble']:
            from modules.owo.gamble import Gamble
            await Gamble.check_slot(self, after)

        if gamble_cfg['coinflip']['mode'] or self.quest_flags['gamble']:
            from modules.owo.gamble import Gamble
            await Gamble.check_coinflip(self, after)

    def is_owo_message(self, message, in_channel=False):
        """Check if message is from OWO bot, optionally in current channel."""
        if message.author.id != OWO_BOT_ID:
            return False
        if in_channel and message.channel.id != self.current_channel_id:
            return False
        return True

    def msg_contains(self, message, all_of=None, any_of=None):
        """Check message content contains required strings."""
        content = message.content
        if all_of and not all(t in content for t in all_of):
            return False
        if any_of and not any(t in content for t in any_of):
            return False
        return True