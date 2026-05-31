import json
import os
import time
import socket

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO

from modules.utils.logger import get_ws_handler, get_logger
from modules.core.data_store import read_text, write_text, validate_json_text
from modules.utils.captcha_store import CaptchaStore

logger = get_logger('app')

app = Flask(__name__)

app.config['SECRET_KEY'] = "Phamdat Selfbot"
socketio = SocketIO(app, cors_allowed_origins = '*', async_mode = 'threading')

get_ws_handler().set_socketio(socketio)

bot_manager = None
_start_time = None

def set_bot_manager(bm):
    global bot_manager
    bot_manager = bm

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/')
def page_dashboard():
    return render_template('dashboard.html')

@app.route('/captcha')
def page_captcha():
    return render_template('captcha.html')

@app.route('/data')
def page_data():
    return render_template('data.html')

@app.route('/api/status')
def api_status():
    global _start_time
    running = bot_manager.is_running() if bot_manager else False
    bots = bot_manager.status() if bot_manager else {}
    return jsonify({'running': running, 'start_time': _start_time if running else None, 'bots': bots})

@app.route('/api/start', methods = ['POST'])
def api_start():
    global _start_time
    if not bot_manager: return jsonify({'ok': False, 'error': 'Bot manager not initialized'}), 500
    if bot_manager.is_running(): return jsonify({'ok': False, 'error': 'Already running'})
    try:
        bot_manager.start()
        _start_time = time.time()
        logger.info('Bot started via web')
        return jsonify({'ok': True})
    except Exception:
        logger.exception('Failed to start')
        return jsonify({'ok': False, 'error': 'Failed to start'}), 500

@app.route('/api/stop', methods = ['POST'])
def api_stop():
    global _start_time
    if not bot_manager: return jsonify({'ok': False, 'error': 'Bot manager not initialized'}), 500
    try:
        bot_manager.stop()
        _start_time = None
        logger.info('Bot stopped via web')
        return jsonify({'ok': True})
    except Exception:
        logger.exception('Failed to stop')
        return jsonify({'ok': False, 'error': 'Failed to stop'}), 500

@app.route('/api/captcha/list')
def api_captcha_list():
    bot = request.args.get('bot')
    return jsonify(CaptchaStore.list(bot))

def _process_captcha_action(action):
    payload = request.get_json() or {}
    c_id = payload.get('id')

    bot = payload.get('bot') or None
    captchas = CaptchaStore.list(bot)

    captcha = next((c for c in captchas if c['id'] == c_id), None)
    if not captcha: return jsonify({'ok': False, 'error': 'Captcha not found'}), 404

    bot = captcha.get('bot', 'owo')
    status = captcha.get('status', 'pending')
    removed = False

    if action == 'solve':
        answer = payload.get('answer')
        if bot_manager and bot_manager.is_running():
            CaptchaStore.update(bot, c_id, {'status': 'processing', 'answer': answer})
            future = bot_manager.handle_captcha_solved(captcha, answer)
            if future:
                try:
                    ok = bool(future.result(timeout=45))
                except Exception:
                    logger.exception(f'Captcha solve failed for {bot}:{c_id}')
                    ok = False
                if ok:
                    CaptchaStore.remove(bot, c_id)
                    removed = True
                    status = 'solved'
                    logger.info(f"Captcha solved for {captcha['display_name']}")
                else:
                    CaptchaStore.update(bot, c_id, {'status': 'failed', 'answer': answer})
                    return jsonify({'ok': False, 'error': 'Captcha solve failed'}), 500
            else:
                CaptchaStore.update(bot, c_id, {'status': 'solved_pending', 'answer': answer})
                status = 'solved_pending'
        else:
            CaptchaStore.update(bot, c_id, {'status': 'solved_pending', 'answer': answer})
            status = 'solved_pending'
            logger.info(f"Captcha answer saved for {captcha['display_name']} (bot offline)")
            if bot_manager and not bot_manager.is_running():
                try:
                    global _start_time
                    bot_manager.start()
                    _start_time = time.time()
                    logger.info("Bot auto-started after captcha solve")
                except Exception:
                    logger.exception("Failed to auto-start bot after captcha solve")
    else:
        if bot_manager and bot_manager.is_running():
            future = bot_manager.handle_captcha_deleted(captcha)
            if future:
                try: future.result(timeout=10)
                except Exception: logger.exception(f'Captcha delete handler failed for {bot}:{c_id}')
        CaptchaStore.remove(bot, c_id)
        removed = True
        status = 'deleted'
        logger.info(f"Captcha deleted for {captcha['display_name']}")

    socketio.emit('captcha_update', {'id': c_id, 'bot': bot, 'action': action}, namespace = '/')
    socketio.emit('captcha_count', {'count': CaptchaStore.count()}, namespace = '/')
    return jsonify({'ok': True, 'status': status, 'removed': removed})

@app.route('/api/captcha/solve', methods = ['POST'])
def api_captcha_solve(): return _process_captcha_action('solve')

@app.route('/api/captcha/delete', methods = ['POST'])
def api_captcha_delete(): return _process_captcha_action('delete')

@app.route('/api/data/files')
def api_data_files():
    try:
        return jsonify(sorted([f for f in os.listdir('data') if os.path.isfile(os.path.join('data', f))]))
    except Exception:
        logger.exception('Failed to list files in folder data')
        return jsonify([])

@app.route('/api/data/read')
def api_data_read():
    filename = request.args.get('file', '')

    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'ok': False, 'error': 'Invalid filename'}), 400

    filepath = f"data/{filename}"
    if not os.path.isfile(filepath): return jsonify({'ok': False, 'error': 'File not found'}), 404

    try:
        content = read_text(filepath)
        return jsonify({'ok': True, 'content': content, 'filename': filename})
    except Exception:
        logger.exception(f'Failed to read file: {filename}')
        return jsonify({'ok': False, 'error': 'Failed to read file'}), 500

@app.route('/api/data/write', methods=['POST'])
def api_data_write():
    payload = request.get_json()
    if not payload: return jsonify({'ok': False, 'error': 'Empty payload'}), 400

    filename = payload.get('file', '')
    content = payload.get('content', '')

    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'ok': False, 'error': 'Invalid filename'}), 400

    filepath = f"data/{filename}"
    if not os.path.isfile(filepath): return jsonify({'ok': False, 'error': 'File not found'}), 404

    try:
        if filename.endswith('.json'):
            validate_json_text(content)
        write_text(filepath, content)
        logger.info(f'File saved via Web: {filename}')
        return jsonify({'ok': True})
    except json.JSONDecodeError as e:
        return jsonify({'ok': False, 'error': f'Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}'}), 400
    except Exception:
        logger.exception(f'Failed to write file: {filename}')
        return jsonify({'ok': False, 'error': 'Failed to write file'}), 500

@app.route('/api/logs')
def api_logs():
    handler = get_ws_handler()
    return jsonify(handler.get_buffer())

@socketio.on('connect')
def handle_connect():
    socketio.emit('captcha_count', {'count': CaptchaStore.count()}, room = request.sid, namespace = '/')

def run_server(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    logger.info(f'Website: http://{ip}:{port}')
    socketio.run(app, host = host, port = port, debug = False, use_reloader = False, allow_unsafe_werkzeug = True)
