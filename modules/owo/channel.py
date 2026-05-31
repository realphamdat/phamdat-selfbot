import random

class Channel:
    @staticmethod
    async def init_channel(client):
        channels = client.config['channels_id']
        if not channels:
            client.logger.error('No channels configured')
            return

        client.current_channel_id = int(random.choice(channels))
        client.current_channel = client.get_channel(client.current_channel_id)

        if client.current_channel:
            await Channel.fetch_nickname(client)
        else:
            client.logger.error(f'Channel {client.current_channel_id} not found')

    @staticmethod
    async def fetch_nickname(client):
        try:
            guild = client.current_channel.guild
            member = await guild.fetch_member(client.user.id)
            client.nickname = member.nick or member.display_name
        except Exception:
            client.nickname = client.user.display_name

    @staticmethod
    async def change_channel(client):
        channels = client.config['channels_id']
        if len(channels) <= 1:
            return

        available = [c for c in channels if int(c) != client.current_channel_id]
        if not available:
            return

        client.current_channel_id = int(random.choice(available))
        client.current_channel = client.get_channel(client.current_channel_id)

        if client.current_channel:
            await Channel.fetch_nickname(client)
            client.logger.info(f'Changed channel to #{client.current_channel.name} ({client.current_channel_id})')
        else:
            client.logger.error(f'Channel {client.current_channel_id} not found')

    @staticmethod
    async def change_when_mentioned(client, message):
        if not client.selfbot_running:
            return
        if message.author.bot:
            return
        if message.channel.id != client.current_channel_id:
            return
        if not message.mentions:
            return

        if any(m.id == client.user.id for m in message.mentions):
            client.logger.info('Mentioned by someone, changing channel')
            await Channel.change_channel(client)

    @staticmethod
    async def accept_challenge(client, message):
        if not client.selfbot_running:
            return
        if not client.is_owo_message(message):
            return
        if f'<@{client.user.id}>' not in message.content:
            return
        if not message.embeds:
            return
        if not any('owo ab' in str(e.description) for e in message.embeds if e.description):
            return

        if client.quest_flags.get('battle_friend'):
            try:
                if message.components and message.components[0].children:
                    await message.components[0].children[0].click()
                    client.logger.info('Accepted battle challenge')
                else:
                    await message.channel.send(f'{client.prefix}ab')
                    client.logger.info(f'Sent {client.prefix}ab')
            except Exception:
                client.logger.exception('Failed to accept challenge')
            return

        if client.config['changing_channel']['when_challenge']:
            client.logger.info('Challenged, changing channel')
            await Channel.change_channel(client)
