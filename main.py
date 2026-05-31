from modules.utils.logger import setup_logging, get_logger
from modules.owo.migration import migrate_owo_data
from bot import BotManager
from app import set_bot_manager, run_server

def main():
    setup_logging()
    logger = get_logger('main')
    logger.info('Initializing...')
    migrate_owo_data()

    bot_manager = BotManager()
    set_bot_manager(bot_manager)

    try: run_server(host = '0.0.0.0', port = 2010)
    except KeyboardInterrupt: logger.info('Shutting down...')
    except Exception: logger.exception('Server error')
    finally: bot_manager.stop()

if __name__ == '__main__': main()
