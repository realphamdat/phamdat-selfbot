import asyncio
import threading

from modules.utils.config import deep_merge
from modules.utils.data_store import read_json
from modules.utils import cache
from modules.utils.logger import get_logger
from modules.bots.owo.client import OWOClient
from modules.bots.owo.defaults import OWO_DEFAULT_CONFIG
from modules.bots.owo.captcha import Captcha

logger = get_logger('owo')

loop = None
thread = None
clients = []
clients_by_user = {}


def status():
    accounts = read_json('data/owo.json', {}) or {}
    return {
        'running': any(c.macro_enabled for c in clients),
        'accounts': len(clients),
        'configured': len(accounts),
        'captchas': cache.count('owo'),
    }


def boot():
    global loop, thread
    if loop:
        return

    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=run_loop, name='owo_runtime', daemon=True)
    thread.start()
    asyncio.run_coroutine_threadsafe(start_accounts(), loop)


def run_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()


async def start_accounts():
    accounts = load_accounts()
    if not accounts:
        logger.warning('No OWO accounts configured')
        return

    total = len(accounts)
    for index, (token, config) in enumerate(accounts.items(), start=1):
        try:
            client = OWOClient(token=token, config=config, clients=clients)
            clients.append(client)
            if index > 1:
                await asyncio.sleep(2)
            asyncio.create_task(run_client(client, token), name=f'owo_account_{index}')
            logger.info(f'Initializing OWO account {index}/{total}')
        except Exception:
            logger.exception(f'Failed to initialize OWO account {index}/{total}')


def load_accounts():
    raw_accounts = read_json('data/owo.json', {}) or {}
    return {
        token: deep_merge(OWO_DEFAULT_CONFIG, config)
        for token, config in raw_accounts.items()
        if token
    }


async def run_client(client, token):
    try:
        await client.start(token)
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception('OWO client error')
    finally:
        if not client.is_closed():
            try:
                await client.close()
            except Exception:
                logger.exception('Failed to close OWO client')


def start_macro():
    if not loop or not loop.is_running():
        return False
    for client in clients:
        client.macro_enabled = True
    logger.info('OWO macro started')
    return True


def stop_macro():
    for client in clients:
        client.macro_enabled = False
        client.reset_quest_state()
    logger.info('OWO macro stopped')


def shutdown():
    global loop, thread
    if not loop:
        return

    for client in clients:
        client.macro_enabled = False

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(stop_accounts(), loop)
        try:
            future.result(timeout=20)
        except Exception:
            logger.exception('OWO shutdown failed')
        loop.call_soon_threadsafe(loop.stop)

    if thread and thread.is_alive():
        thread.join(timeout=10)

    clients.clear()
    clients_by_user.clear()
    loop = None
    thread = None


async def stop_accounts():
    for client in clients:
        try:
            await client.stop_runtime()
        except Exception:
            logger.exception('Failed to stop OWO account runtime')


def solve_captcha(captcha, answer=None):
    if not loop or not loop.is_running():
        return None
    client = find_client(captcha)
    if not client:
        return None
    return asyncio.run_coroutine_threadsafe(Captcha.handle_web_solve(client, captcha, answer), loop)


def delete_captcha(captcha):
    if not loop or not loop.is_running():
        return None
    client = find_client(captcha)
    if not client:
        return None
    return asyncio.run_coroutine_threadsafe(Captcha.handle_web_delete(client), loop)


def find_client(captcha):
    user_id = str(captcha.get('user_id', ''))
    if user_id in clients_by_user:
        return clients_by_user[user_id]

    for client in clients:
        user = getattr(client, 'user', None)
        if user and str(user.id) == user_id:
            clients_by_user[user_id] = client
            return client


def reload():
    if not loop or not loop.is_running():
        return

    future = asyncio.run_coroutine_threadsafe(reload_accounts(), loop)
    try:
        future.result(timeout=30)
    except Exception:
        logger.exception('OWO reload failed')


async def reload_accounts():
    for client in clients:
        try:
            await client.stop_runtime()
        except Exception:
            logger.exception('Failed to stop OWO account during reload')

    clients.clear()
    clients_by_user.clear()

    await start_accounts()