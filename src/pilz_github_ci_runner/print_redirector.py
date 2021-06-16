# Copyright (c) 2021 Pilz GmbH & Co. KG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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