from time import time


class Cache:
    def __init__(self):
        self._store = {}

    def init_app(self, app):
        return None

    def get(self, key):
        item = self._store.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at is not None and expires_at < time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key, value, timeout=None):
        expires_at = None
        if timeout is not None:
            expires_at = time() + timeout
        self._store[key] = (value, expires_at)

    def clear(self):
        self._store.clear()


cache = Cache()
