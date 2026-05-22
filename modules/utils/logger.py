"""
Centralized logging system.
Captures all output and sends to both console and web terminal via SocketIO.
"""

import logging
import sys
import time
from collections import deque

class WebSocketHandler(logging.Handler):
    """Stores log entries and emits them via SocketIO."""

    def __init__(self, max_buffer=100):
        super().__init__()
        self.buffer = deque(maxlen=max_buffer)
        self.socketio = None

    def set_socketio(self, sio):
        self.socketio = sio

    def emit(self, record):
        try:
            entry = {
                'time': time.strftime('%H:%M:%S', time.localtime(record.created)),
                'level': record.levelname,
                'name': record.name,
                'message': self.format(record),
            }
            self.buffer.append(entry)
            if self.socketio:
                self.socketio.emit('log', entry, namespace='/')
        except Exception:
            self.handleError(record)

    def get_buffer(self):
        return list(self.buffer)

# Singleton handler
_ws_handler = None

def get_ws_handler():
    global _ws_handler
    if _ws_handler is None:
        _ws_handler = WebSocketHandler()
        _ws_handler.setFormatter(logging.Formatter('%(message)s'))
    return _ws_handler

def setup_logging():
    """Configure root logger for perfectly synced console + web terminal output."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Clear existing handlers
    for h in list(root.handlers):
        root.removeHandler(h)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%H:%M:%S',
    ))

    # WebSocket handler
    handler = get_ws_handler()
    handler.setLevel(logging.INFO)

    root.addHandler(console)
    root.addHandler(handler)

    # Suppress noisy Flask/Werkzeug HTTP request logs from reaching web terminal
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    werkzeug_logger.propagate = True
    for h in list(werkzeug_logger.handlers):
        werkzeug_logger.removeHandler(h)

    engineio_logger = logging.getLogger('engineio')
    engineio_logger.setLevel(logging.WARNING)
    engineio_logger.propagate = True

    socketio_logger = logging.getLogger('socketio')
    socketio_logger.setLevel(logging.WARNING)
    socketio_logger.propagate = True

    return handler

def get_logger(name):
    """Get a named logger."""
    return logging.getLogger(name)