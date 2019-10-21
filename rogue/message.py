# -*- coding: utf-8 -*-

import logging
from rogue.curse import CursesHelper as Curses


class Messenger:
    _instance = None
    messageList = []
    scrDim = tuple()

    def __init__(self, screen_dim):
        self.messageList = []
        Messenger._instance = self
        self.scrDim = screen_dim

    def show(self, message_line):
        # TODO: zrobic to w nowym oknie
        if len(self.messageList) > 1:
            while len(self.messageList) > 0:
                temp_message = ''
                while (self.scrDim[0] - 7 - len(temp_message)) >\
                        len(self.messageList[0]):
                    temp_message += self.messageList.pop(0) + ' '
                    if len(self.messageList) == 0:
                        break
                logging.debug('temp_message = %s' % temp_message)
                message_end = len(temp_message)
                Curses.print_at(0,
                                message_line,
                                temp_message,
                                Curses.color('WHITE'))
                if len(self.messageList) > 0:
                    logging.debug('still messages left.')
                    Curses.print_at(message_end,
                                    message_line,
                                    '-more-',
                                    Curses.color('YELLOW'))
                    Curses.wait()
                    Curses.print_at(0, message_line, (self.scrDim[0] - 1) * ' ')
                Curses.refresh()
        elif len(self.messageList) == 1:
            Curses.print_at(0,
                            message_line,
                            self.messageList[0],
                            Curses.color('WHITE'))
            Curses.refresh()

    @classmethod
    def add(cls, message):
        cls._instance.messageList.append(message)

    def clear(self, message_line):
        Curses.print_at(0, message_line, (self.scrDim[0] - 1) * ' ')
        Curses.refresh()
        del self.messageList[:]
