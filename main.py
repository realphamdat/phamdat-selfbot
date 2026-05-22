"""
Entry Point
Initializes logging, bot manager, and starts the web server.
"""

import json

from modules.utils.logger import setup_logging, get_logger
from modules.utils.constants import SETTINGS_FILE
from modules.bot import BotManager
from modules.web.app import set_bot_manager, run_server

def load_settings():
    """Load web server settings."""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'port': 8080}

def main():
    # Setup logging
    setup_logging()
    logger = get_logger('main')
    logger.info('Initializing...')

    # Load settings
    settings = load_settings()
    port = settings['port']

    # Create bot manager
    bot_manager = BotManager()
    set_bot_manager(bot_manager)

    logger.info(f'Starting web server on port {port}')

    # Start Flask-SocketIO server (blocking)
    try:
        run_server(host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        logger.info('Shutting down...')
        bot_manager.stop()
    except Exception:
        logger.exception('Server error')
        bot_manager.stop()

if __name__ == '__main__':
    main()