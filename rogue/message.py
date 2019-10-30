# -*- coding: utf-8 -*-

# import logging


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
        msg_buffer = ' '.join(self.messageList)
        '''buffer_length = len(msg_buffer)
        msg_buffer = msg_buffer.split(' ')
        while buffer_length > 0:
            msg_piece = ''
            while (self.scrDim[0] - 6 > len(msg_piece) + len(msg_buffer[0])):
                msg_piece += ' ' + msg_buffer.pop(0)
                msg_piece = msg_piece.strip()
                buffer_length = len(' '.join(msg_buffer))
                if buffer_length == 0:
                    break
            message_end = len(msg_piece)
            self.game.interface.print_at(0, 0,
                                         msg_piece,
                                         self.game.interface.colors[
                                             'WHITE'])
            if len(msg_buffer) > 0:
                if message_end == self.scrDim[0] - 6:
                    logging.warning('Last character of "-more-" is screen end!')
                logging.debug('still {} words left.'.format(len(msg_buffer)))
                self.game.interface.print_at(message_end, 0,
                                             '-more-',
                                             self.game.interface.colors[
                                                 'WHITE'])
                self.game.interface.wait(' ')
                self.game.interface.print_at(0, 0, (self.scrDim[0]) * ' ')'''
        self.game.interface.print_at(0, 23, 200 * ' ')
        self.game.interface.print_at(0, 23, msg_buffer)
        self.game.interface.refresh()

    def add(self, message):
        self.messageList.append(message)

    def clear(self):
        del self.messageList[:]
