# -*- coding: utf-8 -*-

import tcod


class Char(object):
    def __init__(self):
        self.icon = ''
        self.color = tcod.white
        self._groups = []

    def add(self, *groups):
        for group in groups:
            group.append(self)
            if not group in self._groups:
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