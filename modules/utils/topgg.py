import os
import re
import sys
import threading
import time

from urllib.parse import urlparse
from curl_cffi import requests as curl
from DrissionPage import ChromiumOptions, ChromiumPage

from modules.utils.logger import get_logger

logger = get_logger('top.gg')

_lock = threading.Lock()
_stop = threading.Event()

BROWSERS = [
    ('chrome-win64', 'chrome.exe'),
    ('chrome-win32', 'chrome.exe'),
    ('chrome-linux64', 'chrome'),
    ('chrome-linux', 'chrome'),
    ('chrome-mac-arm64', 'Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'),
    ('chrome-mac-x64', 'Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'),
]

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0'

ALREADY_VOTED = 'you have already voted'
VOTED_OK = 'thanks for voting'

_CLICK_DISCORD = ('document.querySelectorAll("button").forEach(e=>{'
                  'let t=(e.textContent||"").trim().toLowerCase();'
                  'if(t==="login with discord")e.click();});')


def stop():
    _stop.set()


def clear_stop():
    _stop.clear()


def find_browser():
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    for folder, binary in BROWSERS:
        path = os.path.join(base, folder, binary)
        if os.path.isfile(path):
            return path
    return None


def _page_text(page):
    try:
        element = page.ele('tag:body')
        return (element.text or '').lower() if element else ''
    except Exception:
        return ''


def _retry_seconds(page):
    match = re.search(r'every\s+(\d+)\s+hours?', _page_text(page))
    return int(match.group(1)) * 3600 if match else 0


def _wait_url(page, text, timeout):
    for _ in range(timeout):
        if _stop.is_set():
            return False
        if text in page.url:
            return True
        time.sleep(0.5)
    return False


def _dismiss_consent(page):
    try:
        agree = page.ele('xpath://button[normalize-space(text())="AGREE"]', timeout=1)
        if agree is not None:
            agree.click()
            return True
    except Exception:
        pass
    return False


def _top_text_at(page, button):
    try:
        x, y = button.rect.midpoint
        return page.run_js(
            'var e=document.elementFromPoint(arguments[0], arguments[1]);'
            'return e ? (e.textContent || "").trim().toLowerCase() : "";',
            int(x), int(y))
    except Exception:
        return ''


def _click_vote(page):
    for _ in range(60):
        if _stop.is_set():
            return False
        text = _page_text(page)
        if ALREADY_VOTED in text:
            logger.info('Already voted')
            return 'already'
        _dismiss_consent(page)
        try:
            button = page.ele('css:button.button-primary', timeout=1)
            ready = button is not None and button.states.is_enabled \
                and (button.text or '').strip().lower() == 'vote'
        except Exception:
            ready = False
        if not ready:
            time.sleep(1)
            continue
        _dismiss_consent(page)
        time.sleep(0.5)
        try:
            button = page.ele('css:button.button-primary', timeout=1)
        except Exception:
            continue
        if 'vote' not in _top_text_at(page, button):
            time.sleep(0.5)
            continue
        try:
            button.click()
            logger.info('Vote button clicked')
            return True
        except Exception:
            return False
    logger.error('Vote button never became ready')
    return False


def _wait_outcome(page):
    for _ in range(15):
        if _stop.is_set():
            return 0
        time.sleep(1)
        text = _page_text(page)
        if VOTED_OK in text:
            retry = _retry_seconds(page)
            if retry:
                logger.info(f'Voted (next in {retry}s)')
            else:
                logger.warning('Voted but retry time not found on page')
            return retry
        if ALREADY_VOTED in text:
            logger.info('Already voted')
            return 0
    logger.warning('No confirmation after clicking vote')
    return 0


def _vote(bot_id, token):
    path = find_browser()
    if not path:
        logger.error('Browser not found for voting')
        return 0
    logger.info(f'Voting for bot {bot_id}')

    vote_url = f'https://top.gg/bot/{bot_id}/vote'
    login_url = f'https://top.gg/auth/login?redir=%2Fbot%2F{bot_id}%2Fvote'

    page = ChromiumPage(ChromiumOptions().set_browser_path(path).auto_port())
    try:
        for attempt in range(3):
            if _stop.is_set():
                return 0
            logger.info(f'Login attempt {attempt + 1}/3')
            page.get(login_url)
            if not page.wait.ele_displayed('xpath://button[contains(., "Login with Discord")]', timeout=25):
                continue
            page.run_js(_CLICK_DISCORD)
            if _wait_url(page, 'discord.com/oauth2/authorize', 30):
                break
        auth = page.url
        if 'discord.com/oauth2/authorize' not in auth:
            logger.error('No oauth url')
            return 0
        logger.info('Discord authorize ok')

        response = curl.post(
            'https://discord.com/api/v9/oauth2/authorize?' + urlparse(auth).query,
            headers={'User-Agent': USER_AGENT, 'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.5',
                     'Content-Type': 'application/json', 'Origin': 'https://discord.com',
                     'Referer': auth, 'Authorization': token,
                     'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin'},
            json={'permissions': '0', 'authorize': True}, impersonate='chrome', timeout=30)
        if response.status_code != 200:
            logger.error(f'Consent failed ({response.status_code})')
            return 0
        logger.info('Oauth consent ok')

        if _stop.is_set():
            return 0
        page.get(response.json()['location'])
        page.wait.doc_loaded(timeout=20)
        if _stop.is_set():
            return 0
        page.get(vote_url)
        page.wait.doc_loaded(timeout=20)
        logger.info('On vote page')

        result = _click_vote(page)
        if result == 'already':
            return 0
        if result is not True:
            logger.error('Could not click vote button')
            return 0
        logger.info('Clicked, waiting for confirmation')
        return _wait_outcome(page)
    finally:
        try:
            page.quit()
        except Exception:
            pass


def vote(bot_id, token):
    with _lock:
        if _stop.is_set():
            logger.warning('Skipped (stop requested)')
            return 0
        return _vote(bot_id, token)