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