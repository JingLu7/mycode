class KVStore:
    def __init__(self):
        self._store = {}

    def set(self, key, value):
        self._store[key] = value

    def get(self, key):
        return self._store.get(key)

    def delete(self, key):
        if key in self._store:
            del self._store[key]

    def exists(self, key):
        return key in self._store

    def keys(self):
        return list(self._store.keys())