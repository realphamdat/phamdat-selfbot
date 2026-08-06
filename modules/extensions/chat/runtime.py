import threading

from modules.extensions.chat import main

_thread = None


def start():
    global _thread
    if main.running:
        return
    main.running = True
    _thread = threading.Thread(target=main.main, name='chat', daemon=True)
    _thread.start()


def stop():
    main.running = False
    if _thread and _thread.is_alive():
        _thread.join(timeout=15)