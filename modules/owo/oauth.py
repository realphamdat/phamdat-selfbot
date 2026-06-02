import aiohttp
import asyncio

from modules.utils.logger import get_logger
from modules.utils.oauth import DiscordOAuth

logger = get_logger('captcha')

class CaptchaSolver:
    REDIRECT_URI = 'https%3A%2F%2Fowobot.com%2Fapi%2Fauth%2Fdiscord%2Fredirect'
    SCOPE = 'identify%20guilds%20email%20guilds.members.read'
    VERIFY_URL = 'https://owobot.com/api/captcha/verify'

    def __init__(self, user_token, bot_id):
        self.user_token = user_token
        self.bot_id = bot_id

    async def get_oauth(self):
        referer = (
            'https://discord.com/oauth2/authorize'
            f'?response_type=code&redirect_uri={self.REDIRECT_URI}&scope={self.SCOPE}&client_id={self.bot_id}'
        )
        location = await DiscordOAuth.authorize(
            token=self.user_token,
            client_id=self.bot_id,
            redirect_uri=self.REDIRECT_URI,
            scope=self.SCOPE,
            referer=referer,
        )
        if not location:
            return None
        return await DiscordOAuth.submit_redirect(location, host='owobot.com')

    @staticmethod
    async def verify_captcha(oauth_session, captcha_token, retries=2):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US;en;q=0.8',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://owobot.com',
            'Referer': 'https://owobot.com/captcha',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': DiscordOAuth.DEFAULT_HEADERS['User-Agent'],
        }
        for attempt in range(retries):
            success = await DiscordOAuth.post_json(oauth_session, CaptchaSolver.VERIFY_URL, {'token': captcha_token}, headers)
            if success:
                return True
            if attempt < retries - 1:
                await asyncio.sleep(1 + attempt)
        return False

    @staticmethod
    async def reset_hcaptcha():
        headers = {'User-Agent': DiscordOAuth.DEFAULT_HEADERS['User-Agent']}
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get('https://owobot.com/captcha', headers=headers) as resp:
                    logger.info(f'reset captcha page: {resp.status}')
        except Exception:
            logger.exception('Failed to reset hcaptcha')
