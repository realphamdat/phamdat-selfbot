class Giveaway:
    @staticmethod
    async def join(client, message):
        if not client.selfbot_running: return
        if not client.is_owo_message(message): return
        if message.id in client.ga_joined: return
        if not message.embeds: return
        if 'New Giveaway' not in str(message.embeds[0].author.name): return
        if not message.components: return

        try:
            button = message.components[0].children[0]
            await button.click()
            client.ga_joined.add(message.id)
            client.logger.info(f'Joined giveaway ({message.id})')
        except Exception as e:
            if 'COMPONENT_VALIDATION_FAILED' in str(e): client.ga_joined.add(message.id)
            else: client.logger.exception('Giveaway join error')