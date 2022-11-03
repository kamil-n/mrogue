# -*- coding: utf-8 -*-
import sys
from collections import namedtuple
from os import path

from mrogue.io import Glyph

__author__ = "Kamil Nienałtowski"
__copyright__ = "Copyright (C) 2018-2021 Kamil Nienałtowski"
__license__ = "GPL-3.0-or-later"
__version__ = "v0.8.3"

if getattr(sys, "frozen", False):
    work_dir = path.dirname(sys.executable)
else:
    work_dir = path.dirname(path.dirname(__file__))

Point = namedtuple("Point", ("x", "y"))


class Entity(Glyph):
    def __init__(self):
        super().__init__()
        self._groups = []

    def add(self, *groups: list) -> None:
        for group in groups:
            if group is not None:
                group.append(self)
                if group not in self._groups:
                    self._groups.append(group)

    def remove(self, *groups: list) -> None:
        for group in groups:
            if self in group:
                group.remove(self)
            if group in self._groups:
                self._groups.remove(group)

    def kill(self) -> None:
        for group in self._groups:
            group.remove(self)
            self._groups.remove(group)
