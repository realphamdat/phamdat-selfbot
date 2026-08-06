import asyncio
import time

import discord

from modules.utils.components import iter_children, section_content
from modules.bots.owo.daily import Daily


class Boss:
    @staticmethod
    async def handle(client, message):
        if not client.is_owo_message(message):
            return
        if not client.can_run():
            return

        for child in iter_children(message):
            content = section_content(child)
            if not content or 'A Guild Boss Appeared!' not in content:
                continue

            button = getattr(child, 'accessory', None)
            if not button or getattr(button, 'custom_id', '') != 'guildboss_fight':
                continue
            if getattr(button, 'disabled', False):
                return

            channel = message.channel
            watch_task = asyncio.create_task(Boss._watch_ticket_response(client, channel))
            try:
                await button.click()
            except discord.HTTPException:
                watch_task.cancel()
                await asyncio.gather(watch_task, return_exceptions=True)
                client.logger.exception('Failed to click boss fight')
                return

            client.logger.info(f'Joined boss battle in #{channel}')
            await watch_task
            break

    @staticmethod
    async def _watch_ticket_response(client, channel):
        try:
            await client.wait_for(
                'message',
                check=lambda m: (
                    m.channel.id == channel.id
                    and m.interaction is not None
                    and "you don't have any boss tickets" in m.content.lower()
                ),
                timeout=5,
            )
        except asyncio.TimeoutError:
            return

        wait = Daily.reset_time(client.cooldown_reset)
        client.cooldown_boss = wait + time.time()
        client.logger.info(f'Boss out of tickets, paused {wait}s until daily reset')
