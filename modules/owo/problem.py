"""
Problem detection: ban and no cowoncy.
"""

class Problem:
    @staticmethod
    async def check(client, message):
        """Check for ban or no cowoncy messages."""
        if not client.is_owo_message(message):
            return

        content = message.content

        # Banned detection
        if 'You have been banned' in content:
            is_relevant = (
                str(client.user.name) in content
                or (client.owo_bot and hasattr(client.owo_bot, 'dm_channel')
                    and client.owo_bot.dm_channel
                    and message.channel.id == client.owo_bot.dm_channel.id)
            )
            if is_relevant:
                client.selfbot_running = False
                client.logger.critical('BANNED - macro stopped')
                return

        # No cowoncy detection
        if ("don't have enough cowoncy" in content
                and str(client.nickname) in content
                and 'you silly hooman' not in content):
            client.selfbot_running = False
            client.logger.critical('Out of cowoncy - macro stopped')