import asyncio
import random
import time

from modules.owo.daily import Daily
from modules.owo.quest import Quest
from modules.owo.spam import Spam
from modules.owo.huntbot import Huntbot
from modules.owo.gem import Gem
from modules.owo.gamble import Gamble

class TaskManager:
    def __init__(self, client):
        self.client = client
        self._tasks = []
        self._running = False

    async def start(self):
        if self._running: return
        self._running = True

        todo = [(self._loop_offline_check, 35)]
        if self.client.config['daily']: todo.append((self._loop_daily, 0))
        if self.client.config['quest']: todo.append((self._loop_quest, 0))
        if self.client.config['huntbot']: todo.append((self._loop_huntbot, 5))
        if self._spam_enabled(): todo.append((self._loop_spam, 10))
        if self.client.config['gem']['glitch']: todo.append((self._loop_glitch, 15))
        if self._gamble_enabled(): todo.append((self._loop_gamble, 25))
        if len(self.client.config['channels_id']) > 1: todo.append((self._loop_channel, 30))

        for coro_func, delay in sorted(todo, key=lambda item: item[1]):
            if delay > 0:
                await asyncio.sleep(delay)
            task = asyncio.create_task(coro_func())
            self._tasks.append(task)

        self.client.logger.info('All tasks started')

    def create_background(self, coro, name=None):
        task = asyncio.create_task(coro, name=name)
        self._tasks.append(task)
        return task

    def _spam_enabled(self):
        cfg = self.client.config['spam']
        return cfg['owo/uwu'] or cfg['hunt'] or cfg['battle']

    def _gamble_enabled(self):
        cfg = self.client.config['gamble']
        return cfg['lottery']['mode'] or cfg['slot']['mode'] or cfg['coinflip']['mode'] or cfg['blackjack']['mode']

    async def stop(self):
        self._running = False
        for task in self._tasks:
            if not task.done(): task.cancel()

        if self._tasks: await asyncio.gather(*self._tasks, return_exceptions = True)

        self._tasks = []
        self.client.logger.info('All tasks stopped')

    async def _loop_daily(self):
        try:
            while self._running:
                if self.client.selfbot_running and self.client.config['daily']:
                    try: await Daily.claim(self.client)
                    except Exception: self.client.logger.exception('Daily error')
                await asyncio.sleep(60)
        except asyncio.CancelledError: pass

    async def _loop_quest(self):
        try:
            while self._running:
                if self.client.selfbot_running and self.client.config['quest']:
                    if self.client.cooldown_quest - time.time() <= 0:
                        try: await Quest.do_quest(self.client)
                        except Exception: self.client.logger.exception('Quest error')
                await asyncio.sleep(60)
        except asyncio.CancelledError: pass

    async def _loop_huntbot(self):
        try:
            while self._running:
                if self.client.selfbot_running and self.client.config['huntbot']:
                    try:
                        await Huntbot.claim_submit(self.client)
                    except Exception:
                        self.client.logger.exception('Huntbot error')
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    async def _loop_spam(self):
        try:
            while self._running:
                if self.client.selfbot_running:
                    cfg = self.client.config['spam']
                    cooldown_min = cfg['cooldown']['min']
                    cooldown_max = cfg['cooldown']['max']

                    has_work = (
                        cfg['owo/uwu'] or cfg['hunt'] or cfg['battle']
                        or any(self.client.quest_flags[k] for k in ['owo', 'hunt', 'battle'])
                    )

                    if has_work:
                        try: await Spam.spam_cycle(self.client)
                        except Exception: self.client.logger.exception('Spam error')

                    await asyncio.sleep(random.randint(int(cooldown_min), int(cooldown_max)))
                else: await asyncio.sleep(5)
        except asyncio.CancelledError: pass

    async def _loop_glitch(self):
        try:
            while self._running:
                if self.client.selfbot_running and self.client.config['gem']['glitch']:
                    try: await Gem.check_glitch(self.client)
                    except Exception: self.client.logger.exception('Glitch check error')
                    await asyncio.sleep(random.randint(600, 1200))
                else:
                    await asyncio.sleep(5)
        except asyncio.CancelledError: pass

    async def _loop_gamble(self):
        try:
            while self._running:
                if self.client.selfbot_running:
                    cfg = self.client.config['gamble']
                    cooldown_min = cfg['cooldown']['min']
                    cooldown_max = cfg['cooldown']['max']

                    has_work = (
                        cfg['lottery']['mode']
                        or cfg['slot']['mode']
                        or cfg['coinflip']['mode']
                        or cfg['blackjack']['mode']
                        or self.client.quest_flags['gamble']
                    )

                    if has_work:
                        try: await Gamble.gamble_cycle(self.client)
                        except Exception: self.client.logger.exception('Gamble error')

                    await asyncio.sleep(random.randint(int(cooldown_min), int(cooldown_max)))
                else: await asyncio.sleep(5)
        except asyncio.CancelledError: pass

    async def _loop_channel(self):
        try:
            while self._running:
                channels = self.client.config['channels_id']
                if self.client.selfbot_running and len(channels) > 1:
                    cfg = self.client.config['changing_channel']
                    cooldown_min = cfg['after_elapsed_time']['min']
                    cooldown_max = cfg['after_elapsed_time']['max']
                    cooldown = random.randint(int(cooldown_min), int(cooldown_max))
                    self.client.logger.info(f'Next channel change in {cooldown}s')
                    await asyncio.sleep(cooldown)
                    try: await self.client.channel_mgr.change_channel(self.client)
                    except Exception: self.client.logger.exception('Channel change error')
                else:
                    await asyncio.sleep(5)
        except asyncio.CancelledError: pass

    async def _loop_offline_check(self):
        try:
            while self._running:
                if self.client.selfbot_running:
                    elapsed = time.time() - self.client.last_owo_message_time
                    if elapsed > 300:
                        try: await self._check_owo_alive()
                        except Exception: self.client.logger.exception('Offline check error')
                await asyncio.sleep(60)
        except asyncio.CancelledError: pass

    async def _check_owo_alive(self):
        if not self.client.current_channel: return

        action = random.choice(self.client.owo_actions)
        await self.client.current_channel.send(f'{self.client.prefix}{action}')
        self.client.logger.info(f'Offline check: sent {self.client.prefix}{action}')

        try:
            await self.client.wait_for(
                'message',
                check = lambda m: m.author.id == self.client.owo_bot.id,
                timeout = 10,
            )
            self.client.logger.info('OWO bot is online')
        except asyncio.TimeoutError:
            self.client.logger.warning('OWO bot appears offline')
            wait = random.randint(120, 300)
            self.client.logger.info(f'Pausing for {wait}s')
            self.client.selfbot_running = False
            await asyncio.sleep(wait)
            if not self.client.captcha_pending:
                self.client.selfbot_running = True
                self.client.logger.info('Resuming after offline pause')
