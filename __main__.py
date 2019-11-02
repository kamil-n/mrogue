# -*- coding: utf-8 -*-

import logging
import os
import sys
import pygame
from rogue.pgame import PygameHelper, PygameWindow
from rogue.map import RogueMap
from rogue.message import Messenger
from rogue.monster import Menagerie
from rogue.player import Player


class Rogue(object):
    turn = 0
    interface = None
    level = None
    player = None
    monsters = None
    messenger = None

    def __init__(self):
        if os.path.isfile('rogue.log'):
            os.remove('rogue.log')
        logging.basicConfig(filename='rogue.log', level=logging.DEBUG)
        logging.info('======== Game start. ========')
        self.interface = PygameHelper()
        self.level = RogueMap(self)
        self.player = Player(self)
        self.monsters = Menagerie(self, 10)
        self.messenger = Messenger(self)
        self.messenger.add(
            'Kill all monsters. Move with arrow keys or numpad. Press q to exit.')

    def mainloop(self):
        key = pygame.K_UNKNOWN
        while key != pygame.K_q:
            self.turn += 1
            logging.info('== Turn %d. ==' % self.turn)
            self.level.look_around()
            self.monsters.handle_monsters()
            self.level.draw_map()
            self.player.show()
            self.messenger.show()
            if len(self.monsters.monsterList) == 0:
                win = PygameWindow(self.interface, title='Congratulations!')
                win.print_at(1, 3, 'YOU WIN!', (0, 255, 0))
                win.loop(pygame.K_q)
                break
            if self.player.current_HP < 1 and 'god' not in sys.argv:
                win = PygameWindow(self.interface, title='Game over.')
                win.print_at(1, 3, 'YOU DIED', (255, 0, 0))
                win.loop(pygame.K_q)
                break
            self.interface.refresh()
            key = self.interface.wait()
            self.messenger.clear()
            # movement:
            if key in range(49, 57 + 1):  # numpad
                dx, dy = 0, 0
                if key in (49, 52, 55):
                    dx = -1
                elif key in (51, 54, 57):
                    dx = 1
                if key > 54:
                    dy = -1
                elif key < 52:
                    dy = 1
                self.level.movement(self.player, (dx, dy))
            elif key == pygame.K_LEFT:
                self.level.movement(self.player, (-1, 0))
            elif key == pygame.K_RIGHT:
                self.level.movement(self.player, (1, 0))
            elif key == pygame.K_UP:
                self.level.movement(self.player, (0, -1))
            elif key == pygame.K_DOWN:
                self.level.movement(self.player, (0, 1))
            elif key == pygame.K_q:
                logging.info('Game exit on Q press.')
            else:
                logging.warning('Key \'%d\' not supported.' % key)
                self.messenger.add('Unknown command: %s.' % key)


if __name__ == '__main__':
    rogue = Rogue()
    try:
        rogue.mainloop()
    except Exception:  # TODO: jakie konkretnie mogą to być wyjątki
        print('ERROR')
        logging.error(sys.exc_info()[1])
        rogue.interface.close()
        print(sys.exc_info()[1])
        raise
    else:
        rogue.interface.close()
