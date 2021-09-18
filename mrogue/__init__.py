# -*- coding: utf-8 -*-

import sys
from os import path
from mrogue.io import Glyph

__version__ = 'v0.6.2'

if getattr(sys, 'frozen', False):
    work_dir = path.dirname(sys.executable)
else:
    work_dir = path.dirname(path.dirname(__file__))


class Entity(io.Glyph):
    def __init__(self):
        super().__init__()
        self._groups = []

    def add(self, *groups):
        for group in groups:
            if group is not None:
                group.append(self)
                if group not in self._groups:
                    self._groups.append(group)

    def remove(self, *groups):
        for group in groups:
            if self in group:
                group.remove(self)
            if group in self._groups:
                self._groups.remove(group)

    def kill(self):
        for group in self._groups:
            group.remove(self)
            self._groups.remove(group)
