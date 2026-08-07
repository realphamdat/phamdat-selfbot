import asyncio
import json
import logging

import discord

logger = logging.getLogger('voice')

running = False

CHECK_INTERVAL = 30


def log(msg):
    logger.info(msg)


def load_config():
    try:
        with open('data/voice.json', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning('Voice config file not found: data/voice.json')
        return {}
    except json.JSONDecodeError as exc:
        logger.error('Voice config invalid JSON: %s', exc)
        return {}


async def _interruptible_sleep(seconds):
    while seconds > 0 and running:
        await asyncio.sleep(min(1.0, seconds))
        seconds -= 1.0


class VoiceSession(discord.Client):
    def __init__(self, token, channel_id):
        super().__init__()
        self.token = token
        self.channel_id = int(channel_id)
        self.channel = None
        self._loop_task = None

    async def on_ready(self):
        self.channel = self.get_channel(self.channel_id)
        if self.channel is None:
            try:
                self.channel = await self.fetch_channel(self.channel_id)
            except discord.HTTPException:
                logger.exception(f'{self.user}: voice channel {self.channel_id} not found')
        if not self.channel:
            logger.error(f'{self.user}: voice channel {self.channel_id} not available')
            return
        log(f'{self.user}: ready for voice in {self.channel.name or self.channel.id}')
        self._loop_task = asyncio.create_task(self._loop())

    async def _loop(self):
        try:
            while running and not self.is_closed():
                voice_client = self.voice_clients[0] if self.voice_clients else None
                if voice_client and getattr(voice_client, 'is_connected', lambda: False)():
                    await _interruptible_sleep(CHECK_INTERVAL)
                    continue

                try:
                    await self.channel.connect()
                    log(f'{self.user}: joined voice in {self.channel.name or self.channel.id}')
                except discord.ClientException:
                    logger.warning(f'{self.user}: voice connection already exists or invalid state')
                except (discord.HTTPException, asyncio.TimeoutError, discord.ConnectionClosed) as exc:
                    logger.exception(f'{self.user}: voice join failed ({exc.__class__.__name__})')
                await _interruptible_sleep(CHECK_INTERVAL)
        except asyncio.CancelledError:
            pass

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
        logger.error('Voice login failed')
    except Exception:
        logger.exception('Voice client error')
    finally:
        if not client.is_closed():
            await client.close()


async def _run():
    config = load_config()
    if not config:
        logger.warning('No voice config')
        return
    clients = [
        VoiceSession(token, channel_id)
        for token, channel_id in config.items()
        if token and channel_id
    ]
    if not clients:
        logger.warning('No voice accounts configured')
        return
    log(f'Starting {len(clients)} voice account(s)')
    tasks = [asyncio.create_task(_run_client(c)) for c in clients]
    while running and any(not t.done() for t in tasks):
        await asyncio.sleep(1)
    for c in clients:
        await c.stop_loop()
    for c in clients:
        if not c.is_closed():
            await c.close()
    await asyncio.gather(*tasks, return_exceptions=True)


def main():
    asyncio.run(_run())