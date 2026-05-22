"""
Bot Manager - manages lifecycle of all bot types.
Designed for extensibility: add new bot types (karuta, etc.) easily.
"""

import asyncio
import threading

from modules.utils.logger import get_logger
from modules.utils.constants import CONFIGS_FILE, TOKENS_FILE, CACHES_FILE

logger = get_logger('bot')

class BotManager:
    """Manages all bot client lifecycles."""

    def __init__(self):
        self._running = False
        self._loop = None
        self._thread = None
        self._clients = []  # List of all OWOClient instances
        self._tasks = []

    def is_running(self):
        return self._running

    def start(self):
        """Start all bots. Re-reads config and tokens from disk."""
        if self._running:
            return

        self._running = True
        self._clients = []
        self._tasks = []

        # Create a new event loop in a background thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        # Schedule bot startup in the loop
        asyncio.run_coroutine_threadsafe(self._start_bots(), self._loop)

    def stop(self):
        """Stop all bots and clean up."""
        if not self._running:
            return

        self._running = False

        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._stop_bots(), self._loop)
            try:
                future.result(timeout=20)
            except Exception:
                logger.exception('Error during shutdown')
            
            # Allow loop to finish pending callbacks
            def _stop_loop():
                self._loop.stop()
            self._loop.call_soon_threadsafe(_stop_loop)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)

        self._clients.clear()
        self._tasks.clear()
        self._loop = None
        self._thread = None
        logger.info('All bots stopped and resources released')

    def _run_loop(self):
        """Run the asyncio event loop in a thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _start_bots(self):
        """Initialize and start all bot clients."""
        import json

        try:
            with open(CONFIGS_FILE, 'r', encoding='utf-8') as f:
                configs = json.load(f)
        except Exception:
            logger.exception('Failed to load configs.json')
            return

        try:
            with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
                tokens = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception:
            logger.exception('Failed to load tokens.txt')
            return

        if not tokens:
            logger.warning('No tokens found in tokens.txt')
            return

        # Check which bots are configured
        if 'owo' in configs:
            await self._start_owo(tokens, configs['owo'])

    async def _start_owo(self, tokens, owo_config):
        """Start OWO bot clients for all tokens."""
        from modules.owo.client import OWOClient

        # Load caches to check pending captchas
        caches = self._load_caches()
        pending_captchas = {
            c['user_id'] for c in caches.get('captchas', [])
            if c.get('bot') == 'owo'
        }

        for i, token in enumerate(tokens):
            try:
                client = OWOClient(
                    clients=self._clients,
                    token=token,
                    config=owo_config,
                    pending_captchas=pending_captchas,
                )
                self._clients.append(client)

                if i > 0:
                    await asyncio.sleep(2 + i * 0.5)

                task = asyncio.create_task(
                    self._run_client(client, token),
                    name=f'owo-client-{i}',
                )
                self._tasks.append(task)
                logger.info(f'Initializing OWO client {i + 1}/{len(tokens)}...')
            except Exception:
                logger.exception(f'Failed to init client {i + 1}')

    async def _run_client(self, client, token):
        """Run a single discord client with error handling."""
        try:
            await client.start(token)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception('Client error')
        finally:
            if not client.is_closed():
                try:
                    await client.close()
                except Exception:
                    pass

    async def _stop_bots(self):
        """Gracefully stop all running clients."""
        # Stop task managers
        for client in self._clients:
            if hasattr(client, 'task_manager') and client.task_manager:
                await client.task_manager.stop()

        # Close clients (which closes aiohttp/curl_cffi sessions)
        for client in self._clients:
            if not client.is_closed():
                try:
                    await client.close()
                except Exception:
                    logger.exception('Error closing client')

        # Cancel our custom run_client tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Cancel all remaining tasks in the loop to prevent "Task was destroyed"
        pending = [t for t in asyncio.all_tasks(self._loop) if t is not asyncio.current_task(self._loop)]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    def _load_caches(self):
        """Load caches.json."""
        import json
        try:
            with open(CACHES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'captchas': []}

    def handle_captcha_solved(self, captcha, answer=None):
        """Handle captcha solved from web UI."""
        user_id = str(captcha.get('user_id', ''))
        bot_type = captcha.get('bot', 'owo')

        for client in self._clients:
            if not hasattr(client, 'user') or client.user is None:
                continue
            if str(client.user.id) == user_id:
                if bot_type == 'owo' and hasattr(client, 'captcha_handler'):
                    if self._loop and self._loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            client.captcha_handler.on_web_solve(captcha, answer),
                            self._loop,
                        )
                break

    def handle_captcha_deleted(self, captcha):
        """Handle captcha deleted (solved externally)."""
        user_id = str(captcha.get('user_id', ''))
        bot_type = captcha.get('bot', 'owo')

        for client in self._clients:
            if not hasattr(client, 'user') or client.user is None:
                continue
            if str(client.user.id) == user_id:
                if bot_type == 'owo' and hasattr(client, 'captcha_handler'):
                    if self._loop and self._loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            client.captcha_handler.on_web_delete(captcha),
                            self._loop,
                        )
                break