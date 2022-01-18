from pathlib import Path

from dictum.model import Model


class StoreProxy:
    """An interface to the store. It is either cached (read only once on creation)
    or re-read if changed.
    """

    def __init__(self, path: str, cache: bool = True):
        self._path = Path(path)
        self._mtime = self._path.stat().st_mtime
        self._store = Model.from_yaml(path)
        self._cache = cache

    def __getattr__(self, key):
        return getattr(self.store, key)

    @property
    def store(self):
        if self._cache is not True:
            mtime = self._path.stat().st_mtime
            if mtime > self._mtime:
                self._mtime = mtime
                self._store = Model.from_yaml(self._path)
            return self._store
        return Model.from_yaml(self.config_path)
