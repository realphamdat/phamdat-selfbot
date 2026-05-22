"""
Task Manager: orchestrates all periodic loops for an OWO client.
Uses asyncio tasks instead of discord.ext.tasks for cleaner lifecycle.
"""

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
    """Manages all periodic tasks for a single OWO client."""

    def __init__(self, client):
        self.client = client
        self._tasks = []
        self._running = False

    async def start(self):
        """Start all task loops."""
        if self._running:
            return
        self._running = True

        self._tasks = [
            asyncio.create_task(self._loop_daily(), name='daily'),
            asyncio.create_task(self._loop_quest(), name='quest'),
            asyncio.create_task(self._loop_spam(), name='spam'),
            asyncio.create_task(self._loop_huntbot(), name='huntbot'),
            asyncio.create_task(self._loop_glitch(), name='glitch'),
            asyncio.create_task(self._loop_gamble(), name='gamble'),
            asyncio.create_task(self._loop_channel(), name='channel'),
            asyncio.create_task(self._loop_offline_check(), name='offline'),
        ]

        self.client.logger.info('All tasks started')

    async def stop(self):
        """Cancel all running tasks gracefully."""
        self._running = False
        for task in self._tasks:
            if not task.done():
                task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks = []
        self.client.logger.info('All tasks stopped')

    # ── Task Loops ──────────────────────────────────────────────

    async def _loop_daily(self):
        """Claim daily every minute."""
        try:
            await asyncio.sleep(5)
            while self._running:
                if self.client.selfbot_running and self.client.config['daily']:
                    try:
                        await Daily.claim(self.client)
                    except Exception:
                        self.client.logger.exception('Daily error')
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    async def _loop_quest(self):
        """Check and do quests every minute."""
        try:
            await asyncio.sleep(15)
            while self._running:
                if self.client.selfbot_running and self.client.config['quest']:
                    if self.client.cooldown_quest - time.time() <= 0:
                        try:
                            await Quest.do_quest(self.client)
                        except Exception:
                            self.client.logger.exception('Quest error')
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    async def _loop_spam(self):
        """Main spam loop (owo/hunt/battle)."""
        try:
            await asyncio.sleep(10)
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
                        try:
                            await Spam.spam_cycle(self.client)
                        except Exception:
                            self.client.logger.exception('Spam error')

                    await asyncio.sleep(random.randint(int(cooldown_min), int(cooldown_max)))
                else:
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    async def _loop_huntbot(self):
        """Claim/submit huntbot every minute."""
        try:
            await asyncio.sleep(20)
            while self._running:
                if self.client.selfbot_running and self.client.config['huntbot']:
                    try:
                        await Huntbot.claim_submit(self.client)
                    except Exception:
                        self.client.logger.exception('Huntbot error')
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    async def _loop_glitch(self):
        """Check for glitch/distortion periodically."""
        try:
            await asyncio.sleep(30)
            while self._running:
                if self.client.selfbot_running and self.client.config['gem']['glitch']:
                    try:
                        await Gem.check_glitch(self.client)
                    except Exception:
                        self.client.logger.exception('Glitch check error')
                await asyncio.sleep(random.randint(600, 1200))
        except asyncio.CancelledError:
            pass

    async def _loop_gamble(self):
        """Gamble loop."""
        try:
            await asyncio.sleep(25)
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
                        try:
                            await Gamble.gamble_cycle(self.client)
                        except Exception:
                            self.client.logger.exception('Gamble error')

                    await asyncio.sleep(random.randint(int(cooldown_min), int(cooldown_max)))
                else:
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    async def _loop_channel(self):
        """Periodically change channel."""
        try:
            await asyncio.sleep(random.randint(600, 1200))
            while self._running:
                channels = self.client.config['channels_id']
                if self.client.selfbot_running and len(channels) > 1:
                    try:
                        await self.client.channel_mgr.change_channel()
                    except Exception:
                        self.client.logger.exception('Channel change error')
                await asyncio.sleep(random.randint(600, 1200))
        except asyncio.CancelledError:
            pass

    async def _loop_offline_check(self):
        """Check if OWO bot is offline by monitoring last message time."""
        try:
            await asyncio.sleep(120)
            while self._running:
                if self.client.selfbot_running:
                    elapsed = time.time() - self.client.last_owo_message_time
                    # If no OWO message for 5 minutes, check
                    if elapsed > 300:
                        try:
                            await self._check_owo_alive()
                        except Exception:
                            self.client.logger.exception('Offline check error')
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    async def _check_owo_alive(self):
        """Actively check if OWO bot is responding."""
        if not self.client.current_channel:
            return

        action = random.choice(self.client.owo_actions)
        await self.client.current_channel.send(f'{self.client.prefix}{action}')
        self.client.logger.info(f'Offline check: sent {self.client.prefix}{action}')

        try:
            await self.client.wait_for(
                'message',
                check=lambda m: m.author.id == self.client.owo_bot.id,
                timeout=10,
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