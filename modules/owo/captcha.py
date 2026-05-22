"""
Captcha detection and web notification.
Handles: image captcha, hcaptcha, unknown captcha.
Sends captcha data to web dashboard for manual solving.
"""

import re

from modules.utils.logger import get_logger
from modules.owo.constants import OWO_SITEKEY

logger = get_logger('captcha')

class CaptchaHandler:
    """Detects OWO captchas and sends them to the web dashboard for solving."""

    def __init__(self, client):
        self.client = client

    async def _get_image_height(self, attachment):
        """Get image height, prioritizing metadata, fallback to PIL."""
        if attachment.height is not None:
            return attachment.height
        try:
            import aiohttp
            import io
            from PIL import Image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).height
        except Exception:
            self.client.logger.exception('Failed to get image height fallback')
            return 0

    async def detect(self, message):
        """Detect captcha from OWO bot messages."""
        if not self.client.owo_bot:
            return
        
        content = message.content
        is_owo = message.author.id == self.client.owo_bot.id

        # Already has pending captcha and got thumbs up = solved
        if self.client.captcha_pending and is_owo:
            if (hasattr(self.client.owo_bot, 'dm_channel')
                    and self.client.owo_bot.dm_channel
                    and message.channel.id == self.client.owo_bot.dm_channel.id
                    and '👍' in content):
                await self._on_solved()
                return

        # Skip if captcha already pending
        if self.client.captcha_pending:
            return

        if not is_owo:
            return

        clean = re.sub(r'[^0-9a-zA-Z]', '', content)

        # 1) Image captcha: DM or channel mention with attachment
        is_image = (
            (message.attachments and await self._get_image_height(message.attachments[0]) <= 100)
            and (
            (hasattr(self.client.owo_bot, 'dm_channel')
             and self.client.owo_bot.dm_channel
             and message.channel.id == self.client.owo_bot.dm_channel.id)
            or f'**⚠️ | {self.client.user.name}**' in content
            )
        )

        # 2) hCaptcha: mention with verify button
        is_hcaptcha = (
            f'<@{self.client.user.id}>' in content
            and hasattr(message, 'components') and message.components
            and any(
                'verify' in getattr(child, 'label', '').lower()
                for row in message.components
                for child in getattr(row, 'children', [])
            )
        )

        if not (is_image or is_hcaptcha):
            return

        # Set captcha pending
        self.client.captcha_pending = True
        self.client.selfbot_running = False

        if is_image:
            await self._handle_image_captcha(message, clean)
        elif is_hcaptcha:
            await self._handle_hcaptcha(message)

    async def _handle_image_captcha(self, message, clean):
        """Process image captcha detection."""
        self.client.logger.warning('Image captcha detected')

        image_url = message.attachments[0].url if message.attachments else None

        # Try to extract length
        length = '?'
        try:
            idx = clean.find('letter')
            if idx > 0:
                length = clean[idx - 1]
        except Exception:
            pass

        from modules.utils.captcha_manager import CaptchaManager
        await CaptchaManager.send_captcha(
            bot_name='owo',
            user=self.client.user,
            captcha_type='image',
            message_url=message.jump_url,
            data={
                'render_type': 'image_input',
                'image_url': image_url,
                'length': length
            },
            expires_in=600
        )

    async def _handle_hcaptcha(self, message):
        """Process hCaptcha detection."""
        self.client.logger.warning('hCaptcha detected')

        from modules.utils.captcha_manager import CaptchaManager
        await CaptchaManager.send_captcha(
            bot_name='owo',
            user=self.client.user,
            captcha_type='hcaptcha',
            message_url=message.jump_url,
            data={
                'render_type': 'widget',
                'widget_provider': 'hcaptcha',
                'sitekey': OWO_SITEKEY,
            },
            expires_in=600
        )

    async def _on_solved(self):
        """Called when OWO confirms captcha is solved (thumbs up)."""
        self.client.captcha_pending = False
        self.client.selfbot_running = True
        self.client.logger.info('Captcha solved - resuming')

    async def on_web_solve(self, captcha, answer=None):
        """Called from BotManager when web UI solves a captcha."""
        captcha_type = captcha.get('type', 'unknown')

        if captcha_type == 'image' and answer:
            # Send answer to OWO bot DM
            try:
                if self.client.owo_bot and self.client.owo_bot.dm_channel:
                    await self.client.owo_bot.dm_channel.send(answer)
                    self.client.logger.info(f'Sent captcha answer: {answer}')
            except Exception:
                self.client.logger.exception('Failed to send captcha answer')
        elif captcha_type == 'hcaptcha' and answer:
            self.client.logger.info('hCaptcha token received, attempting to verify...')
            from modules.owo.oauth import CaptchaSolver
            from modules.owo.constants import OWO_BOT_ID
            solver = CaptchaSolver(self.client._token, OWO_BOT_ID)

            oauth_session = await solver.get_oauth()
            if not oauth_session:
                self.client.logger.error('OAuth failed, resetting captcha page...')
                await solver.reset_hcaptcha()
                return

            success = await solver.verify_captcha(oauth_session, answer)
            await oauth_session.close()

            if success:
                self.client.logger.info('hCaptcha successfully verified via owobot.com')
            else:
                self.client.logger.error('hCaptcha verification failed, resetting...')
                await solver.reset_hcaptcha()

    async def on_web_delete(self, captcha):
        """Called when captcha is deleted from web (solved externally)."""
        self.client.captcha_pending = False
        self.client.selfbot_running = True
        self.client.logger.info('Captcha cleared (manual) - resuming')
