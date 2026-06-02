import discord
import time

from modules.core.config import deep_merge
from modules.utils.logger import get_logger
from modules.core.data_store import read_lines

from modules.owo.channel import Channel
from modules.owo.captcha import CaptchaHandler
from modules.owo.task import TaskManager
from modules.owo.problem import Problem
from modules.owo.quest import Quest
from modules.owo.gem import Gem
from modules.owo.giveaway import Giveaway
from modules.owo.gamble import Gamble
from modules.owo.defaults import OWO_DEFAULT_CONFIG

class OWOClient(discord.Client):

    def __init__(
            self, bot_name='owo', token='', token_hash='', config=None,
            shared_clients=None, pending_captchas=None, *args, **kwargs
            ):
        super().__init__(*args, **kwargs)

        self.bot_name = bot_name
        self.clients = shared_clients if shared_clients is not None else []
        self._token = token
        self.token_hash = token_hash
        self.config = deep_merge(OWO_DEFAULT_CONFIG, config or {})
        self.prefix = 'owo'
        self.owo_bot = None
        self.current_channel = None
        self.current_channel_id = None
        self.nickname = ''

        self.selfbot_running = False
        self.captcha_pending = False
        self._on_ready_done = False

        self.cooldown_daily = 0
        self.cooldown_quest = 0
        self.cooldown_huntbot = 0
        self.cooldown_glitch = 0
        self.cooldown_lottery = 0
        self.cooldown_reset = 0

        self.quest_flags = {
            'owo': False, 'hunt': False, 'battle': False,
            'gamble': False, 'action_someone': False,
            'battle_friend': False, 'cookie': False,
            'pray': False, 'curse': False, 'action_you': False,
        }
        self.doing_quest = False
        self.current_quest = None

        self.bet_slot = int(self.config['gamble']['slot']['bet'])
        self.bet_coinflip = int(self.config['gamble']['coinflip']['bet'])
        self.bet_blackjack = int(self.config['gamble']['blackjack']['bet'])

        self.ga_joined = set()
        self.block_battle = False
        self.block_pray_curse = False
        self.no_gem = False
        self.special_pet_available = True
        self.inventory_str = 'gem1 gem3 gem4 star'
        self.last_owo_message_time = time.time()

        self.task_manager = None
        self.captcha_handler = None
        self.logger = None

        self.owo_actions = read_lines('assets/owo/actions.txt')

        self._pending_captchas = pending_captchas or []

    async def on_ready(self):
        if self._on_ready_done: return
        self._on_ready_done = True

        self.logger = get_logger(f'{self.user.name}')
        self.owo_bot = self.get_user(408785106942164992)
        if not self.owo_bot:
            self.logger.critical("OWO bot not found. Make sure the account is in a server with OWO bot.")
            return

        try: await self.owo_bot.create_dm()
        except Exception: pass

        self.channel_mgr = Channel
        await self.channel_mgr.init_channel(self)

        self.captcha_handler = CaptchaHandler
        self.task_manager = TaskManager(self)

        account_pending = [
            c for c in self._pending_captchas
            if c.get('token_hash') == self.token_hash or str(c.get('user_id', '')) == str(self.user.id)
        ]
        if account_pending:
            self.captcha_pending = True
            self.logger.warning('Has pending captcha - OWO features paused')
            await self.captcha_handler.process_pending(self, account_pending)
        else: self.selfbot_running = True

        self.logger.info(f'Ready in #{self.current_channel} ({self.current_channel_id})')

        await self.task_manager.start()

    async def on_message(self, message):
        if not self.owo_bot: return

        if message.author.id == self.owo_bot.id: self.last_owo_message_time = time.time()

        if self.captcha_handler: await self.captcha_handler.detect(self, message)

        if not self.selfbot_running: return

        await Problem.check(self, message)

        cfg_ch = self.config['changing_channel']
        if cfg_ch['when_mentioned']: await self.channel_mgr.change_when_mentioned(self, message)
        if cfg_ch['when_challenge'] or self.quest_flags['battle_friend']: await self.channel_mgr.accept_challenge(self, message)

        if self.config['quest']: await Quest.quest_progress(self, message)

        if self.config['gem']['use'] or self.config['gem']['glitch']: await Gem.check_gem(self, message)

    async def on_message_edit(self, before, after):
        if not self.selfbot_running or not self.owo_bot: return

        if self.config['giveaway']: await Giveaway.join(self, after)

        gamble_cfg = self.config['gamble']
        if gamble_cfg['slot']['mode'] or self.quest_flags['gamble']: await Gamble.check_slot(self, after)
        if gamble_cfg['coinflip']['mode'] or self.quest_flags['gamble']: await Gamble.check_coinflip(self, after)

    def is_owo_message(self, message, in_channel = False):
        if message.author.id != self.owo_bot.id: return False
        if in_channel and message.channel.id != self.current_channel_id: return False
        return True

    @staticmethod
    def msg_contains(message, all_of = None, any_of = None):
        content = message.content
        if all_of and not all(t in content for t in all_of): return False
        if any_of and not any(t in content for t in any_of): return False
        return True
