# -*- coding: utf-8 -*-

from mrogue import wait
from textwrap import wrap
import tcod.console


class Messenger(object):
    messageList = []

    def __init__(self, game):
        self.game = game
        self.window = tcod.console.Console(game.screen.width, 1)

    def show(self):
        buffer = wrap(' '.join(self.messageList), self.game.screen.width - 7)
        while buffer:
            line = buffer.pop(0)
            self.window.clear()
            self.window.print(0, 0, line)
            if buffer:
                self.window.print(len(line) + 1, 0, '-more-', tcod.yellow)
                self.window.blit(self.game.screen, 0, self.game.screen.height - 1)
                tcod.console_flush()
                wait(32)
            else:
                self.window.blit(self.game.screen, 0, self.game.screen.height - 1)

    def add(self, message):
        self.messageList.append(message)

    def clear(self):
        del self.messageList[:]
        self.window.clear()
        # self.window.update()
