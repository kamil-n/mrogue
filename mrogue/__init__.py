# -*- coding: utf-8 -*-
import sys
from collections import namedtuple
from dataclasses import dataclass
from os import path

__author__ = "Kamil Nienałtowski"
__copyright__ = "Copyright (C) 2018-2021 Kamil Nienałtowski"
__license__ = "GPL-3.0-or-later"
__version__ = "v0.8.3"

if getattr(sys, "frozen", False):
    work_dir = path.dirname(sys.executable)
else:
    work_dir = path.dirname(path.dirname(__file__))

Point = namedtuple("Point", ("x", "y"))


@dataclass
class Glyph:
    icon: int = 0
    color: tuple[int, ...] = (255, 255, 255)
    fg_alpha: int = 255
    background: tuple[int, ...] = (0, 0, 0)
    bg_alpha: int = 255

    @property
    def tile(self) -> tuple[int, tuple[int, ...], tuple[int, ...]]:
        return (
            self.icon,
            (*self.color, self.fg_alpha),
            (*self.background, self.bg_alpha),
        )

    @tile.setter
    def tile(
        self,
        tile_tuple: tuple[int, tuple[int, ...], tuple[int, ...]],
    ) -> None:
        self.icon = tile_tuple[0]
        self.color = tile_tuple[1][:3]
        self.fg_alpha = tile_tuple[1][3]
        self.background = tile_tuple[2][:3]
        self.bg_alpha = tile_tuple[2][3]


class Entity(Glyph):
    def __init__(self) -> None:
        super().__init__()
        self._groups: list[list[Entity]] = []

    def add(self, *groups: list["Entity"]) -> None:
        for group in groups:
            if group is not None:
                group.append(self)
                if group not in self._groups:
                    self._groups.append(group)

    def remove(self, *groups: list["Entity"]) -> None:
        for group in groups:
            if self in group:
                group.remove(self)
            if group in self._groups:
                self._groups.remove(group)

    def kill(self) -> None:
        for group in self._groups:
            group.remove(self)
            self._groups.remove(group)
