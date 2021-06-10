import sys
import os


class _Tee(object):
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()


class PrintRedirector:
    def __init__(self, path):
        self._path = path
        self.__open()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__close()

    def __open(self):
        self._orig_stdout = sys.stdout
        dir = os.path.dirname(self._path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        self.__f = open(self._path, 'w')
        sys.stdout = _Tee(self.__f, sys.stdout)

    def __close(self):
        sys.stdout = self._orig_stdout
        self.__f.close()