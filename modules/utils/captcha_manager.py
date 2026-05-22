"""
Global Captcha Dispatch System.

This module provides a unified API for any bot module (OWO, Karuta, etc.) to send
captcha challenges to the web dashboard and receive user solutions.

=============================================================================
HOW TO USE - QUICK START GUIDE FOR DEVELOPERS
=============================================================================

1. IMPORTING THE MANAGER
-----------------------------------------------------------------------------
from modules.utils.captcha_manager import CaptchaManager

2. SENDING A CAPTCHA TO THE WEB UI
-----------------------------------------------------------------------------
When your bot detects a captcha, call `CaptchaManager.send_captcha(...)`.
The magic lies in the `data` dictionary, which controls EXACTLY how the web
UI renders the captcha. You must specify a `render_type`.

Supported `render_type`s:

A) "image_input": For standard image captchas.
   data={
       "render_type": "image_input",
       "image_url": "https://discord.com/...", # URL to the captcha image
       "placeholder": "Enter the text from the image..." # Optional
   }

B) "audio": For audio captchas.
   data={
       "render_type": "audio",
       "audio_url": "https://discord.com/...", # URL to the audio file (.mp3, .wav)
       "placeholder": "Type what you hear..." # Optional
   }

C) "widget": For standard 3rd party providers like hCaptcha, reCAPTCHA, Turnstile.
   data={
       "render_type": "widget",
       "widget_provider": "hcaptcha", # or "recaptcha" or "turnstile"
       "sitekey": "a6a1d5ce-612d-472d-8e37-7601408fbc09"
   }
   -> Note: The UI will automatically load the script and render the widget!

D) "iframe": For custom captchas hosted on another website.
   data={
       "render_type": "iframe",
       "url": "https://your-custom-captcha-site.com/solve?id=123"
   }

E) "link": If the captcha site prevents iframe embedding (X-Frame-Options),
   use this to show a button that opens a new tab.
   data={
       "render_type": "link",
       "url": "https://external-site.com/solve"
   }

3. HANDLING THE SOLUTION (CALLBACKS)
-----------------------------------------------------------------------------
When the user submits the answer (or completes the widget) on the web UI,
it hits the `app.py` /api/captcha/solve endpoint. `BotManager` will then
route it to your bot's `captcha_handler.on_web_solve(captcha_dict, answer)`.
You process the answer and send it back to Discord/Web.

Example code for sending an audio captcha:
    await CaptchaManager.send_captcha(
        bot_name="mybot",
        user=self.client.user,          # discord.User object
        captcha_type="audio_challenge",
        message_url=message.jump_url,
        data={
            "render_type": "audio",
            "audio_url": "https://example.com/captcha.mp3"
        }
    )
"""

import time
import uuid
import json

from modules.utils.logger import get_logger
from modules.utils.constants import CACHES_FILE

logger = get_logger('captcha_manager')

class CaptchaManager:
    @staticmethod
    async def send_captcha(bot_name, user, captcha_type, message_url, data, expires_in=None):
        """
        Send a captcha challenge to the web dashboard.

        Args:
            bot_name (str): Identifier for the bot (e.g., 'owo', 'karuta').
            user (discord.User): The discord user object of the client that got the captcha.
            captcha_type (str): Short description (e.g., 'image', 'hcaptcha', 'audio').
            message_url (str): The jump_url to the Discord message containing the captcha.
            data (dict): Render schema dictionary (must contain 'render_type').
        """
        avatar_url = str(user.avatar.url) if user.avatar else ''
        created_at_ts = time.time()
        created_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(created_at_ts))
        expires_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(created_at_ts + expires_in)) if expires_in is not None else None

        payload = {
            'id': str(uuid.uuid4()),
            'user_id': str(user.id),
            'display_name': user.display_name,
            'username': str(user.name),
            'avatar_url': avatar_url,
            'bot': bot_name,
            'type': captcha_type,
            'data': data,
            'message_url': message_url,
            'created_at': created_at,
            'expires_at': expires_at,
        }

        try:
            # Read current caches
            try:
                with open(CACHES_FILE, 'r', encoding='utf-8') as f:
                    caches = json.load(f)
            except Exception:
                caches = {'captchas': []}

            if 'captchas' not in caches:
                caches['captchas'] = []

            # Append new captcha
            caches['captchas'].append(payload)

            # Write back
            with open(CACHES_FILE, 'w', encoding='utf-8') as f:
                json.dump(caches, f, indent=4, ensure_ascii=False)

            # Emit via SocketIO for real-time update
            from modules.web.app import socketio
            socketio.emit('captcha_new', payload, namespace='/')
            socketio.emit('captcha_count', {'count': len(caches['captchas'])}, namespace='/')

            # Send Browser Push Notification
            socketio.emit('notification', {
                'title': f'Captcha [{bot_name}] - {user.display_name}',
                'body': f'{captcha_type} captcha detected!',
                'tag': f'captcha-{user.id}',
            }, namespace='/')

            logger.warning(f'[{bot_name}] Captcha sent to web dashboard ({captcha_type}) for user {user.name}')

        except Exception:
            logger.exception('Failed to dispatch captcha to web')