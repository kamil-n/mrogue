# -*- coding: utf-8 -*-

from rogue.pgame import PygameWindow


class Messenger(object):
    messageList = []

    def __init__(self, game):
        self.game = game
        self.window = PygameWindow(game.interface, 0, game.interface.dimensions[1]-1, game.interface.dimensions[0], 1)
        self.scrWidth = game.interface.screen.get_size()[0]

    def show(self):
        width = self.game.interface.font.size
        words_left = ' '.join(self.messageList)  # join all sentences
        number_of_letters = len(words_left)
        words_left = words_left.split(' ')  # split into words
        while number_of_letters > 0:
            words_to_show = ''
            while width(words_to_show)[0] + width(words_left[0])[0] + width('-more-')[0] < self.scrWidth:
                words_to_show += ' ' + words_left.pop(0)
                words_to_show = words_to_show.strip()
                number_of_letters = len(' '.join(words_left))
                if number_of_letters == 0:
                    break
            message_end = width(words_to_show)[0]
            self.window.clear()
            self.window.print_at(0, 0, words_to_show)
            self.window.update()
            if len(words_left) > 0:
                self.window.print_at(message_end // 32 + 1, 0, '-more-', (255, 255, 0))
                self.window.loop(32)

    def add(self, message):
        self.messageList.append(message)

    def clear(self):
        del self.messageList[:]
        self.window.clear()
        self.window.update()
