"""
Channel management: init, change, mention detection, challenge accept.
"""

import random

class Channel:
    def __init__(self, client):
        self.client = client

    async def init_channel(self):
        """Set initial channel and nickname."""
        channels = self.client.config['channels_id']
        if not channels:
            self.client.logger.error('No channels configured')
            return
        self.client.current_channel_id = int(random.choice(channels))
        self.client.current_channel = self.client.get_channel(self.client.current_channel_id)
        if self.client.current_channel:
            await self._fetch_nickname()
        else:
            self.client.logger.error(f'Channel {self.client.current_channel_id} not found')

    async def _fetch_nickname(self):
        """Get the bot user's nickname in the current channel's guild."""
        try:
            guild = self.client.current_channel.guild
            member = await guild.fetch_member(self.client.user.id)
            self.client.nickname = member.nick or member.display_name
        except Exception:
            self.client.nickname = self.client.user.display_name

    async def change_channel(self):
        """Switch to a random different channel."""
        channels = self.client.config['channels_id']
        if len(channels) <= 1:
            return

        available = [c for c in channels if int(c) != self.client.current_channel_id]
        if not available:
            return

        self.client.current_channel_id = int(random.choice(available))
        self.client.current_channel = self.client.get_channel(self.client.current_channel_id)

        if self.client.current_channel:
            await self._fetch_nickname()
            self.client.logger.info(
                f'Changed channel to #{self.client.current_channel.name} ({self.client.current_channel_id})'
            )
        else:
            self.client.logger.error(f'Channel {self.client.current_channel_id} not found')

    async def change_when_mentioned(self, message):
        """Change channel when user is mentioned by a non-bot."""
        if not self.client.selfbot_running:
            return
        if message.author.bot:
            return
        if message.channel.id != self.client.current_channel_id:
            return
        if not message.mentions:
            return

        if any(m.id == self.client.user.id for m in message.mentions):
            self.client.logger.info('Mentioned by someone, changing channel')
            await self.change_channel()

    async def accept_challenge(self, message):
        """Accept or change channel when challenged (embed with 'owo ab')."""
        if not self.client.selfbot_running:
            return
        if not self.client.is_owo_message(message):
            return
        if f'<@{self.client.user.id}>' not in message.content:
            return
        if not message.embeds:
            return
        if not any('owo ab' in str(e.description) for e in message.embeds if e.description):
            return

        cfg = self.client.config['changing_channel']

        # If battle_friend quest is active, accept the challenge
        if self.client.quest_flags.get('battle_friend'):
            try:
                if message.components and message.components[0].children:
                    await message.components[0].children[0].click()
                    self.client.logger.info('Accepted battle challenge')
                else:
                    await message.channel.send(f'{self.client.prefix}ab')
                    self.client.logger.info(f'Sent {self.client.prefix}ab')
            except Exception:
                self.client.logger.exception('Failed to accept challenge')
            return

        # Otherwise, change channel if configured
        if cfg['when_challenge']:
            self.client.logger.info('Challenged, changing channel')
            await self.change_channel()
