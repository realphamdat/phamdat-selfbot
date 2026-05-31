import asyncio
import hashlib
import threading

from modules.core.config import deep_merge
from modules.core.data_store import read_json
from modules.core.registry import BotRegistry
from modules.owo.client import OWOClient
from modules.owo.defaults import OWO_DEFAULT_CONFIG
from modules.owo.migration import migrate_owo_data
from modules.utils.captcha_store import CaptchaStore
from modules.utils.logger import get_logger
from modules.utils.extension_manager import ExtensionManager

logger = get_logger('bot')

def token_hash(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()[:16]

class BotManager:
    def __init__(self):
        self._running = False
        self._loop = None
        self._thread = None
        self._clients = []
        self._tasks = []
        self._clients_by_bot = {}
        self._clients_by_user = {}
        self._clients_by_token = {}
        self.registry = self._build_registry()
        self.extension_manager = ExtensionManager()

    @staticmethod
    def _build_registry():
        registry = BotRegistry()
        registry.register('owo', OWOClient, OWO_DEFAULT_CONFIG)
        return registry

    def is_running(self):
        return self._running

    def status(self):
        bots = {}
        for name in self.registry.names():
            clients = self._clients_by_bot.get(name, [])
            accounts = read_json(f'data/{name}.json', {}) or {}
            bots[name] = {
                'running_accounts': len(clients),
                'configured_accounts': len(accounts),
                'captchas': CaptchaStore.count(name),
            }
        return bots

    def start(self):
        if self._running:
            return

        self._running = True
        self._clear_runtime()
        migrate_owo_data()
        CaptchaStore.normalize()

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        asyncio.run_coroutine_threadsafe(self._start_bots(), self._loop)

        self.extension_manager.discover_and_load()
        self.extension_manager.start_all()

    def stop(self):
        if not self._running:
            return

        self._running = False

        self.extension_manager.stop_all()

        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._stop_bots(), self._loop)
            try:
                future.result(timeout=20)
            except Exception:
                logger.exception('Error during shutdown')
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)

        self._clear_runtime()
        self._loop = None
        self._thread = None
        logger.info('All bots stopped and resources released')

    def handle_captcha_solved(self, captcha, answer=None):
        return self._captcha_action(captcha, 'handle_web_solve', answer)

    def handle_captcha_deleted(self, captcha):
        return self._captcha_action(captcha, 'handle_web_delete')

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _start_bots(self):
        for bot_name in self.registry.names():
            accounts = self._load_accounts(bot_name)
            if not accounts:
                logger.warning(f'No accounts configured for bot: {bot_name}')
                continue
            await self._start_bot_accounts(bot_name, accounts)

    def _load_accounts(self, bot_name):
        if bot_name == 'owo':
            migrate_owo_data()
        raw_accounts = read_json(f'data/{bot_name}.json', {}) or {}
        defaults = self.registry.defaults(bot_name)
        return {token: deep_merge(defaults, config) for token, config in raw_accounts.items() if token}

    async def _start_bot_accounts(self, bot_name, accounts):
        pending_captchas = CaptchaStore.list(bot_name)
        pending_by_token = {}
        pending_without_token = []

        for captcha in pending_captchas:
            status = captcha.get('status', 'pending')
            if status not in {'pending', 'solved_pending', 'failed'}:
                continue
            if captcha.get('token_hash'):
                pending_by_token.setdefault(captcha['token_hash'], []).append(captcha)
            else:
                pending_without_token.append(captcha)

        shared_clients = self._clients_by_bot.setdefault(bot_name, [])
        total = len(accounts)

        for index, (token, config) in enumerate(accounts.items(), start=1):
            try:
                thash = token_hash(token)
                client = self.registry.create_client(
                    bot_name,
                    bot_name=bot_name,
                    token=token,
                    token_hash=thash,
                    config=config,
                    shared_clients=shared_clients,
                    pending_captchas=pending_by_token.get(thash, []) + pending_without_token,
                )
                shared_clients.append(client)
                self._clients.append(client)
                self._clients_by_token[f'{bot_name}:{thash}'] = client

                if index > 1:
                    await asyncio.sleep(2)

                task = asyncio.create_task(self._run_client(client, token), name=f'{bot_name}-client-{index}')
                self._tasks.append(task)
                logger.info(f'Initializing {bot_name.upper()} client {index}/{total}...')
            except Exception:
                logger.exception(f'Failed to initialize {bot_name} client {index}/{total}')

    async def _run_client(self, client, token):
        try:
            await client.start(token)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception(f'{getattr(client, "bot_name", "bot")} client error')
        finally:
            if not client.is_closed():
                try:
                    await client.close()
                except Exception:
                    pass

    async def _stop_bots(self):
        await self._stop_task_managers()
        await self._close_all_clients()
        await self._cancel_managed_tasks()
        await self._cancel_remaining_tasks()

    async def _stop_task_managers(self):
        for client in self._clients:
            if getattr(client, 'task_manager', None):
                try:
                    await client.task_manager.stop()
                except Exception:
                    logger.exception(f'Error stopping task manager for {client}')

    async def _close_all_clients(self):
        for client in self._clients:
            if not client.is_closed():
                try:
                    await client.close()
                except Exception:
                    logger.exception(f'Error closing client for {client}')

    async def _cancel_managed_tasks(self):
        for task in self._tasks:
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _cancel_remaining_tasks(self):
        pending = [t for t in asyncio.all_tasks(self._loop) if t is not asyncio.current_task(self._loop)]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    def _captcha_action(self, captcha, method_name, answer=None):
        bot_name = captcha.get('bot', '')
        client = self._find_client(bot_name, captcha)
        if not client or not self._loop or not self._loop.is_running():
            return False

        handler = getattr(client, 'captcha_handler', None)
        if not handler or not hasattr(handler, method_name):
            return False

        coro = getattr(handler, method_name)
        args = (client, captcha, answer) if answer is not None else (client, captcha)
        future = asyncio.run_coroutine_threadsafe(coro(*args), self._loop)
        return future

    def _find_client(self, bot_name, captcha):
        token_key = f"{bot_name}:{captcha.get('token_hash', '')}"
        if token_key in self._clients_by_token:
            return self._clients_by_token[token_key]

        user_id = str(captcha.get('user_id', ''))
        user_key = f'{bot_name}:{user_id}'
        if user_key in self._clients_by_user:
            return self._clients_by_user[user_key]

        for client in self._clients_by_bot.get(bot_name, []):
            user = getattr(client, 'user', None)
            if user and str(user.id) == user_id:
                self._clients_by_user[user_key] = client
                return client

    def _clear_runtime(self):
        self._clients.clear()
        self._tasks.clear()
        self._clients_by_bot.clear()
        self._clients_by_user.clear()
        self._clients_by_token.clear()
