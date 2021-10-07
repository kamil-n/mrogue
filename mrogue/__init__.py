# -*- coding: utf-8 -*-
"""Package containing all the components required to run the game.

Modules:
    * effects - handling of on-use effects from consumables
    * io - layer on top of libTCOD wrapper, handling keyboard input and SDL emulated terminal output
    * item - items usable by player - wearable and/or consumable
    * item_data - several type definitions as well as a list of all item blueprints
    * map - creates a map to traverse and provides helper functions like pathfinding and line of sight
    * message - for communicating the state of the game to the player
    * monster - monster handler class and monster class definition
    * monster_data - blueprints for monster types
    * player - holds player stats and provides several unique functions
    * timers - for tracking time flow
    * unit - base mobile entity definition
    * utils - several smaller functions (i.e. random number generators, text utils
"""
import sys
from collections import namedtuple
from os import path


__author__ = 'Kamil Nienałtowski'
__copyright__ = 'Copyright (C) 2018-2021 Kamil Nienałtowski'
__license__ = 'GPL-3.0-or-later'
__version__ = 'v0.6.23'

if getattr(sys, 'frozen', False):
    work_dir = path.dirname(sys.executable)
else:
    work_dir = path.dirname(path.dirname(__file__))

Point = namedtuple('Point', ('x', 'y'))

from mrogue.io import Glyph


class Entity(io.Glyph):
    """Implements group membership for the extending classes, similar to how PyGame does it.

    Useful for organising entities by their location or function.
    Allows for easy removal of the entity from all groups, effectively removing it from game.
    """

    def __init__(self):
        super().__init__()
        self._groups = []

    def add(self, *groups: list) -> None:
        """Assign this object to one or more groups, adding internal reference(s) to those groups.
        Usage: obj.add(a_group, another_group)

        :param groups: one or more groups (lists)
        """
        for group in groups:
            if group is not None:
                group.append(self)
                if group not in self._groups:
                    self._groups.append(group)

    def remove(self, *groups: list) -> None:
        """Remove this object from one on more groups.
        Usage: obj.remove(a_group, another_group)

        :param groups: one or more groups (lists)
        """
        for group in groups:
            if self in group:
                group.remove(self)
            if group in self._groups:
                self._groups.remove(group)

    def kill(self) -> None:
        """Destroy all relationships between this object and any group."""
        for group in self._groups:
            group.remove(self)
            self._groups.remove(group)
