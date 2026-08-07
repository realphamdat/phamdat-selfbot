import base64
import json
import logging
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

logger = logging.getLogger('quest')

running = False
stop_event = threading.Event()

API_BASE = 'https://discord.com/api/v9'
POLL_INTERVAL = 60
HEARTBEAT_INTERVAL = 20
AUTO_ACCEPT = True
MAX_QUEST_WORKERS = 10

SUPPORTED_TASKS = [
    'WATCH_VIDEO',
    'PLAY_ON_DESKTOP',
    'STREAM_ON_DESKTOP',
    'PLAY_ACTIVITY',
    'WATCH_VIDEO_ON_MOBILE',
]


def log(msg):
    logger.info(msg)


def warn(msg):
    logger.warning(msg)


def error(msg):
    logger.error(msg)


def read_tokens():
    result = []
    try:
        with open('data/quest.txt', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    result.append(stripped)
    except FileNotFoundError:
        warn('Quest token file not found: data/quest.txt')
    return result


def fetch_latest_build_number():
    FALLBACK = 504649
    try:
        log('Fetching build number from Discord')
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
        r = requests.get('https://discord.com/app', headers={'User-Agent': ua}, timeout=15)
        if r.status_code != 200:
            warn(f'Could not fetch Discord page ({r.status_code}), using fallback')
            return FALLBACK

        scripts = re.findall(r'/assets/([a-f0-9]+)\.js', r.text)
        if not scripts:
            scripts_alt = re.findall(r'src="(/assets/[^"]+\.js)"', r.text)
            scripts = [s.split('/')[-1].replace('.js', '') for s in scripts_alt]
        if not scripts:
            warn('No JS assets found, using fallback')
            return FALLBACK

        for asset_hash in scripts[-5:]:
            try:
                ar = requests.get(f'https://discord.com/assets/{asset_hash}.js', headers={'User-Agent': ua}, timeout=15)
                m = re.search(r'buildNumber["\s:]+["\s]*(\d{5,7})', ar.text)
                if m:
                    bn = int(m.group(1))
                    log(f'Build number: {bn}')
                    return bn
            except Exception:
                continue

        warn(f'Build number not found, using fallback {FALLBACK}')
        return FALLBACK
    except Exception as e:
        error(f'Error fetching build number: {e}, using fallback {FALLBACK}')
        return FALLBACK


def make_super_properties(build_number):
    obj = {
        'os': 'Windows',
        'browser': 'Discord Client',
        'release_channel': 'stable',
        'client_version': '1.0.9175',
        'os_version': '10.0.26100',
        'os_arch': 'x64',
        'app_arch': 'x64',
        'system_locale': 'en-US',
        'browser_user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9175 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36',
        'browser_version': '32.2.7',
        'client_build_number': build_number,
        'native_build_number': 59498,
        'client_event_source': None,
    }
    return base64.b64encode(json.dumps(obj).encode()).decode()


class DiscordAPI:
    def __init__(self, token, build_number):
        self.token = token
        self.session = requests.Session()
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9175 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36'
        sp = make_super_properties(build_number)
        self.session.headers.update({
            'Authorization': token,
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': ua,
            'X-Super-Properties': sp,
            'X-Discord-Locale': 'en-US',
            'X-Discord-Timezone': 'Asia/Ho_Chi_Minh',
            'Origin': 'https://discord.com',
            'Referer': 'https://discord.com/channels/@me',
        })

    def get(self, path, **kwargs):
        kwargs.setdefault('timeout', 15)
        return self.session.get(f'{API_BASE}{path}', **kwargs)

    def post(self, path, payload=None, **kwargs):
        kwargs.setdefault('timeout', 15)
        return self.session.post(f'{API_BASE}{path}', json=payload, **kwargs)

    def validate_token(self):
        try:
            r = self.get('/users/@me')
            if r.status_code == 200:
                user = r.json()
                log(f'Logged in as {user["username"]} (ID: {user["id"]})')
                return True
            warn(f'Token invalid (status {r.status_code})')
            return False
        except Exception as e:
            error(f'Connection to Discord failed: {e}')
            return False


def _get(source, *keys):
    if source is None:
        return None
    for k in keys:
        if k in source:
            return source[k]
    return None


def get_task_config(quest):
    quest_config = quest.get('config', {})
    return _get(quest_config, 'taskConfig', 'task_config', 'taskConfigV2', 'task_config_v2')


def get_quest_name(quest):
    quest_config = quest.get('config', {})
    msgs = quest_config.get('messages', {})
    name = _get(msgs, 'questName', 'quest_name')
    if name:
        return name.strip()
    game = _get(msgs, 'gameTitle', 'game_title')
    if game:
        return game.strip()
    app_name = quest_config.get('application', {}).get('name')
    if app_name:
        return app_name
    return f"Quest#{quest.get('id', '?')}"


def get_expires_at(quest):
    quest_config = quest.get('config', {})
    return _get(quest_config, 'expiresAt', 'expires_at')


def get_user_status(quest):
    us = _get(quest, 'userStatus', 'user_status')
    return us if isinstance(us, dict) else {}


def is_completable(quest):
    expires = get_expires_at(quest)
    if expires:
        try:
            exp_dt = datetime.fromisoformat(expires.replace('Z', '+00:00'))
            if exp_dt <= datetime.now(timezone.utc):
                return False
        except Exception:
            pass
    tc = get_task_config(quest)
    if not tc or 'tasks' not in tc:
        return False
    tasks = tc['tasks']
    return any(tasks.get(t) is not None for t in SUPPORTED_TASKS)


def is_enrolled(quest):
    us = get_user_status(quest)
    return bool(_get(us, 'enrolledAt', 'enrolled_at'))


def is_completed(quest):
    us = get_user_status(quest)
    return bool(_get(us, 'completedAt', 'completed_at'))


def get_task_type(quest):
    tc = get_task_config(quest)
    if not tc or 'tasks' not in tc:
        return None
    for t in SUPPORTED_TASKS:
        if tc['tasks'].get(t) is not None:
            return t
    return None


def get_seconds_needed(quest):
    tc = get_task_config(quest)
    task_type = get_task_type(quest)
    if not tc or not task_type:
        return 0
    return tc['tasks'][task_type].get('target', 0)


def get_seconds_done(quest):
    task_type = get_task_type(quest)
    if not task_type:
        return 0
    us = get_user_status(quest)
    progress = us.get('progress', {})
    return progress.get(task_type, {}).get('value', 0)


def get_enrolled_at(quest):
    us = get_user_status(quest)
    return _get(us, 'enrolledAt', 'enrolled_at')


class QuestAutocompleter:
    def __init__(self, api):
        self.api = api
        self.completed_ids = set()
        self.in_progress_ids = set()
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=MAX_QUEST_WORKERS)

    def fetch_quests(self):
        while True:
            if not running:
                return []
            try:
                r = self.api.get('/quests/@me')
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, dict):
                        quests = data.get('quests', [])
                        blocked = _get(data, 'quest_enrollment_blocked_until')
                        if blocked:
                            warn(f'Enrollment blocked until: {blocked}')
                        return quests
                    elif isinstance(data, list):
                        return data
                    return []
                elif r.status_code == 429:
                    retry_after = r.json().get('retry_after', 10)
                    warn(f'Rate limited on fetch, waiting {retry_after}s')
                    if stop_event.wait(retry_after):
                        return []
                    continue
                else:
                    error(f'Quest fetch error ({r.status_code}): {r.text[:200]}')
                    return []
            except Exception as e:
                error(f'Error fetching quests: {e}')
                return []

    def enroll_quest(self, quest):
        name = get_quest_name(quest)
        qid = quest['id']
        for attempt in range(1, 4):
            if not running:
                return False
            try:
                payload = {
                    'location': 11,
                    'is_targeted': False,
                    'metadata_raw': None,
                    'metadata_sealed': None,
                    'traffic_metadata_raw': quest.get('traffic_metadata_raw'),
                    'traffic_metadata_sealed': quest.get('traffic_metadata_sealed'),
                }
                r = self.api.post(f'/quests/{qid}/enroll', payload)
                if r.status_code == 429:
                    retry_after = r.json().get('retry_after', 5)
                    wait = retry_after + 1
                    warn(f'Rate limited on enroll "{name}" (attempt {attempt}/3), waiting {wait}s')
                    if stop_event.wait(wait):
                        return False
                    continue
                if r.status_code in (200, 201, 204):
                    log(f'Enrolled: {name}')
                    return True
                error(f'Enroll "{name}" failed ({r.status_code}): {r.text[:200]}')
                return False
            except Exception as e:
                error(f'Enroll error "{name}": {e}')
                return False
        warn(f'Skipping "{name}" after 3 rate limit hits')
        return False

    def auto_accept(self, quests):
        if not AUTO_ACCEPT:
            return quests
        unaccepted = [q for q in quests if not is_enrolled(q) and not is_completed(q) and is_completable(q)]
        if not unaccepted:
            return quests
        log(f'Found {len(unaccepted)} quest(s) to auto-accept')
        for q in unaccepted:
            self.enroll_quest(q)
            if stop_event.wait(3):
                return quests
        if stop_event.wait(2):
            return quests
        return self.fetch_quests()

    def complete_video(self, quest):
        name = get_quest_name(quest)
        qid = quest['id']
        seconds_needed = get_seconds_needed(quest)
        seconds_done = get_seconds_done(quest)
        enrolled_at_str = get_enrolled_at(quest)
        if enrolled_at_str:
            enrolled_ts = datetime.fromisoformat(enrolled_at_str.replace('Z', '+00:00')).timestamp()
        else:
            enrolled_ts = time.time()

        log(f'[Video] {name} ({seconds_done:.0f}/{seconds_needed}s)')
        max_future = 10
        speed = 7
        interval = 1

        while seconds_done < seconds_needed:
            if not running or qid in self.completed_ids:
                return
            max_allowed = (time.time() - enrolled_ts) + max_future
            diff = max_allowed - seconds_done
            timestamp = seconds_done + speed

            if diff >= speed:
                try:
                    r = self.api.post(f'/quests/{qid}/video-progress', {
                        'timestamp': min(seconds_needed, timestamp + random.random())
                    })
                    if r.status_code == 200:
                        body = r.json()
                        if body.get('completed_at'):
                            log(f'Completed: {name}')
                            with self.lock:
                                self.completed_ids.add(qid)
                            return
                        seconds_done = min(seconds_needed, timestamp)
                        log(f'[{name}] {seconds_done:.0f}/{seconds_needed}s')
                    elif r.status_code == 429:
                        retry_after = r.json().get('retry_after', 5)
                        warn(f'Rate limited on video, waiting {retry_after + 1}s')
                        if stop_event.wait(retry_after + 1):
                            return
                        continue
                    else:
                        error(f'Video progress error ({r.status_code}): {r.text[:200]}')
                except Exception as e:
                    error(f'Video progress error: {e}')
            if timestamp >= seconds_needed:
                break
            if stop_event.wait(interval):
                return

        try:
            self.api.post(f'/quests/{qid}/video-progress', {'timestamp': seconds_needed})
        except Exception:
            pass
        log(f'Completed: {name}')
        with self.lock:
            self.completed_ids.add(qid)

    def _heartbeat_loop(self, quest, stream_key, task_type):
        name = get_quest_name(quest)
        qid = quest['id']
        seconds_needed = get_seconds_needed(quest)
        seconds_done = get_seconds_done(quest)
        remaining = max(0, seconds_needed - seconds_done)
        log(f'[{task_type}] {name} (~{remaining // 60} min left)')

        while seconds_done < seconds_needed:
            if not running or qid in self.completed_ids:
                return
            try:
                r = self.api.post(f'/quests/{qid}/heartbeat', {
                    'stream_key': stream_key,
                    'terminal': False,
                })
                if r.status_code == 200:
                    body = r.json()
                    progress_data = body.get('progress', {})
                    if progress_data and task_type in progress_data:
                        seconds_done = progress_data[task_type].get('value', seconds_done)
                    log(f'[{name}] {seconds_done:.0f}/{seconds_needed}s')
                    if body.get('completed_at') or seconds_done >= seconds_needed:
                        log(f'Completed: {name}')
                        with self.lock:
                            self.completed_ids.add(qid)
                        return
                elif r.status_code == 429:
                    retry_after = r.json().get('retry_after', 10)
                    warn(f'Rate limited on heartbeat, waiting {retry_after + 1}s')
                    if stop_event.wait(retry_after + 1):
                        return
                else:
                    error(f'Heartbeat error ({r.status_code}): {r.text[:200]}')
            except Exception as e:
                error(f'Heartbeat error: {e}')
            if stop_event.wait(HEARTBEAT_INTERVAL):
                return

        try:
            self.api.post(f'/quests/{qid}/heartbeat', {'stream_key': stream_key, 'terminal': True})
        except Exception:
            pass
        log(f'Completed: {name}')
        with self.lock:
            self.completed_ids.add(qid)

    def process_quest(self, quest):
        name = get_quest_name(quest)
        qid = quest['id']
        task_type = get_task_type(quest)
        if not task_type:
            warn(f'{name}, unsupported task, skipping')
            return
        log(f'Starting: {name} (task: {task_type})')
        if task_type in ('WATCH_VIDEO', 'WATCH_VIDEO_ON_MOBILE'):
            self.complete_video(quest)
        elif task_type in ('PLAY_ON_DESKTOP', 'STREAM_ON_DESKTOP'):
            pid = random.randint(1000, 30000)
            self._heartbeat_loop(quest, f'call:0:{pid}', task_type)
        elif task_type == 'PLAY_ACTIVITY':
            self._heartbeat_loop(quest, 'call:0:1', 'PLAY_ACTIVITY')

    def _process_and_cleanup(self, quest):
        qid = quest['id']
        try:
            self.process_quest(quest)
        except Exception as e:
            warn(f'Unexpected error processing quest {qid}: {e}')
        finally:
            with self.lock:
                self.in_progress_ids.discard(qid)

    def run(self):
        cycle = 0
        while running:
            cycle += 1
            log(f'--- Scan {cycle} ---')
            quests = self.fetch_quests()
            if not quests:
                log('No quests available')
            else:
                enrolled = sum(1 for q in quests if is_enrolled(q))
                completed = sum(1 for q in quests if is_completed(q))
                completable = sum(1 for q in quests if is_completable(q))
                log(f'Total: {len(quests)} | Enrolled: {enrolled} | Completed: {completed} | Completable: {completable}')

                quests = self.auto_accept(quests)

                with self.lock:
                    actionable = [
                        q for q in quests
                        if is_enrolled(q) and not is_completed(q) and is_completable(q)
                        and q['id'] not in self.completed_ids
                        and q['id'] not in self.in_progress_ids
                    ]

                if actionable:
                    log(f'Starting {len(actionable)} quest(s)')
                    for q in actionable:
                        qid = q['id']
                        with self.lock:
                            if qid not in self.in_progress_ids:
                                self.in_progress_ids.add(qid)
                                self.executor.submit(self._process_and_cleanup, q)
                else:
                    log('No quests need completion right now')

            log(f'Waiting {POLL_INTERVAL}s before next scan')
            if stop_event.wait(POLL_INTERVAL):
                break

        self.executor.shutdown(wait=False)
        log('Quest autocompleter stopped')


def run_account(token, build_number):
    api = DiscordAPI(token, build_number)
    if not api.validate_token():
        warn('Skipping account, token validation failed')
        return
    completer = QuestAutocompleter(api)
    completer.run()


def main():
    global running
    tokens = read_tokens()
    if not tokens:
        running = False
        return

    log(f'Loaded {len(tokens)} token(s)')
    build_number = fetch_latest_build_number()

    account_threads = []
    for token in tokens:
        t = threading.Thread(target=run_account, args=(token, build_number), daemon=True)
        t.start()
        account_threads.append(t)

    log(f'Running {len(tokens)} account(s)')
    while running and any(t.is_alive() for t in account_threads):
        if stop_event.wait(1):
            break
    running = False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s', datefmt='%H:%M:%S')
    running = True
    stop_event.clear()
    main()