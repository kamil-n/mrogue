# -*- coding: utf-8 -*-

from textwrap import wrap
import tcod.console

class Messenger(object):
    messageList = []

    def __init__(self, game):
        self.game = game
        self.window = tcod.console.Console(game.screen.width, 1)

    def show(self):
        buffer = wrap(' '.join(self.messageList), self.game.screen.width - 7)
        self.window.clear()
        if len(buffer) > 1:
            for line in buffer:
                self.window.print(0, 0, line)
        elif buffer:
            self.window.print(0, 0, buffer[0])
        self.window.blit(self.game.screen, 0, self.game.screen.height - 1)
        '''if len(buffer) > 1:
            self.window.print_at(message_end // 32 + 1, 0, '-more-', (255, 255, 0))
            self.window.loop(32)'''

    def add(self, message):
        self.messageList.append(message)

    def clear(self):
        del self.messageList[:]
        self.window.clear()
        # self.window.update()
