from modules.core.data_store import read_json, write_json
from modules.utils.captcha_store import CaptchaStore

def migrate_owo_data():
    existing = read_json('data/owo.json', None)
    if isinstance(existing, dict):
        CaptchaStore.normalize()
        return existing

    accounts = {}
    write_json('data/owo.json', accounts)
    CaptchaStore.normalize()
    return accounts
