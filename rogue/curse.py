# -*- coding: utf-8 -*-

import curses


class CursesHelper(object):
    stdscr = None
    colors = None
    dimensions = None
    status_line = 0
    message_line = 23

    def __init__(self):
        self.stdscr = curses.initscr()
        self.dimensions = self.stdscr.getmaxyx()
        self.message_line = self.dimensions[0] - 1
        curses.curs_set(False)
        curses.noecho()
        self.stdscr.keypad(1)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_BLACK)
        self.colors = {
            'WHITE': curses.color_pair(0) | curses.A_BOLD,
            'GRAY': curses.color_pair(0),
            'RED': curses.color_pair(1) | curses.A_BOLD,
            'DARKRED': curses.color_pair(1),
            'GREEN': curses.color_pair(2) | curses.A_BOLD,
            'DARKGREEN': curses.color_pair(2),
            'BLUE': curses.color_pair(3) | curses.A_BOLD,
            'DARKBLUE': curses.color_pair(3),
            'LIGHTBLUE': curses.color_pair(4) | curses.A_BOLD,
            'AQUAMARINE': curses.color_pair(4),
            'PURPLE': curses.color_pair(5) | curses.A_BOLD,
            'DARKPURPLE': curses.color_pair(5),
            'YELLOW': curses.color_pair(6) | curses.A_BOLD,
            'BROWN': curses.color_pair(6),
            'DARKGRAY': curses.color_pair(7) | curses.A_BOLD
        }

    def print_at(self, x, y, string, decoration=None, window=None):
        if decoration is None:  # because 0 (valid int arg) evaluates to False
            decoration = self.colors['DARKGRAY']
        if not window:
            window = self.stdscr
        try:
            window.addstr(y, x, string, decoration)
        except curses.error:
            # import logging
            # logging.error('Error when drawing "{}" at coords {}, {}!'.format(
            #    string, x, y))
            # raise
            pass

    def wait(self, character=None, window=None):
        if not window:
            window = self.stdscr
        key = 1
        if key:
            while key != ord(character):
                key = window.getch()
        else:
            window.getch()

    def refresh(self):
        self.stdscr.refresh()

    def close(self):
        curses.curs_set(True)
        curses.echo()
        self.stdscr.keypad(0)
        curses.endwin()


class CursesWindow(object):
    window = None

    def __init__(self, curs, left=1, top=1, width=20, height=4,
                 title='Window title', title_color='GRAY', bg_attr='GRAY'):
        self.window = curses.newwin(height, width, top, left)
        self.window.bkgdset(' ', curs.colors[bg_attr])  # bkgdset
        self.window.addstr(1, 2, title, curs.colors[title_color])
        self.window.border(0, 0, 0, 0, 0, 0, 0, 0)
        self.window.addch(2, 0, curses.ACS_LTEE)
        self.window.hline(2, 1, curses.ACS_BSBS, width - 2)
        self.window.addch(2, width - 1, curses.ACS_RTEE)
        self.window.addch(0, width - 2, 'q')
        self.window.refresh()

    def set_border(self, ls=0, rs=0, ts=0, bs=0, tl=0, tr=0, bl=0, br=0):
        self.window.border(ls, rs, ts, bs, tl, tr, bl, br)
        self.window.refresh()

    def loop(self):
        key = 1
        while key != ord('q'):
            key = self.window.getch()

    def close(self):
        del self.window
