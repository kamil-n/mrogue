# -*- coding: utf-8 -*-

import logging


class Messenger(object):
    messageList = []
    game = None
    scrDim = tuple()

    def __init__(self, game):
        self.messageList = []
        self.game = game
        self.scrDim = (game.interface.dimensions[1],
                       game.interface.dimensions[0])

    def show(self):
        # TODO: zrobic to w nowym oknie
        if len(self.messageList) > 1:
            while len(self.messageList) > 0:
                temp_message = ''
                while (self.scrDim[0] - 7 - len(temp_message)) > \
                        len(self.messageList[0]):
                    temp_message += self.messageList.pop(0) + ' '
                    if len(self.messageList) == 0:
                        break
                logging.debug('temp_message = %s' % temp_message)
                message_end = len(temp_message)
                self.game.interface.print_at(0,
                                             self.game.interface.message_line,
                                             temp_message,
                                             self.game.interface.colors[
                                                 'WHITE'])
                if len(self.messageList) > 0:
                    logging.debug('still messages left.')
                    self.game.interface.print_at(message_end,
                                                 self.game.interface.message_line,
                                                 '-more-',
                                                 self.game.interface.colors[
                                                     'YELLOW'])
                    self.game.interface.wait()
                    self.game.interface.print_at(0,
                                                 self.game.interface.message_line,
                                                 (self.scrDim[0] - 1) * ' ')
                self.game.interface.refresh()
        elif len(self.messageList) == 1:
            self.game.interface.print_at(0,
                                         self.game.interface.message_line,
                                         self.messageList[0],
                                         self.game.interface.colors[
                                             'WHITE'])
            self.game.interface.refresh()

    def add(self, message):
        self.messageList.append(message)

    def clear(self):
        self.game.interface.print_at(0, self.game.interface.message_line,
                                     (self.scrDim[0] - 1) * ' ')
        self.game.interface.refresh()
        del self.messageList[:]
