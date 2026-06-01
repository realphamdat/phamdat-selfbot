import io
import re
import aiohttp
import asyncio

from PIL import Image

from modules.owo.oauth import CaptchaSolver
from modules.utils.captcha_manager import CaptchaManager
from modules.utils.captcha_store import CaptchaStore

class CaptchaHandler:
    @staticmethod
    async def get_image_height(client, attachment):
        if attachment.height is not None:
            return attachment.height
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).height
        except Exception:
            client.logger.exception('Failed to get image height fallback')
            return 0

    @staticmethod
    async def detect(client, message):
        if not client.owo_bot:
            return

        content = message.content
        is_owo = message.author.id == client.owo_bot.id

        if client.captcha_pending and is_owo:
            is_dm = hasattr(client.owo_bot, 'dm_channel') and client.owo_bot.dm_channel
            if is_dm and message.channel.id == client.owo_bot.dm_channel.id and client.msg_contains(message, any_of = ['👍', 'thumbsup']):
                await CaptchaHandler.mark_solved(client)
                return

        if client.captcha_pending or not is_owo:
            return

        clean = re.sub(r'[^0-9a-zA-Z]', '', content)
        is_dm = hasattr(client.owo_bot, 'dm_channel') and client.owo_bot.dm_channel
        in_dm = is_dm and message.channel.id == client.owo_bot.dm_channel.id

        is_image = (
            message.attachments
            and await CaptchaHandler.get_image_height(client, message.attachments[0]) <= 100
            and (in_dm or f'**⚠️ | {client.user.name}**' in content)
        )

        is_hcaptcha = (
            f'<@{client.user.id}>' in content
            and hasattr(message, 'components') and message.components
            and any(
                'verify' in getattr(child, 'label', '').lower()
                for row in message.components
                for child in getattr(row, 'children', [])
            )
        )

        if not (is_image or is_hcaptcha):
            return

        client.captcha_pending = True
        client.selfbot_running = False

        if is_image:
            await CaptchaHandler.handle_image_captcha(client, message, clean)
        elif is_hcaptcha:
            await CaptchaHandler.handle_hcaptcha(client, message)

    @staticmethod
    async def handle_image_captcha(client, message, clean):
        client.logger.warning('Image captcha detected')
        image_url = message.attachments[0].url if message.attachments else None
        length = '?'

        try:
            idx = clean.find('letter')
            if idx > 0:
                length = clean[idx - 1]
        except Exception:
            pass

        await CaptchaManager.send_captcha(
            bot_name=client.bot_name,
            user=client.user,
            token_hash=client.token_hash,
            captcha_type='image',
            message_url=message.jump_url,
            data={'render_type': 'image_input', 'image_url': image_url, 'length': length},
            expires_in=600,
        )

    @staticmethod
    async def handle_hcaptcha(client, message):
        client.logger.warning('hCaptcha detected')
        await CaptchaManager.send_captcha(
            bot_name=client.bot_name,
            user=client.user,
            token_hash=client.token_hash,
            captcha_type='hcaptcha',
            message_url=message.jump_url,
            data={
                'render_type': 'widget',
                'widget_provider': 'hcaptcha',
                'sitekey': 'a6a1d5ce-612d-472d-8e37-7601408fbc09',
            },
            expires_in=600,
        )

    @staticmethod
    async def mark_solved(client):
        client.captcha_pending = False
        client.selfbot_running = True
        client.logger.info('Captcha solved - resuming')

    @staticmethod
    async def process_pending(client, captchas):
        solved = [c for c in captchas if c.get('status') == 'solved_pending' and c.get('answer')]
        if not solved:
            return

        for captcha in solved:
            ok = await CaptchaHandler.handle_web_solve(client, captcha, captcha.get('answer'))
            if ok:
                CaptchaStore.remove(client.bot_name, captcha['id'])

    @staticmethod
    async def handle_web_solve(client, captcha, answer=None):
        captcha_type = captcha.get('type', 'unknown')

        if captcha_type == 'image' and answer:
            try:
                if client.owo_bot and client.owo_bot.dm_channel:
                    await asyncio.wait_for(client.owo_bot.dm_channel.send(answer), timeout=10)
                else:
                    await client.owo_bot.create_dm()
                    await asyncio.wait_for(client.owo_bot.dm_channel.send(answer), timeout=10)
                client.logger.info('Sent image captcha answer')
                return True
            except asyncio.TimeoutError:
                client.logger.error('Timeout sending image captcha answer')
            except Exception:
                client.logger.exception('Failed to send image captcha answer')
            return False

        if captcha_type == 'hcaptcha' and answer:
            client.logger.info('hCaptcha token received, attempting to verify')
            solver = CaptchaSolver(client._token, client.owo_bot.id)
            oauth_session = await solver.get_oauth()

            if not oauth_session:
                client.logger.error('OAuth failed, resetting captcha page')
                await solver.reset_hcaptcha()
                return False

            try:
                success = await solver.verify_captcha(oauth_session, answer)
            finally:
                await oauth_session.close()

            if success:
                client.logger.info('hCaptcha verified via owobot.com')
                return True

            client.logger.error('hCaptcha verification failed, resetting')
            await solver.reset_hcaptcha()
            return False

        client.logger.error(f'Unsupported captcha solve payload: type={captcha_type}, has_answer={bool(answer)}')
        return False

    @staticmethod
    async def handle_web_delete(client, captcha):
        client.captcha_pending = False
        client.selfbot_running = True
        client.logger.info('Captcha cleared manually - resuming')
        return True
