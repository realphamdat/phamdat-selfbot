import random
import asyncio

class Spam:
    @staticmethod
    async def send_owo(client):
        if not client.selfbot_running or not client.current_channel: return
        say = random.choice(['owo', 'uwu'])
        await client.current_channel.send(say)
        client.logger.info(f'Sent {say}')

    @staticmethod
    async def send_hunt(client):
        if not client.selfbot_running or not client.current_channel: return
        cmd = random.choice(['h', 'hunt'])
        await client.current_channel.send(f'{client.prefix}{cmd}')
        client.logger.info(f'Sent {client.prefix}{cmd}')

    @staticmethod
    async def send_battle(client):
        if not client.selfbot_running or not client.current_channel: return
        if client.block_battle: return
        cmd = random.choice(['b', 'battle'])
        await client.current_channel.send(f'{client.prefix}{cmd}')
        client.logger.info(f'Sent {client.prefix}{cmd}')

    @staticmethod
    async def spam_cycle(client):
        cfg = client.config['spam']
        delay_min = cfg['delay']['min']
        delay_max = cfg['delay']['max']

        should_owo = cfg['owo/uwu'] or client.quest_flags['owo']
        should_hunt = cfg['hunt'] or client.quest_flags['hunt']
        should_battle = cfg['battle'] or client.quest_flags['battle']

        try:
            if should_owo:
                await Spam.send_owo(client)
                await asyncio.sleep(random.uniform(delay_min, delay_max))

            if should_hunt:
                await Spam.send_hunt(client)
                await asyncio.sleep(random.uniform(delay_min, delay_max))

            if should_battle:
                await Spam.send_battle(client)
                await asyncio.sleep(random.uniform(delay_min, delay_max))
        except Exception: client.logger.exception('Spam error')