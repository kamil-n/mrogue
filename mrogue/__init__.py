# -*- coding: utf-8 -*-

from mrogue.io import Glyph

__version__ = 'v0.5.2'


def cap(word):
    return word[0].upper() + word[1:]


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
