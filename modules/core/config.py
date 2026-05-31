from copy import deepcopy

def deep_merge(defaults, user_config):
    base = deepcopy(defaults or {})
    if not isinstance(user_config, dict):
        return base

    for key, value in user_config.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = deepcopy(value)
    return base

def get_section(config, key, default=None):
    value = config.get(key, default or {})
    return value if isinstance(value, dict) else (default or {})

def get_bool(config, key, default=False):
    value = config.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)

def get_int(config, key, default=0):
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default

def get_float(config, key, default=0.0):
    try:
        return float(config.get(key, default))
    except (TypeError, ValueError):
        return default

def get_range(config, key, default_min=0, default_max=0, as_float=False):
    data = get_section(config, key, {'min': default_min, 'max': default_max})
    getter = get_float if as_float else get_int
    return getter(data, 'min', default_min), getter(data, 'max', default_max)
