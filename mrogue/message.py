# -*- coding: utf-8 -*-

from mrogue import wait
from textwrap import wrap
import tcod.console


class Messenger:
    _message_list = []
    message_history = []

    def __init__(self, game):
        self.game = game
        self.window = tcod.console.Console(game.screen.width, 1)

    def show(self):
        whole_message = ' '.join(self._message_list)
        if whole_message:
            self.message_history += wrap(whole_message, 63)
        buffer = wrap(whole_message, self.game.screen.width - 7)
        while buffer:
            line = buffer.pop(0)
            self.window.clear()
            self.window.print(0, 0, line)
            if buffer:
                self.window.print(len(line) + 1, 0, '-more-', tcod.yellow)
                self.window.blit(self.game.screen, 0, self.game.screen.height - 1)
                self.game.context.present(self.game.screen)
                wait(32)
            else:
                self.window.blit(self.game.screen, 0, self.game.screen.height - 1)

    def add(self, message):
        self._message_list.append(message)

    def clear(self):
        del self._message_list[:]
        self.window.clear()
