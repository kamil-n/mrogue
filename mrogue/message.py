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
                self.screen.present()
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

    def message_screen(self):
        window = tcod.Console(65, 12, 'F')
        scroll = len(self.message_history) - 10 if len(self.message_history) > 10 else 0
        while True:
            window.clear()
            window.draw_frame(0, 0, 65, 12, 'Messages')
            if scroll > 0:
                window.print(0, 1, chr(0x2191), tcod.black, tcod.white)
            for i in range(len(self.message_history)):
                if i > 10 - 1:
                    break
                window.print(1, 1 + i, self.message_history[i+scroll])
            if 10 + scroll < len(self.message_history):
                window.print(0, 10, chr(0x2193), tcod.black, tcod.white)
            window.blit(self.screen, 12, 12, bg_alpha=0.95)
            self.screen.present()
            key = mrogue.io.wait()
            if mrogue.io.key_is(key, 27):
                return False
            elif mrogue.io.key_is(key, tcod.event.K_DOWN):
                scroll += 1 if 10 + scroll < len(self.message_history) else 0
            elif mrogue.io.key_is(key, tcod.event.K_UP):
                scroll -= 1 if scroll > 0 else 0
