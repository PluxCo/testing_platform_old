import json
import os


class Settings(dict):
    def __init__(self):
        super().__init__()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Settings, cls).__new__(cls)
        return cls.instance

    def setup(self, filename, default_values: dict):
        self.file = filename
        self._update_handlers = []

        for k, v in default_values.items():
            self.setdefault(k, v)

        if not os.path.exists(filename):
            with open(filename, "w") as file:
                json.dump(dict(), file)

        with open(filename, "rb") as file:
            self.update(json.load(file))

    def update_settings(self):
        with open(self.file, "w") as file:
            json.dump(self.copy(), file)
        for handler in self._update_handlers:
            handler()

    def add_update_handler(self, handler):
        if hasattr(self, "_update_handlers"):
            self._update_handlers.append(handler)
        else:
            self._update_handlers = [handler]
