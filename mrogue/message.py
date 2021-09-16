# -*- coding: utf-8 -*-

from textwrap import wrap
import tcod.console
import mrogue.io


class Messenger:
    _message_list = []
    message_history = []
    window = None

    def __init__(self):
        self.screen = mrogue.io.Screen.get()
        Messenger.window = tcod.console.Console(self.screen.width, 1)

    def show(self):
        whole_message = ' '.join(self._message_list)
        if whole_message:
            self.message_history += wrap(whole_message, 63)
        buffer = wrap(whole_message, self.screen.width - 7)
        while buffer:
            line = buffer.pop(0)
            Messenger.window.clear()
            Messenger.window.print(0, 0, line)
            if buffer:
                Messenger.window.print(len(line) + 1, 0, '-more-', tcod.yellow)
                Messenger.window.blit(self.screen, 0, self.screen.height - 1)
                mrogue.io.Screen.get().context.present(self.screen)
                mrogue.io.wait(32)
            else:
                Messenger.window.blit(self.screen, 0, self.screen.height - 1)

    @classmethod
    def add(cls, message):
        cls._message_list.append(message)

    @classmethod
    def clear(cls):
        del cls._message_list[:]
        cls.window.clear()
