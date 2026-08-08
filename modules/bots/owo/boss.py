import asyncio
import time

import discord

from modules.bots.owo.daily import Daily


class Boss:
    @staticmethod
    async def handle(client, message):
        if not client.is_owo_message(message):
            return
        if not client.can_run():
            return
        if not message.components:
            return

        container = message.components[0]
        children = getattr(container, 'children', None)
        if not children:
            return

        if 'A Guild Boss Appeared!' not in Boss._section_text(children[0]):
            return

        fight = getattr(children[-1], 'accessory', None)
        if fight is None or getattr(fight, 'disabled', False):
            return

        channel = message.channel
        watch_task = asyncio.create_task(Boss._watch_ticket_response(client, channel))
        try:
            await fight.click()
        except discord.HTTPException:
            watch_task.cancel()
            await asyncio.gather(watch_task, return_exceptions=True)
            client.logger.exception('Failed to click boss fight')
            return

        client.logger.info(f'Joined boss battle in #{channel}')
        await watch_task

    @staticmethod
    def _section_text(section):
        parts = [getattr(child, 'content', '') for child in getattr(section, 'children', []) or []]
        return '\n'.join(part for part in parts if part)

    @staticmethod
    async def _watch_ticket_response(client, channel):
        try:
            await client.wait_for(
                'message',
                check=lambda m: (
                    m.channel.id == channel.id
                    and m.interaction is not None
                    and "You don't have any boss tickets!" in m.content
                ),
                timeout=10,
            )
        except asyncio.TimeoutError:
            return

        wait = Daily.reset_time(client.cooldown_reset)
        client.cooldown_boss = wait + time.time()
        client.logger.info(f'Boss out of tickets, paused {wait}s until daily reset')
