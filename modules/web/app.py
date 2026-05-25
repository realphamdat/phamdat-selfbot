"""
Flask web application with SocketIO.
Serves dashboard, captcha, and data pages. Provides REST API.
"""

import json
import os
import secrets
import time
import uuid
import requests
import threading

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO

from modules.utils.logger import get_ws_handler, get_logger
from modules.utils.constants import WEBSITES_DIR, ASSETS_DIR, DATA_DIR, CACHES_FILE

logger = get_logger('app')

app = Flask(
    __name__,
    template_folder=str(WEBSITES_DIR),
    static_folder=str(ASSETS_DIR),
    static_url_path='/assets',
)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# Link SocketIO to the log handler
get_ws_handler().set_socketio(socketio)

# Reference to BotManager (set by main.py)
bot_manager = None
_start_time = None

def set_bot_manager(bm):
    global bot_manager
    bot_manager = bm

# ── Static & Pages ──────────────────────────────────────────────

@app.route('/')
def page_dashboard():
    return render_template('dashboard.html')

@app.route('/captcha')
def page_captcha():
    return render_template('captcha.html')

@app.route('/data')
def page_data():
    return render_template('data.html')

@app.route('/sw.js')
def service_worker():
    return send_from_directory(str(WEBSITES_DIR), 'sw.js', mimetype='application/javascript')

# ── API: Status ─────────────────────────────────────────────────

@app.route('/api/status')
def api_status():
    global _start_time
    running = bot_manager.is_running() if bot_manager else False
    return jsonify({
        'running': running,
        'start_time': _start_time if running else None,
    })

# ── API: Start / Stop ──────────────────────────────────────────

@app.route('/api/start', methods=['POST'])
def api_start():
    global _start_time
    if not bot_manager:
        return jsonify({'ok': False, 'error': 'Bot manager not initialized'}), 500
    if bot_manager.is_running():
        return jsonify({'ok': False, 'error': 'Already running'})
    try:
        bot_manager.start()
        _start_time = time.time()
        logger.info('Bot started via web')
        return jsonify({'ok': True})
    except Exception:
        logger.exception('Failed to start')
        return jsonify({'ok': False, 'error': 'Failed to start'}), 500

@app.route('/api/stop', methods=['POST'])
def api_stop():
    global _start_time
    if not bot_manager:
        return jsonify({'ok': False, 'error': 'Bot manager not initialized'}), 500
    try:
        bot_manager.stop()
        _start_time = None
        logger.info('Bot stopped via web')
        return jsonify({'ok': True})
    except Exception:
        logger.exception('Failed to stop')
        return jsonify({'ok': False, 'error': 'Failed to stop'}), 500

# ── API: Captcha ────────────────────────────────────────────────

def _load_caches():
    try:
        with open(CACHES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'captchas' not in data:
            data['captchas'] = []
        return data
    except Exception:
        return {'captchas': []}

def _save_caches(data):
    with open(CACHES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route('/api/captcha/list')
def api_captcha_list():
    caches = _load_caches()
    return jsonify(caches.get('captchas', []))

def send_discord_webhook(captcha_data):
    with open(CONFIGS_FILE, 'r', encoding='utf-8') as f:
        DISCORD_WEBHOOK_URL = json.load(f).get('discord_webhook_url')
    if not DISCORD_WEBHOOK_URL:
        return
    
    payload = {
        "content": "🚨 **NEW CAPTCHA DETECTED!** @everyone",
        "embeds": [{
            "title": f"Account: {captcha_data.get('display_name', 'Unknown')}",
            "description": f"Go to solve it!\n**Type:** {captcha_data.get('type', 'Unknown')}\n**Bot:** {captcha_data.get('bot', 'owo')}",
            "color": 16711680,
            "thumbnail": {"url": captcha_data.get('avatar_url', '')}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Discord webhook failed: {e}")

@app.route('/api/captcha/new', methods=['POST'])
def api_captcha_new():
    """Called by bot modules when captcha is detected."""
    payload = request.get_json()
    if not payload:
        return jsonify({'ok': False}), 400

    captcha_entry = {
        'id': str(uuid.uuid4()),
        'user_id': str(payload.get('user_id', '')),
        'display_name': payload.get('display_name', ''),
        'username': payload.get('username', ''),
        'avatar_url': payload.get('avatar_url', ''),
        'bot': payload.get('bot', 'owo'),
        'type': payload.get('type', 'unknown'),
        'data': payload.get('data', None),
        'message_url': payload.get('message_url', ''),
        'answer_input': payload.get('answer_input', False),
        'created_at': payload.get('created_at', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
        'expires_at': payload.get('expires_at', None),
    }

    caches = _load_caches()
    caches['captchas'].append(captcha_entry)
    _save_caches(caches)

    socketio.emit('captcha_new', captcha_entry, namespace='/')
    socketio.emit('captcha_count', {'count': len(caches['captchas'])}, namespace='/')
    threading.Thread(target=send_discord_webhook, args=(captcha_entry,), daemon=True).start()

    logger.warning(f"Captcha detected for {captcha_entry['display_name']} ({captcha_entry['type']})")
    return jsonify({'ok': True, 'id': captcha_entry['id']})

@app.route('/api/captcha/solve', methods=['POST'])
def api_captcha_solve():
    """Called when user solves a captcha on the web."""
    payload = request.get_json()
    captcha_id = payload.get('id')
    answer = payload.get('answer', None)

    caches = _load_caches()
    captcha = None
    for c in caches['captchas']:
        if c['id'] == captcha_id:
            captcha = c
            break

    if not captcha:
        return jsonify({'ok': False, 'error': 'Captcha not found'}), 404

    # Remove from caches
    caches['captchas'] = [c for c in caches['captchas'] if c['id'] != captcha_id]
    _save_caches(caches)

    # Notify bot manager to handle the solve
    if bot_manager:
        bot_manager.handle_captcha_solved(captcha, answer)

    socketio.emit('captcha_count', {'count': len(caches['captchas'])}, namespace='/')
    logger.info(f"Captcha solved for {captcha['display_name']}")
    return jsonify({'ok': True})

@app.route('/api/captcha/delete', methods=['POST'])
def api_captcha_delete():
    """Delete a captcha (already solved externally)."""
    payload = request.get_json()
    captcha_id = payload.get('id')

    caches = _load_caches()
    captcha = None
    for c in caches['captchas']:
        if c['id'] == captcha_id:
            captcha = c
            break

    if not captcha:
        return jsonify({'ok': False, 'error': 'Captcha not found'}), 404

    caches['captchas'] = [c for c in caches['captchas'] if c['id'] != captcha_id]
    _save_caches(caches)

    # Also notify bot manager so the client can resume
    if bot_manager:
        bot_manager.handle_captcha_deleted(captcha)

    socketio.emit('captcha_count', {'count': len(caches['captchas'])}, namespace='/')
    logger.info(f"Captcha deleted for {captcha['display_name']}")
    return jsonify({'ok': True})

# ── API: Data Editor ────────────────────────────────────────────

@app.route('/api/data/files')
def api_data_files():
    """List all files in data/ folder."""
    files = []
    for f in sorted(DATA_DIR.iterdir()):
        if f.is_file():
            files.append(f.name)
    return jsonify(files)

@app.route('/api/data/read')
def api_data_read():
    """Read file content as raw text."""
    filename = request.args.get('file', '')
    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'ok': False, 'error': 'Invalid filename'}), 400

    filepath = DATA_DIR / filename
    if not filepath.is_file():
        return jsonify({'ok': False, 'error': 'File not found'}), 404

    try:
        content = filepath.read_text(encoding='utf-8')
        return jsonify({'ok': True, 'content': content, 'filename': filename})
    except Exception:
        logger.exception('Failed to read file')
        return jsonify({'ok': False, 'error': 'Failed to read file'}), 500

@app.route('/api/data/write', methods=['POST'])
def api_data_write():
    """Write raw text content to a file in data/."""
    payload = request.get_json()
    filename = payload.get('file', '')
    content = payload.get('content', '')

    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'ok': False, 'error': 'Invalid filename'}), 400

    filepath = DATA_DIR / filename
    if not filepath.is_file():
        return jsonify({'ok': False, 'error': 'File not found'}), 404

    try:
        filepath.write_text(content, encoding='utf-8')
        logger.info(f'File saved: {filename}')
        return jsonify({'ok': True})
    except Exception:
        logger.exception('Failed to write file')
        return jsonify({'ok': False, 'error': 'Failed to write file'}), 500

# ── API: Logs ───────────────────────────────────────────────────

@app.route('/api/logs')
def api_logs():
    """Get buffered log entries."""
    handler = get_ws_handler()
    return jsonify(handler.get_buffer())

# ── SocketIO Events ─────────────────────────────────────────────

@socketio.on('connect')
def handle_connect():
    # Send current captcha count
    caches = _load_caches()
    count = len(caches.get('captchas', []))
    socketio.emit('captcha_count', {'count': count}, room=request.sid, namespace='/')

def run_server(host='0.0.0.0', port=8080):
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    logger.info(f'Web: http://{ip}:{port}')
    socketio.run(app, host=host, port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
