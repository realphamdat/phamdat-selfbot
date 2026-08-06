import asyncio

import discord

from modules.utils.components import iter_children, section_content


class OWOSettings:
    @staticmethod
    async def apply(client):
        channel = client.current_channel
        if not channel:
            return

        await channel.send(f'{client.prefix}bs')
        client.logger.info(f'Sent {client.prefix}bs')

        msg = await OWOSettings._find_settings_message(client, channel)
        if not msg:
            client.logger.critical('User Settings message not found, quest data may be wrong')
            return

        if await OWOSettings._apply_user_settings(client, msg):
            await OWOSettings._verify_user_settings(client, channel, msg.id)
        else:
            client.logger.info('User Settings already correct')

    @staticmethod
    async def _find_settings_message(client, channel):
        try:
            return await client.wait_for(
                'message',
                check=lambda m: (
                    client.is_owo_message(m, in_channel=True)
                    and m.components
                    and OWOSettings._has_settings_header(m)
                ),
                timeout=2,
            )
        except asyncio.TimeoutError:
            pass
        try:
            async for m in channel.history(limit=5):
                if client.is_owo_message(m) and m.components and OWOSettings._has_settings_header(m):
                    return m
        except discord.HTTPException:
            client.logger.exception('Failed to fetch User Settings history')
        return None

    @staticmethod
    def _has_settings_header(message):
        for child in iter_children(message):
            content = getattr(child, 'content', '')
            if content and '## User Settings' in content:
                return True
        return False

    @staticmethod
    async def _apply_user_settings(client, message):
        clicked = False
        for child in iter_children(message):
            accessory = getattr(child, 'accessory', None)
            if not accessory or not hasattr(accessory, 'click'):
                continue
            content = section_content(child)
            label = getattr(accessory, 'label', '')
            if 'Quest Display' in content and label == 'image':
                if await OWOSettings._click(client, accessory, 'Quest Display -> text'):
                    clicked = True
            elif 'Achievement Display' in content and label == 'image':
                if await OWOSettings._click(client, accessory, 'Achievement Display -> text'):
                    clicked = True
            elif 'Quest Completion Notifications' in content and label == 'false':
                if await OWOSettings._click(client, accessory, 'Quest Completion Notifications -> true'):
                    clicked = True
        return clicked

    @staticmethod
    async def _click(client, accessory, label):
        await asyncio.sleep(1)
        try:
            await accessory.click()
            client.logger.info(f'Set {label}')
            return True
        except discord.HTTPException:
            client.logger.exception(f'Failed to set {label}')
            return False

    @staticmethod
    async def _verify_user_settings(client, channel, message_id):
        try:
            refreshed = await channel.fetch_message(message_id)
        except discord.HTTPException:
            client.logger.warning('Could not verify User Settings')
            return

        display = notify = None
        for child in iter_children(refreshed):
            accessory = getattr(child, 'accessory', None)
            if not accessory:
                continue
            content = section_content(child)
            label = getattr(accessory, 'label', '')
            if 'Quest Display' in content:
                display = label
            elif 'Quest Completion Notifications' in content:
                notify = label

        if display == 'text' and notify == 'true':
            client.logger.info('User Settings OK (Quest Display=text, Quest Notifications=true)')
        else:
            client.logger.warning(f'User Settings wrong: display={display} notify={notify}')
