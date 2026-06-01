import requests
import base64
import json
import re
import random
import threading
import time
import traceback

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, List, Optional

from modules.utils.logger import get_logger # 
from modules.core.data_store import read_lines # 

logger = get_logger('discord_quest') # 

running = True

API_BASE = "https://discord.com/api/v9"
POLL_INTERVAL = 3600
HEARTBEAT_INTERVAL = 60
AUTO_ACCEPT = True
MAX_QUEST_WORKERS = 10
DEBUG = True

SUPPORTED_TASKS = [
    "WATCH_VIDEO",
    "PLAY_ON_DESKTOP",
    "STREAM_ON_DESKTOP",
    "PLAY_ACTIVITY",
    "WATCH_VIDEO_ON_MOBILE",
]

def log(msg: str) -> None:
    logger.info(msg) # 

def debug(msg: str) -> None:
    if DEBUG:
        logger.debug(msg) # 

def fetch_latest_build_number() -> int:
    FALLBACK = 504649
    try:
        log("Fetching latest build number from Discord...")
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        r = requests.get("https://discord.com/app", headers={"User-Agent": ua}, timeout=15)
        if r.status_code != 200:
            log(f"Could not fetch Discord page ({r.status_code}), using fallback")
            return FALLBACK

        scripts = re.findall(r'/assets/([a-f0-9]+)\.js', r.text)
        if not scripts:
            scripts_alt = re.findall(r'src="(/assets/[^"]+\.js)"', r.text)
            scripts = [s.split('/')[-1].replace('.js', '') for s in scripts_alt]
        if not scripts:
            log("No JS assets found, using fallback")
            return FALLBACK

        for asset_hash in scripts[-5:]:
            try:
                ar = requests.get(f"https://discord.com/assets/{asset_hash}.js",
                                  headers={"User-Agent": ua}, timeout=15)
                m = re.search(r'buildNumber["\s:]+["\s]*(\d{5,7})', ar.text)
                if m:
                    bn = int(m.group(1))
                    log(f"Build number: {bn}")
                    return bn
            except Exception:
                continue

        log(f"Build number not found, using fallback {FALLBACK}")
        return FALLBACK
    except Exception as e:
        log(f"Error fetching build number: {e}, using fallback {FALLBACK}")
        return FALLBACK

def make_super_properties(build_number: int) -> str:
    obj = {
        "os": "Windows",
        "browser": "Discord Client",
        "release_channel": "stable",
        "client_version": "1.0.9175",
        "os_version": "10.0.26100",
        "os_arch": "x64",
        "app_arch": "x64",
        "system_locale": "en-US",
        "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9175 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36",
        "browser_version": "32.2.7",
        "client_build_number": build_number,
        "native_build_number": 59498,
        "client_event_source": None,
    }
    return base64.b64encode(json.dumps(obj).encode()).decode()

def _get(d: Optional[dict], *keys) -> Any:
    if d is None:
        return None
    for k in keys:
        if k in d:
            return d[k]
    return None

def get_task_config(quest: dict) -> Optional[dict]:
    cfg = quest.get("config", {})
    return _get(cfg, "taskConfig", "task_config", "taskConfigV2", "task_config_v2")

def get_quest_name(quest: dict) -> str:
    cfg = quest.get("config", {})
    msgs = cfg.get("messages", {})
    name = _get(msgs, "questName", "quest_name")
    if name:
        return name.strip()
    game = _get(msgs, "gameTitle", "game_title")
    if game:
        return game.strip()
    app_name = cfg.get("application", {}).get("name")
    if app_name:
        return app_name
    return f"Quest#{quest.get('id', '?')}"

def get_expires_at(quest: dict) -> Optional[str]:
    cfg = quest.get("config", {})
    return _get(cfg, "expiresAt", "expires_at")

def get_user_status(quest: dict) -> dict:
    us = _get(quest, "userStatus", "user_status")
    return us if isinstance(us, dict) else {}

def is_completable(quest: dict) -> bool:
    expires = get_expires_at(quest)
    if expires:
        try:
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if exp_dt <= datetime.now(timezone.utc):
                return False
        except Exception:
            pass
    tc = get_task_config(quest)
    if not tc or "tasks" not in tc:
        return False
    tasks = tc["tasks"]
    return any(tasks.get(t) is not None for t in SUPPORTED_TASKS)

def is_enrolled(quest: dict) -> bool:
    us = get_user_status(quest)
    return bool(_get(us, "enrolledAt", "enrolled_at"))

def is_completed(quest: dict) -> bool:
    us = get_user_status(quest)
    return bool(_get(us, "completedAt", "completed_at"))

def get_task_type(quest: dict) -> Optional[str]:
    tc = get_task_config(quest)
    if not tc or "tasks" not in tc:
        return None
    for t in SUPPORTED_TASKS:
        if tc["tasks"].get(t) is not None:
            return t
    return None

def get_task_target(quest: dict, task_type: str) -> int:
    tc = get_task_config(quest)
    if tc and "tasks" in tc and task_type in tc["tasks"]:
        return tc["tasks"][task_type].get("target", 0)
    return 0

def get_task_progress(quest: dict, task_type: str) -> float:
    us = get_user_status(quest)
    progress = us.get("progress", {})
    if not progress:
        return 0.0
    return progress.get(task_type, {}).get("value", 0.0)

def get_enrolled_at(quest: dict) -> Optional[str]:
    us = get_user_status(quest)
    return _get(us, "enrolledAt", "enrolled_at")

class DiscordAPI:
    def __init__(self, token: str, build_number: int):
        self.token = token
        self.session = requests.Session()
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9175 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36"
        sp = make_super_properties(build_number)
        self.session.headers.update({
            "Authorization": token,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": ua,
            "X-Super-Properties": sp,
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "Asia/Ho_Chi_Minh",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/channels/@me",
        })

    def get(self, path: str, **kwargs) -> requests.Response:
        debug(f"GET {path}")
        r = self.session.get(f"{API_BASE}{path}", **kwargs)
        debug(f"  -> {r.status_code} ({len(r.content)} bytes)")
        return r

    def post(self, path: str, payload: Optional[dict] = None, **kwargs) -> requests.Response:
        debug(f"POST {path}")
        r = self.session.post(f"{API_BASE}{path}", json=payload, **kwargs)
        debug(f"  -> {r.status_code} ({len(r.content)} bytes)")
        return r

    def validate_token(self) -> bool:
        try:
            r = self.get("/users/@me")
            if r.status_code == 200:
                user = r.json()
                log(f"Logged in as {user['username']} (ID: {user['id']})")
                return True
            else:
                log(f"Token invalid (status {r.status_code})")
                return False
        except Exception as e:
            log(f"Connection to Discord failed: {e}")
            return False

class QuestAutocompleter:
    def __init__(self, api: DiscordAPI):
        self.api = api
        self.completed_ids: set = set()
        self.in_progress_ids: set = set()
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=MAX_QUEST_WORKERS)

    def fetch_quests(self) -> List[dict]:
        while True:
            if not running:
                return []
            try:
                r = self.api.get("/quests/@me")
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, dict):
                        quests = data.get("quests", [])
                        blocked = _get(data, "quest_enrollment_blocked_until")
                        if blocked:
                            log(f"Enrollment blocked until: {blocked}")
                        return quests
                    elif isinstance(data, list):
                        return data
                    return []
                elif r.status_code == 429:
                    retry_after = r.json().get("retry_after", 10)
                    log(f"Rate limited on fetch – waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue
                else:
                    log(f"Quest fetch error ({r.status_code}): {r.text[:200]}")
                    return []
            except Exception as e:
                log(f"Error fetching quests: {e}")
                if DEBUG:
                    traceback.print_exc()
                return []

    def enroll_quest(self, quest: dict) -> bool:
        name = get_quest_name(quest)
        qid = quest["id"]
        for attempt in range(1, 4):
            try:
                payload = {
                    "location": 11,
                    "is_targeted": False,
                    "metadata_raw": None,
                    "metadata_sealed": None,
                    "traffic_metadata_raw": quest.get("traffic_metadata_raw"),
                    "traffic_metadata_sealed": quest.get("traffic_metadata_sealed"),
                }
                r = self.api.post(f"/quests/{qid}/enroll", payload)
                if r.status_code == 429:
                    retry_after = r.json().get("retry_after", 5)
                    wait = retry_after + 1
                    log(f"Rate limited on enroll \"{name}\" (attempt {attempt}/3) – waiting {wait}s")
                    time.sleep(wait)
                    continue
                if r.status_code in (200, 201, 204):
                    log(f"Enrolled: {name}")
                    return True
                log(f"Enroll \"{name}\" failed ({r.status_code}): {r.text[:200]}")
                return False
            except Exception as e:
                log(f"Enroll error \"{name}\": {e}")
                return False
        log(f"Skipping \"{name}\" after 3 rate limit hits")
        return False

    def auto_accept(self, quests: List[dict]) -> List[dict]:
        if not AUTO_ACCEPT:
            return quests
        unaccepted = [q for q in quests if not is_enrolled(q) and not is_completed(q) and is_completable(q)]
        if not unaccepted:
            return quests
        log(f"Found {len(unaccepted)} quest(s) to auto-accept")
        for q in unaccepted:
            self.enroll_quest(q)
            time.sleep(3)
        time.sleep(2)
        return self.fetch_quests()

    def _heartbeat_loop(self, quest: dict, stream_key: str, task_type: str):
        name = get_quest_name(quest)
        qid = quest["id"]
        seconds_needed = get_task_target(quest, task_type)
        seconds_done = get_task_progress(quest, task_type)
        remaining = max(0, seconds_needed - seconds_done)
        log(f"[{task_type}] {name} (~{remaining // 60} min left)")

        while seconds_done < seconds_needed:
            if qid in self.completed_ids:
                debug(f"Quest {qid} already completed, stopping heartbeat")
                return
            try:
                r = self.api.post(f"/quests/{qid}/heartbeat", {
                    "stream_key": stream_key,
                    "terminal": False,
                })
                if r.status_code == 200:
                    body = r.json()
                    progress_data = body.get("progress", {})
                    if progress_data and task_type in progress_data:
                        seconds_done = progress_data[task_type].get("value", seconds_done)
                    log(f"[{name}] {seconds_done:.0f}/{seconds_needed}s")
                    if body.get("completed_at") or seconds_done >= seconds_needed:
                        log(f"Completed: {name}")
                        with self.lock:
                            self.completed_ids.add(qid)
                        return
                elif r.status_code == 429:
                    retry_after = r.json().get("retry_after", 10)
                    log(f"Rate limited on heartbeat – waiting {retry_after + 1}s")
                    time.sleep(retry_after + 1)
                    continue
                else:
                    log(f"Heartbeat error ({r.status_code}): {r.text[:200]}")
            except Exception as e:
                log(f"Heartbeat exception: {e}")
            time.sleep(HEARTBEAT_INTERVAL)

        try:
            self.api.post(f"/quests/{qid}/heartbeat", {
                "stream_key": stream_key,
                "terminal": True,
            })
        except Exception:
            pass
        log(f"Completed: {name}")
        with self.lock:
            self.completed_ids.add(qid)

    def complete_video(self, quest: dict):
        name = get_quest_name(quest)
        qid = quest["id"]
        task_type = get_task_type(quest)
        seconds_needed = get_task_target(quest, task_type)
        seconds_done = get_task_progress(quest, task_type)
        enrolled_at_str = get_enrolled_at(quest)
        enrolled_ts = (
            datetime.fromisoformat(enrolled_at_str.replace("Z", "+00:00")).timestamp()
            if enrolled_at_str else time.time()
        )

        log(f"[Video] {name} ({seconds_done:.0f}/{seconds_needed}s)")
        max_future = 10
        speed = 7
        interval = 1

        while seconds_done < seconds_needed:
            if qid in self.completed_ids:
                debug(f"Quest {qid} already completed, stopping video loop")
                return
            max_allowed = (time.time() - enrolled_ts) + max_future
            diff = max_allowed - seconds_done
            timestamp = seconds_done + speed

            if diff >= speed:
                try:
                    r = self.api.post(f"/quests/{qid}/video-progress", {
                        "timestamp": min(seconds_needed, timestamp + random.random())
                    })
                    if r.status_code == 200:
                        body = r.json()
                        if body.get("completed_at"):
                            log(f"Completed: {name}")
                            with self.lock:
                                self.completed_ids.add(qid)
                            return
                        seconds_done = min(seconds_needed, timestamp)
                        log(f"[{name}] {seconds_done:.0f}/{seconds_needed}s")
                    elif r.status_code == 429:
                        retry_after = r.json().get("retry_after", 5)
                        log(f"Rate limited on video progress – waiting {retry_after + 1}s")
                        time.sleep(retry_after + 1)
                        continue
                    else:
                        log(f"Video progress error ({r.status_code}): {r.text[:200]}")
                except Exception as e:
                    log(f"Video progress exception: {e}")
            if timestamp >= seconds_needed:
                break
            time.sleep(interval)

        try:
            self.api.post(f"/quests/{qid}/video-progress", {"timestamp": seconds_needed})
        except Exception:
            pass
        log(f"Completed: {name}")
        with self.lock:
            self.completed_ids.add(qid)

    def process_quest(self, quest: dict):
        name = get_quest_name(quest)
        task_type = get_task_type(quest)

        if not task_type:
            log(f"{name} – unsupported task, skipping")
            return

        log(f"Starting: {name} (task: {task_type})")

        if task_type in ("WATCH_VIDEO", "WATCH_VIDEO_ON_MOBILE"):
            self.complete_video(quest)
        elif task_type in ("PLAY_ON_DESKTOP", "STREAM_ON_DESKTOP"):
            pid = random.randint(1000, 30000)
            self._heartbeat_loop(quest, f"call:0:{pid}", task_type)
        elif task_type == "PLAY_ACTIVITY":
            self._heartbeat_loop(quest, "call:0:1", "PLAY_ACTIVITY")

    def _process_and_cleanup(self, quest: dict):
        qid = quest["id"]
        try:
            self.process_quest(quest)
        except Exception as e:
            log(f"Unexpected error processing quest {qid}: {e}")
            if DEBUG:
                traceback.print_exc()
        finally:
            with self.lock:
                self.in_progress_ids.discard(qid)

    def run(self):
        cycle = 0
        while running:
            cycle += 1
            log(f"--- Scan {cycle} ---")
            quests = self.fetch_quests()
            if not quests:
                log("No quests available")
            else:
                enrolled_count = sum(1 for q in quests if is_enrolled(q))
                completed_count = sum(1 for q in quests if is_completed(q))
                completable_count = sum(1 for q in quests if is_completable(q))
                log(f"Total: {len(quests)} | Enrolled: {enrolled_count} | Completed: {completed_count} | Completable: {completable_count}")

                quests = self.auto_accept(quests)

                with self.lock:
                    actionable = [
                        q for q in quests
                        if is_enrolled(q) and not is_completed(q) and is_completable(q)
                        and q["id"] not in self.completed_ids
                        and q["id"] not in self.in_progress_ids
                    ]

                if actionable:
                    log(f"Starting {len(actionable)} quest(s) in parallel")
                    for q in actionable:
                        qid = q["id"]
                        with self.lock:
                            if qid not in self.in_progress_ids:
                                self.in_progress_ids.add(qid)
                                self.executor.submit(self._process_and_cleanup, q)
                else:
                    log("No quests need completion right now")

            log(f"Waiting {POLL_INTERVAL}s before next scan...")
            time.sleep(POLL_INTERVAL)

def run_account(token: str, build_number: int):
    api = DiscordAPI(token, build_number)
    if not api.validate_token():
        log("Skipping account – token validation failed")
        return
    completer = QuestAutocompleter(api)
    completer.run()

def main():
    tokens = read_lines('data/discord_quest.txt') # 
    if not tokens: return

    log(f"Loaded {len(tokens)} token(s)")
    build_number = fetch_latest_build_number()

    threads = []
    for token in tokens:
        t = threading.Thread(target=run_account, args=(token, build_number), daemon=True)
        t.start()
        threads.append(t)

    log(f"Running {len(tokens)} account(s)")
    while running and any(t.is_alive() for t in threads):
        time.sleep(1)

if __name__ == "__main__":
    main()