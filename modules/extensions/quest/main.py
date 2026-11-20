import base64
import json
import logging
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import parse_qs, quote, urlparse

import requests
from requests.adapters import HTTPAdapter

from modules.utils.data_store import read_lines

logger = logging.getLogger('quest')

running = False
stop_event = threading.Event()

API_BASE = 'https://discord.com/api/v9'
POLL_INTERVAL = 300
AUTO_ACCEPT = True
CLAIM_REWARDS = True
ACHIEVEMENT_BYPASS = False
VIDEO_WORKERS = 2
GAME_WORKERS = 1
EXCLUDED_QUESTS = set()

BLACKLISTED_QUEST_ID = '1412491570820812933'
CONSOLE_KEYS = {'PLAY_ON_XBOX', 'PLAY_ON_PLAYSTATION'}
UNAUTOMATABLE_KEYS = {'ACHIEVEMENT_IN_GAME': 'needs the game linked and an achievement earned in-game'}
TASK_FAMILIES = (
    ('ACHIEVEMENT', lambda k: k == 'ACHIEVEMENT_IN_ACTIVITY', ('ACHIEVEMENT_IN_ACTIVITY',)),
    ('ACTIVITY', lambda k: k == 'PLAY_ACTIVITY', ('PLAY_ACTIVITY',)),
    ('VIDEO', lambda k: 'VIDEO' in k, ('WATCH_VIDEO',)),
    ('GAME', lambda k: k.startswith('PLAY'), ('PLAY_ON_DESKTOP',)),
    ('STREAM', lambda k: k.startswith('STREAM'), ('STREAM_ON_DESKTOP',)),
    ('ACTIVITY', lambda k: 'ACTIVITY' in k, ()),
)
CLIENT_ERRORS = {400, 403, 404, 409, 410}
MAX_RETRIES = 3
MAX_FAILURES = 5
MAX_TIME = 25 * 60

UA_CLIENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
             '(KHTML, like Gecko) discord/1.0.9175 Chrome/128.0.6613.186 '
             'Electron/32.2.7 Safari/537.36')


def fetch_latest_build_number():
    FALLBACK = 504649
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    try:
        r = requests.get('https://discord.com/app', headers={'User-Agent': ua}, timeout=15)
        if r.status_code == 200:
            scripts = re.findall(r'/assets/([a-f0-9]+)\.js', r.text) or \
                      [m.split('/')[-1][:-3] for m in re.findall(r'src="(/assets/[^"]+\.js)"', r.text)]
            for asset_hash in scripts[-5:]:
                ar = requests.get(f'https://discord.com/assets/{asset_hash}.js', headers={'User-Agent': ua}, timeout=15)
                m = re.search(r'buildNumber["\s:]+["\s]*(\d{5,7})', ar.text)
                if m:
                    return int(m.group(1))
    except Exception:
        pass
    return FALLBACK


def make_super_properties(build_number):
    return base64.b64encode(json.dumps({
        'os': 'Windows',
        'browser': 'Discord Client',
        'release_channel': 'stable',
        'client_version': '1.0.9175',
        'os_version': '10.0.26100',
        'os_arch': 'x64',
        'app_arch': 'x64',
        'system_locale': 'en-US',
        'browser_user_agent': UA_CLIENT,
        'browser_version': '32.2.7',
        'client_build_number': build_number,
        'native_build_number': 59498,
        'client_event_source': None,
    }).encode()).decode()


class DiscordAPI:
    def __init__(self, token, build_number):
        self.session = requests.Session()
        pool = HTTPAdapter(pool_connections=4, pool_maxsize=4)
        self.session.mount('https://', pool)
        self.session.mount('http://', pool)
        self.session.headers.update({
            'Authorization': token,
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': UA_CLIENT,
            'X-Super-Properties': make_super_properties(build_number),
            'X-Discord-Locale': 'en-US',
            'X-Discord-Timezone': 'Asia/Ho_Chi_Minh',
            'Origin': 'https://discord.com',
            'Referer': 'https://discord.com/channels/@me',
        })

    def get(self, path, **kwargs):
        return self.session.get(f'{API_BASE}{path}', timeout=15, **kwargs)

    def post(self, path, payload=None, **kwargs):
        return self.session.post(f'{API_BASE}{path}', json=payload, timeout=15, **kwargs)

    def delete(self, path, **kwargs):
        return self.session.delete(f'{API_BASE}{path}', timeout=15, **kwargs)

    def validate_token(self):
        try:
            r = self.get('/users/@me')
            if r.status_code == 200:
                user = r.json()
                logger.info(f'Logged in as {user["username"]} (ID: {user["id"]})')
                return user
            logger.warning(f'Token invalid (status {r.status_code})')
        except Exception as e:
            logger.warning(f'Connection to Discord failed: {e}')
        return None


def build_stream_key(api, user_id):
    try:
        r = api.get('/users/@me/channels')
        if r.status_code == 200:
            for ch in r.json():
                if ch.get('type') == 1:
                    return f'call:{ch["id"]}:{user_id}'
    except Exception:
        pass
    return f'call:0:{user_id}'


def _get(source, *keys):
    if source is None:
        return None
    for k in keys:
        if k in source:
            return source[k]
    return None


def get_task_config(config):
    v2 = _get(config, 'taskConfigV2', 'task_config_v2')
    if v2 and v2.get('tasks'):
        return v2
    legacy = _get(config, 'taskConfig', 'task_config')
    if legacy and legacy.get('tasks'):
        return legacy
    return v2 or legacy or {}


def get_quest_name(quest):
    cfg = quest.get('config', {})
    msgs = cfg.get('messages', {})
    name = _get(msgs, 'questName', 'quest_name') or _get(msgs, 'gameTitle', 'game_title')
    if name:
        return name.strip()
    return cfg.get('application', {}).get('name') or f"Quest#{quest.get('id', '?')}"


def get_user_status(quest):
    us = _get(quest, 'userStatus', 'user_status')
    return us if isinstance(us, dict) else {}


def is_expired(quest):
    expires = _get(quest.get('config', {}), 'expiresAt', 'expires_at')
    if not expires:
        return False
    try:
        return datetime.fromisoformat(expires.replace('Z', '+00:00')) <= datetime.now(timezone.utc)
    except ValueError:
        return False


def is_enrolled(quest):
    return bool(_get(get_user_status(quest), 'enrolledAt', 'enrolled_at'))


def is_completed(quest):
    return bool(_get(get_user_status(quest), 'completedAt', 'completed_at'))


def select_task(quest):
    cfg = quest.get('config', {})
    tasks = get_task_config(cfg).get('tasks') or {}
    for family, match, prefer in TASK_FAMILIES:
        key = next((k for k in prefer if k in tasks), None) or \
              next((k for k in tasks if match(k) and k not in CONSOLE_KEYS), None)
        if key:
            task = tasks[key] or {}
            apps = task.get('applications') or []
            app_id = (apps[0].get('id') if apps else None) or cfg.get('application', {}).get('id')
            return {'family': family, 'key': key, 'target': task.get('target', 0), 'app_id': app_id}
    return None


def quest_blocker(quest):
    keys = list(get_task_config(quest.get('config', {})).get('tasks') or {})
    task = select_task(quest)
    if not task:
        if not keys:
            return 'no tasks listed'
        if all(k in CONSOLE_KEYS for k in keys):
            return f'console-only ({", ".join(keys)})'
        named = next((k for k in keys if k in UNAUTOMATABLE_KEYS), None)
        if named:
            return f'{named}: {UNAUTOMATABLE_KEYS[named]}'
        return f'unsupported task type ({", ".join(keys)})'
    if task['target'] <= 0:
        return f'invalid target ({task["target"]})'
    if task['family'] in ('GAME', 'STREAM') and not task['app_id']:
        return 'no application id in config'
    return None


def get_progress(quest, key):
    us = get_user_status(quest)
    entry = (us.get('progress') or {}).get(key) or {}
    return entry.get('value') or us.get('streamProgressSeconds') or 0


def quest_orbs(quest):
    cfg = _get(quest.get('config', {}), 'rewardsConfig', 'rewards_config') or {}
    return sum(r.get('orbQuantity') or 0 for r in cfg.get('rewards') or [] if isinstance(r, dict))


def _in_future(raw):
    if not raw:
        return False
    try:
        return datetime.fromisoformat(str(raw).replace('Z', '+00:00')) > datetime.now(timezone.utc)
    except ValueError:
        return False


class QuestStopped(Exception):
    pass


class QuestHTTPError(Exception):
    def __init__(self, status, body):
        self.status = status
        self.body = body if isinstance(body, dict) else {}
        super().__init__(f'HTTP {status}: {self.body.get("message") or json.dumps(self.body)[:150]}')


class Traffic:
    def __init__(self, api):
        self.api = api
        self._lock = threading.Lock()
        self._next_at = 0.0
        self._global_until = 0.0

    def _slot(self):
        with self._lock:
            now = time.time()
            start = max(now, self._next_at, self._global_until)
            self._next_at = start + random.uniform(1.2, 1.8)
        return start - now

    def post(self, path, payload):
        for attempt in range(MAX_RETRIES + 1):
            if not running:
                raise QuestStopped()
            wait = self._slot()
            if wait > 0 and stop_event.wait(wait):
                raise QuestStopped()
            try:
                r = self.api.post(path, payload)
            except requests.RequestException as e:
                if attempt >= MAX_RETRIES:
                    raise QuestHTTPError(0, {'message': str(e)})
                logger.warning(f'Retry {attempt + 1}/{MAX_RETRIES} for {path}: {e}')
                if stop_event.wait(2 ** (attempt + 1) + random.uniform(0.2, 0.8)):
                    raise QuestStopped()
                continue
            if r.status_code in (200, 201, 202, 204):
                return r.json() if r.content else {}
            try:
                body = r.json()
            except ValueError:
                body = {}
            if not isinstance(body, dict):
                body = {}
            retryable = r.status_code in (408, 429) or r.status_code >= 500
            if retryable and attempt < MAX_RETRIES:
                delay = (body.get('retry_after') or 2 ** (attempt + 1)) + random.uniform(0.2, 0.8)
                if body.get('global'):
                    with self._lock:
                        self._global_until = max(self._global_until, time.time() + delay)
                logger.warning(f'Rate limited ({r.status_code}) on {path}, retry in {delay:.1f}s')
                if stop_event.wait(delay):
                    raise QuestStopped()
                continue
            raise QuestHTTPError(r.status_code, body)


class QuestAutocompleter:
    def __init__(self, api, stream_key):
        self.api = api
        self.stream_key = stream_key
        self.traffic = Traffic(api)
        self.completed_ids = set()
        self.skipped_ids = set()
        self.in_progress_ids = set()
        self.lock = threading.Lock()
        self.enrollment_blocked_until = None
        self.access_suspended_until = None
        self.access_suspended = False

    def _skip(self, qid):
        with self.lock:
            self.skipped_ids.add(qid)

    def _fail(self, quest, reason):
        logger.warning(f'Failed "{get_quest_name(quest)}": {reason}')
        self._skip(quest['id'])

    def _finish(self, quest):
        name = get_quest_name(quest)
        orbs = quest_orbs(quest)
        logger.info(f'Completed: {name}' + (f' (+{orbs} Orbs)' if orbs else ''))
        with self.lock:
            self.completed_ids.add(quest['id'])
        self.claim_reward(quest)

    def fetch_quests(self):
        while running:
            try:
                r = self.api.get('/quests/@me')
            except Exception as e:
                logger.warning(f'Error fetching quests: {e}')
                return []
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    self.enrollment_blocked_until = data.get('quest_enrollment_blocked_until')
                    self.access_suspended_until = data.get('quest_access_suspended_until')
                    self.access_suspended = bool(data.get('is_quest_access_suspended'))
                    return data.get('quests', [])
                return data if isinstance(data, list) else []
            if r.status_code == 429:
                retry_after = r.json().get('retry_after', 10)
                logger.warning(f'Rate limited, waiting {retry_after}s')
                if stop_event.wait(retry_after):
                    return []
                continue
            logger.warning(f'Quest fetch error ({r.status_code}): {r.text[:200]}')
            return []
        return []

    def enroll_quest(self, quest):
        name = get_quest_name(quest)
        try:
            self.traffic.post(f'/quests/{quest["id"]}/enroll', {
                'location': 11,
                'is_targeted': False,
                'metadata_sealed': None,
                'traffic_metadata_sealed': quest.get('traffic_metadata_sealed'),
            })
            logger.info(f'Enrolled: {name}')
            return True
        except QuestStopped:
            return False
        except QuestHTTPError as e:
            logger.warning(f'Enroll "{name}" failed: {e}')
            self._skip(quest['id'])
            return False

    def claim_reward(self, quest):
        if not CLAIM_REWARDS:
            return
        if stop_event.wait(random.uniform(2.5, 6.0)):
            return
        name = get_quest_name(quest)
        try:
            body = self.traffic.post(f'/quests/{quest["id"]}/claim-reward', {
                'platform': 0,
                'location': 11,
                'is_targeted': False,
                'metadata_sealed': None,
                'traffic_metadata_sealed': quest.get('traffic_metadata_sealed'),
            })
            if body.get('claimed_at'):
                logger.info(f'Claimed reward: {name}')
        except QuestStopped:
            pass
        except QuestHTTPError as e:
            if e.body.get('captcha_key') or e.body.get('captcha_sitekey'):
                logger.warning(f'Claim "{name}" needs captcha; claim it in Discord\'s Quests page')
            else:
                logger.warning(f'Claim "{name}" failed: {e}')

    def auto_accept(self, quests):
        if not AUTO_ACCEPT:
            return quests
        unaccepted = [
            q for q in quests
            if not is_enrolled(q) and not is_completed(q) and not is_expired(q)
            and q['id'] not in self.skipped_ids and q['id'] not in EXCLUDED_QUESTS
            and q['id'] != BLACKLISTED_QUEST_ID
        ]
        if not unaccepted:
            return quests
        logger.info(f'Auto-accepting {len(unaccepted)} quest(s)')
        for q in unaccepted:
            if not running:
                return quests
            self.enroll_quest(q)
        if stop_event.wait(2):
            return quests
        return self.fetch_quests()

    def complete_video(self, quest, task):
        name = get_quest_name(quest)
        qid, key, target = quest['id'], task['key'], task['target']
        cur = get_progress(quest, key)
        logger.info(f'Video: {name} ({cur:.0f}/{target}s)')
        fails = 0
        start = time.time()
        while cur < target and running:
            delay = random.uniform(7.0, 9.5)
            if stop_event.wait(delay):
                return 'stopped'
            cur += delay + random.uniform(-0.01, 0.01)
            try:
                body = self.traffic.post(f'/quests/{qid}/video-progress', {'timestamp': round(min(target, cur), 6)})
            except QuestStopped:
                return 'stopped'
            except QuestHTTPError as e:
                if e.status in CLIENT_ERRORS:
                    self._fail(quest, f'video unavailable (HTTP {e.status})')
                    return 'failed'
                fails += 1
                if fails >= MAX_FAILURES:
                    self._fail(quest, 'too many network failures')
                    return 'failed'
                continue
            if not running:
                return 'stopped'
            fails = 0
            server = ((body.get('progress') or {}).get(key) or {}).get('value')
            if server is not None and server > cur:
                cur = min(target, server)
            if body.get('completed_at'):
                return 'completed'
            logger.info(f'[{name}] {cur:.0f}/{target}s')
            if time.time() - start > MAX_TIME:
                self._fail(quest, 'timeout exceeded')
                return 'failed'
        return 'completed' if cur >= target and running else 'stopped'

    def _heartbeat_abort(self, quest, task, reason):
        if task['family'] == 'ACHIEVEMENT':
            return 'rejected'
        self._fail(quest, reason)
        return 'failed'

    def complete_heartbeat(self, quest, task):
        name = get_quest_name(quest)
        qid, key, target = quest['id'], task['key'], task['target']
        interval = (19.0, 22.0) if task['family'] in ('ACTIVITY', 'ACHIEVEMENT') else (60.0, 61.0)
        beat = {'stream_key': self.stream_key, 'application_id': str(task['app_id'] or ''), 'terminal': False}
        cur = get_progress(quest, key)
        logger.info(f'[{key}] {name} (~{max(0, target - cur) // 60:.0f} min left)')
        fails = 0
        stalled = 0
        start = time.time()
        while cur < target and running:
            try:
                body = self.traffic.post(f'/quests/{qid}/heartbeat', beat)
            except QuestStopped:
                return 'stopped'
            except QuestHTTPError as e:
                if e.status in CLIENT_ERRORS:
                    return self._heartbeat_abort(quest, task, f'heartbeat rejected (HTTP {e.status})')
                fails += 1
                if fails >= MAX_FAILURES:
                    return self._heartbeat_abort(quest, task, 'too many network failures')
                if stop_event.wait(random.uniform(*interval)):
                    return 'stopped'
                continue
            if not running:
                return 'stopped'
            fails = 0
            value = ((body.get('progress') or {}).get(key) or {}).get('value')
            if value is not None:
                stalled = stalled + 1 if value <= cur else 0
                cur = value
                if stalled >= MAX_FAILURES:
                    return self._heartbeat_abort(quest, task, 'Discord credited no progress')
            logger.info(f'[{name}] {cur:.0f}/{target}s')
            if body.get('completed_at') or cur >= target:
                try:
                    self.traffic.post(f'/quests/{qid}/heartbeat', {**beat, 'terminal': True})
                except (QuestHTTPError, QuestStopped):
                    pass
                return 'completed'
            if time.time() - start > MAX_TIME:
                return self._heartbeat_abort(quest, task, 'timeout exceeded')
            if stop_event.wait(random.uniform(*interval)):
                return 'stopped'
        return 'stopped'

    def bypass_achievement(self, quest, task):
        name = get_quest_name(quest)
        qid, app_id = quest['id'], str(task['app_id'] or '')
        if not app_id.isdigit():
            logger.warning(f'Bypass "{name}": no numeric application id')
            return False
        try:
            r = self.api.get('/oauth2/tokens')
            if r.status_code != 200:
                logger.warning(f'Bypass "{name}": cannot snapshot OAuth grants (HTTP {r.status_code})')
                return False
            pre_ids = {t['id'] for t in r.json() if (t.get('application') or {}).get('id') == app_id}
        except Exception as e:
            logger.warning(f'Bypass "{name}": grant snapshot failed: {e}')
            return False
        authorized = False
        try:
            r = self.api.post(
                f'/oauth2/authorize?response_type=code&client_id={app_id}'
                '&scope=identify%20applications.commands%20applications.entitlements',
                {'permissions': '0', 'authorize': True, 'integration_type': 1,
                 'location_context': {'guild_id': '10000', 'channel_id': '10000', 'channel_type': 10000}})
            authorized = True
            if r.status_code != 200:
                raise QuestHTTPError(r.status_code, r.json() if r.content else {})
            code = (parse_qs(urlparse(r.json().get('location') or '').query).get('code') or [None])[0]
            if not code:
                raise ValueError('no code in authorize response')
            r = self.api.post(f'/applications/{app_id}/proxy-tickets', {})
            if r.status_code != 200:
                raise QuestHTTPError(r.status_code, r.json() if r.content else {})
            ticket = r.json().get('ticket')
            if not ticket:
                raise ValueError('no proxy ticket')
            referrer = (f'https://{app_id}.discordsays.com/?instance_id=example-cl-instance'
                        f'&platform=desktop&discord_proxy_ticket={quote(ticket)}')
            headers = {'Content-Type': 'application/json', 'X-Auth-Token': '',
                       'X-Discord-Quest-ID': qid, 'Referer': referrer}
            base = f'https://{app_id}.discordsays.com/.proxy/acf'
            auth = requests.post(f'{base}/authorize', json={'code': code}, headers=headers, timeout=15, allow_redirects=False)
            if auth.status_code != 200:
                raise QuestHTTPError(auth.status_code, auth.json() if auth.content else {})
            token = auth.json().get('token')
            if not token:
                raise ValueError('no discordsays token')
            headers['X-Auth-Token'] = token
            prog = requests.post(f'{base}/quest/progress', json={'progress': task['target']}, headers=headers, timeout=15, allow_redirects=False)
            if prog.status_code != 200:
                raise QuestHTTPError(prog.status_code, prog.json() if prog.content else {})
            logger.info(f'Bypass succeeded: {name}')
            return True
        except Exception as e:
            body = e.body if isinstance(e, QuestHTTPError) else {}
            if body.get('code') == 50165:
                logger.warning(f'Bypass "{name}": activity is age-gated or delisted on this account')
            else:
                logger.warning(f'Bypass "{name}" failed: {e}')
            return False
        finally:
            if authorized:
                self._revoke_new_grants(app_id, pre_ids)

    def _revoke_new_grants(self, app_id, pre_ids):
        try:
            r = self.api.get('/oauth2/tokens')
            if r.status_code != 200:
                return
            for t in r.json():
                if (t.get('application') or {}).get('id') == app_id and t['id'] not in pre_ids:
                    self.api.delete(f'/oauth2/tokens/{t["id"]}')
        except Exception as e:
            logger.warning(f'OAuth grant cleanup failed: {e}')

    def process_quest(self, quest):
        task = select_task(quest)
        if not task:
            return
        name = get_quest_name(quest)
        logger.info(f'Starting: {name} (task: {task["key"]})')
        if task['family'] == 'VIDEO':
            status = self.complete_video(quest, task)
        elif task['family'] == 'ACHIEVEMENT':
            status = self.complete_heartbeat(quest, task)
            if status in ('rejected', 'failed'):
                if not ACHIEVEMENT_BYPASS:
                    self._fail(quest, 'heartbeat path failed and ACHIEVEMENT_BYPASS is off')
                    return
                logger.info(f'Attempting Discord Says bypass: {name}')
                if not self.bypass_achievement(quest, task):
                    self._fail(quest, 'no auto-completion path worked (likely age-gated/delisted)')
                    return
                status = 'completed'
        else:
            status = self.complete_heartbeat(quest, task)
        if status == 'completed':
            self._finish(quest)

    def _process_and_cleanup(self, quest):
        try:
            self.process_quest(quest)
        except QuestStopped:
            pass
        except Exception as e:
            logger.warning(f'Unexpected error processing quest {quest["id"]}: {e}')
            self._skip(quest['id'])
        finally:
            with self.lock:
                self.in_progress_ids.discard(quest['id'])

    def _mark_blockers(self, quests):
        for q in quests:
            qid = q['id']
            if qid in self.skipped_ids or qid in self.completed_ids or qid in EXCLUDED_QUESTS \
                    or qid == BLACKLISTED_QUEST_ID or is_completed(q) or is_expired(q):
                continue
            reason = quest_blocker(q)
            if reason:
                logger.warning(f'Skipping "{get_quest_name(q)}": {reason}')
                self._skip(qid)

    def run(self):
        logger.info(f'Quest Auto-Completer | Auto-accept: {"ON" if AUTO_ACCEPT else "OFF"} '
                    f'| Claim: {"ON" if CLAIM_REWARDS else "OFF"} | Poll: {POLL_INTERVAL}s')
        video_pool = ThreadPoolExecutor(max_workers=VIDEO_WORKERS)
        game_pool = ThreadPoolExecutor(max_workers=GAME_WORKERS)
        cycle = 0
        while running:
            cycle += 1
            logger.info(f'-- Scan #{cycle} --')
            quests = self.fetch_quests()
            if self.access_suspended or _in_future(self.access_suspended_until):
                logger.error('Discord has suspended quest access on this account; stopping')
                break
            if _in_future(self.enrollment_blocked_until):
                logger.error(f'Quest enrollment blocked until {self.enrollment_blocked_until}; stopping')
                break
            if not quests:
                logger.info('No quests available')
                if stop_event.wait(POLL_INTERVAL):
                    break
                continue
            logger.info(f'Total: {len(quests)} | Enrolled: {sum(is_enrolled(q) for q in quests)} '
                        f'| Completed: {sum(is_completed(q) for q in quests)}')
            self._mark_blockers(quests)
            quests = self.auto_accept(quests)
            with self.lock:
                actionable = [
                    q for q in quests
                    if is_enrolled(q) and not is_completed(q) and not is_expired(q)
                    and q['id'] not in self.completed_ids and q['id'] not in self.skipped_ids
                    and q['id'] not in self.in_progress_ids and q['id'] not in EXCLUDED_QUESTS
                    and q['id'] != BLACKLISTED_QUEST_ID
                ]
                for q in actionable:
                    self.in_progress_ids.add(q['id'])
            if actionable:
                for q in actionable:
                    task = select_task(q)
                    pool = video_pool if task and task['family'] == 'VIDEO' else game_pool
                    pool.submit(self._process_and_cleanup, q)
                logger.info(f'Started {len(actionable)} quest(s) (video x{VIDEO_WORKERS}, game x{GAME_WORKERS})')
            else:
                logger.info(f'Nothing left to run. {len(self.completed_ids)} completed, '
                            f'{len(self.skipped_ids)} skipped/failed this session')
            if stop_event.wait(POLL_INTERVAL):
                break
        video_pool.shutdown(wait=False)
        game_pool.shutdown(wait=False)
        logger.info('Quest autocompleter stopped')


def run_account(token, build_number):
    api = DiscordAPI(token, build_number)
    user = api.validate_token()
    if not user:
        logger.warning('Skipping account, token validation failed')
        return
    QuestAutocompleter(api, build_stream_key(api, user['id'])).run()


def main():
    global running
    tokens = read_lines('data/quest.txt')
    if not tokens:
        logger.warning('No quest tokens found in data/quest.txt')
        running = False
        return
    logger.info(f'Loaded {len(tokens)} token(s)')
    build_number = fetch_latest_build_number()
    account_threads = [threading.Thread(target=run_account, args=(t, build_number), daemon=True) for t in tokens]
    for t in account_threads:
        t.start()
    logger.info(f'Running {len(account_threads)} account(s)')
    while running and any(t.is_alive() for t in account_threads):
        if stop_event.wait(1):
            break
    running = False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s', datefmt='%H:%M:%S')
    running = True
    stop_event.clear()
    main()