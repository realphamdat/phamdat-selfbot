import json
import os
import tempfile

from modules.utils.logger import get_logger

logger = get_logger('data_store')

def read_text(path, default=''):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return default
    except Exception:
        logger.exception(f'Failed to read text file: {path}')
        return default

def write_text(path, content):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def read_lines(path):
    text = read_text(path, '')
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]

def read_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        logger.exception(f'Invalid JSON file: {path}')
        return default
    except Exception:
        logger.exception(f'Failed to read JSON file: {path}')
        return default

def write_json(path, data):
    folder = os.path.dirname(path) or '.'
    os.makedirs(folder, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix='.tmp-', suffix='.json', dir=folder, text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.write('\n')
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        logger.exception(f'Failed to write JSON file: {path}')
        raise

def validate_json_text(content):
    return json.loads(content)
