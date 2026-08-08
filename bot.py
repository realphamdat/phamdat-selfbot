import os
import time
import threading

from modules.utils.logger import get_logger
from modules.bots.owo import runtime as owo
from modules.extensions.quest import runtime as quest
from modules.extensions.chat import runtime as chat
from modules.extensions.voice import runtime as voice

logger = get_logger('bot')

BOTS = {'owo': owo}
EXTENSIONS = {'quest': quest, 'chat': chat, 'voice': voice}

WATCH_FILES = {'owo.json'}
_file_mtimes = {}
_running = False
_lock = threading.Lock()


class BotManager:
    def __init__(self):
        self._start_time = None

    def boot(self):
        for bot in BOTS.values():
            bot.boot()
        _init_mtimes()
        threading.Thread(target=_watch_files, name='file_watcher', daemon=True).start()

    def start(self):
        global _running
        with _lock:
            if _running:
                return
            for bot in BOTS.values():
                bot.start_macro()
            for ext in EXTENSIONS.values():
                ext.start()
            _running = True
            self._start_time = time.time()
        logger.info('Started')

    def stop(self):
        global _running
        with _lock:
            if not _running:
                return
            for bot in BOTS.values():
                bot.stop_macro()
            for ext in EXTENSIONS.values():
                ext.stop()
            _running = False
            self._start_time = None
        logger.info('Stopped')

    def shutdown(self):
        for bot in BOTS.values():
            bot.shutdown()
        for ext in EXTENSIONS.values():
            ext.stop()

    def is_running(self):
        return _running

    def start_time(self):
        return self._start_time

    def status(self):
        return {name: bot.status() for name, bot in BOTS.items() if hasattr(bot, 'status')}

    def solve_captcha(self, captcha, answer=None):
        bot = BOTS.get(captcha.get('bot'))
        if bot and hasattr(bot, 'solve_captcha'):
            return bot.solve_captcha(captcha, answer)
        return None

    def delete_captcha(self, captcha):
        bot = BOTS.get(captcha.get('bot'))
        if bot and hasattr(bot, 'delete_captcha'):
            return bot.delete_captcha(captcha)
        return None


def _init_mtimes():
    _file_mtimes.clear()
    for filename in WATCH_FILES:
        path = os.path.join('data', filename)
        if os.path.isfile(path):
            _file_mtimes[filename] = os.path.getmtime(path)


def _watch_files():
    while True:
        for filename in WATCH_FILES:
            path = os.path.join('data', filename)
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            if filename in _file_mtimes and _file_mtimes[filename] != mtime:
                _file_mtimes[filename] = mtime
                with _lock:
                    if not _running:
                        logger.info(f'Data file changed: {filename}, reloading')
                        for bot in BOTS.values():
                            if hasattr(bot, 'reload'):
                                bot.reload()
                    else:
                        logger.info(f'Data file changed: {filename} (running, skip reload)')
        time.sleep(2)
