import asyncio
import json
import logging
import random

import discord

logger = logging.getLogger('chat')

running = False


def load_config():
    try:
        with open('data/chat.json', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning('Chat config file not found: data/chat.json')
        return {}
    except json.JSONDecodeError as exc:
        logger.error('Chat config invalid JSON: %s', exc)
        return {}


def load_messages():
    try:
        with open('assets/messages.txt', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.warning('Chat messages file not found: assets/messages.txt')
        return []


async def _interruptible_sleep(seconds):
    while seconds > 0 and running:
        await asyncio.sleep(min(1.0, seconds))
        seconds -= 1.0


class ChatClient(discord.Client):
    def __init__(self, token, config, messages):
        super().__init__()
        self.token = token
        self.channel_ids = [int(c) for c in config.get('chat_channel_id', [])]
        self.cooldown = config.get('cooldown', {'min': 60, 'max': 120})
        self.exist = config.get('exist', False)
        self.messages = messages
        self.channels = []
        self._loop_task = None

    async def on_ready(self):
        for cid in self.channel_ids:
            channel = self.get_channel(cid)
            if channel is None:
                try:
                    channel = await self.fetch_channel(cid)
                except discord.HTTPException:
                    logger.exception(f'{self.user}: channel {cid} not found')
            if channel:
                self.channels.append(channel)
        if not self.channels:
            logger.error(f'{self.user}: no valid channels')
            return
        logger.info(f'{self.user} ready ({len(self.channels)} channel(s))')
        self._loop_task = asyncio.create_task(self._loop())

    async def _loop(self):
        if not self.messages:
            logger.warning(f'{self.user}: no chat messages to send')
            return

        try:
            while running and not self.is_closed():
                channel = random.choice(self.channels)
                content = random.choice(self.messages)
                preview = content if len(content) <= 80 else content[:77] + '...'
                channel_label = f'{getattr(channel, "name", None) or channel.id}'
                try:
                    sent = await channel.send('`' + content + '`')
                    if not self.exist:
                        await asyncio.sleep(0.5)
                        deleted = await self._delete_message(sent)
                        if deleted:
                            logger.info(f'{self.user}: sent and deleted message in {channel_label} -> "{preview}"')
                        else:
                            logger.warning(f'{self.user}: could not delete message in {channel_label} -> "{preview}"')
                    else:
                        logger.info(f'{self.user}: sent message in {channel_label} -> "{preview}"')
                except discord.HTTPException:
                    logger.exception(f'{self.user}: send failed in {channel_label}')
                await _interruptible_sleep(random.uniform(self.cooldown['min'], self.cooldown['max']))
        except asyncio.CancelledError:
            pass

    async def _delete_message(self, message, retries=3, delay=0.5):
        for attempt in range(retries):
            try:
                await message.delete()
                return True
            except discord.NotFound:
                return False
            except discord.HTTPException:
                if attempt + 1 == retries:
                    logger.exception('Delete failed after retries')
                    return False
                await asyncio.sleep(delay)

    async def stop_loop(self):
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass


async def _run_client(client):
    try:
        await client.start(client.token)
    except asyncio.CancelledError:
        pass
    except discord.LoginFailure:
        logger.error('Chat login failed')
    except Exception:
        logger.exception('Chat client error')
    finally:
        if not client.is_closed():
            await client.close()


async def _run():
    config = load_config()
    messages = load_messages()
    if not config or not messages:
        logger.warning('No chat config or messages')
        return
    clients = [
        ChatClient(token, cfg, messages)
        for token, cfg in config.items()
        if token and cfg.get('chat_channel_id')
    ]
    if not clients:
        logger.warning('No chat accounts configured')
        return
    logger.info(f'Starting {len(clients)} chat account(s)')
    tasks = [asyncio.create_task(_run_client(c)) for c in clients]
    while running and any(not t.done() for t in tasks):
        await asyncio.sleep(0.5)
    for c in clients:
        await c.stop_loop()
    for c in clients:
        if not c.is_closed():
            await c.close()
    await asyncio.gather(*tasks, return_exceptions=True)


def main():
    asyncio.run(_run())
