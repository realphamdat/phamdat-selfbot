class BotRegistry:
    def __init__(self):
        self._factories = {}

    def register(self, name, factory, defaults=None):
        self._factories[name] = {'factory': factory, 'defaults': defaults or {}}

    def names(self):
        return list(self._factories)

    def get(self, name):
        return self._factories.get(name)

    def create_client(self, name, **kwargs):
        entry = self.get(name)
        if not entry:
            raise KeyError(f'Bot is not registered: {name}')
        return entry['factory'](**kwargs)

    def defaults(self, name):
        entry = self.get(name)
        return entry['defaults'] if entry else {}
