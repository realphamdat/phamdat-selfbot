import time

from modules.core.data_store import read_json, write_json

class CaptchaStore:
    PATH = 'data/caches.json'

    @staticmethod
    def load():
        data = read_json(CaptchaStore.PATH, {'captchas': {}}) or {'captchas': {}}
        captchas = data.get('captchas', {})
        if isinstance(captchas, list):
            data['captchas'] = {'owo': captchas}
        elif not isinstance(captchas, dict):
            data['captchas'] = {}
        return data

    @staticmethod
    def save(data):
        write_json(CaptchaStore.PATH, data)

    @staticmethod
    def list(bot=None):
        data = CaptchaStore.load()
        captchas = data.get('captchas', {})
        if bot:
            return list(captchas.get(bot, []))

        all_items = []
        for items in captchas.values():
            all_items.extend(items)
        return all_items

    @staticmethod
    def count(bot=None):
        return len(CaptchaStore.list(bot))

    @staticmethod
    def add(bot, payload):
        data = CaptchaStore.load()
        data.setdefault('captchas', {}).setdefault(bot, []).append(payload)
        CaptchaStore.save(data)
        return payload

    @staticmethod
    def find(bot, captcha_id):
        for captcha in CaptchaStore.list(bot):
            if captcha.get('id') == captcha_id:
                return captcha

    @staticmethod
    def update(bot, captcha_id, patch):
        data = CaptchaStore.load()
        items = data.setdefault('captchas', {}).setdefault(bot, [])
        for captcha in items:
            if captcha.get('id') == captcha_id:
                captcha.update(patch)
                captcha['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                CaptchaStore.save(data)
                return captcha

    @staticmethod
    def remove(bot, captcha_id):
        data = CaptchaStore.load()
        items = data.setdefault('captchas', {}).setdefault(bot, [])
        kept = [item for item in items if item.get('id') != captcha_id]
        removed = len(items) - len(kept)
        data['captchas'][bot] = kept
        CaptchaStore.save(data)
        return removed > 0

    @staticmethod
    def normalize():
        data = CaptchaStore.load()
        CaptchaStore.save(data)
        return data
