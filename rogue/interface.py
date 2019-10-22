# -*- coding: utf-8 -*-

import curses
import rogue.curse


class Interface(rogue.curse.CursesHelper):
    _impl = 'Curses'


class Window(rogue.curse.CursesWindow):
    _impl = 'Curses'


class Arrows(object):
    UP = curses.KEY_UP
    DOWN = curses.KEY_DOWN
    LEFT = curses.KEY_LEFT
    RIGHT = curses.KEY_RIGHT
