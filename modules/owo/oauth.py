"""
OAuth-based Captcha Solver for OWO bot (hCaptcha).
Uses aiohttp to simulate Discord OAuth login and submit the token to owobot.com.

Copied from reference: TÀI LIỆU THAM KHẢO/dự án cũ/oauth.py
"""

import aiohttp
from modules.utils.logger import get_logger
from modules.owo.constants import OWO_VERIFY_URL, OWO_CAPTCHA_PAGE

logger = get_logger('captcha')

class CaptchaSolver:
    """Async OAuth + captcha verification for owobot."""

    def __init__(self, user_token: str, bot_id: int):
        self.user_token = user_token
        self.bot_id = bot_id

    async def submit_oauth(self, res: aiohttp.ClientResponse) -> Optional[aiohttp.ClientSession]:
        loc = (await res.json()).get("location")
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.5",
            "connection": "keep-alive",
            "host": "owobot.com",
            "referer": "https://discord.com/",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "cross-site",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
        }
        session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar())
        try:
            async with session.get(loc, headers=headers, allow_redirects=False) as resp:
                if resp.status in (302, 307):
                    return session
                else:
                    logger.error(f"submit_oauth failed: {resp.status}")
                    await session.close()
                    return None
        except Exception:
            logger.exception('Failed to submit oauth')
            await session.close()
            return None

    async def get_oauth(self) -> Optional[aiohttp.ClientSession]:
        url = (
            f"https://discord.com/api/v9/oauth2/authorize"
            f"?response_type=code"
            f"&redirect_uri=https%3A%2F%2Fowobot.com%2Fapi%2Fauth%2Fdiscord%2Fredirect"
            f"&scope=identify%20guilds%20email%20guilds.members.read"
            f"&client_id={self.bot_id}"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "Authorization": self.user_token,
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRmlyZWZveCIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQ7IHJ2OjEwOS4wKSBHZWNrby8yMDEwMDEwMSBGaXJlZm94LzExMS4wIiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTExLjAiLCJvc192ZXJzaW9uIjoiMTAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MTg3NTk5LCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ==",
            "X-Debug-Options": "bugReporterEnabled",
            "Origin": "https://discord.com",
            "Connection": "keep-alive",
            "Referer": f"https://discord.com//oauth2/authorize?response_type=code&redirect_uri=https%3A%2F%2Fowobot.com%2Fapi%2Fauth%2Fdiscord%2Fredirect&scope=identify%20guilds%20email%20guilds.members.read&client_id={self.bot_id}",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"permissions": "0", "authorize": True}) as resp:
                if resp.status == 200:
                    return await self.submit_oauth(resp)
                else:
                    logger.error(f"get_oauth failed: {resp.status} {await resp.text()}")
                    return None

    async def verify_captcha(self, oauth_session: aiohttp.ClientSession, captcha_token: str) -> bool:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US;en;q=0.8",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://owobot.com",
            "Referer": OWO_CAPTCHA_PAGE,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
        }
        try:
            async with oauth_session.post(OWO_VERIFY_URL, headers=headers, json={"token": captcha_token}) as resp:
                if resp.status == 200:
                    return True
                else:
                    logger.error(f"verify failed: {resp.status} {await resp.text()}")
                    return False
        except Exception:
            logger.exception('Failed to verify captcha API')
            return False

    async def reset_hcaptcha(self) -> None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(OWO_CAPTCHA_PAGE, headers=headers) as resp:
                    logger.info(f"reset captcha page: {resp.status}")
        except Exception:
            logger.exception('Failed to reset hcaptcha')