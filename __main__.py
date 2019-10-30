# -*- coding: utf-8 -*-

import logging
import os
import sys
import pygame
from rogue.interface import Interface, Window
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
        self.interface = Interface()
        self.level = RogueMap(self)
        self.player = Player(self)
        self.monsters = Menagerie(self, 10)
        self.messenger = Messenger(self)
        self.messenger.add(
            'Kill all monsters. Move with arrow keys or numpad. Q to exit.')

    def mainloop(self):
        key = pygame.K_UNKNOWN
        while key != pygame.K_q:
            self.turn += 1
            logging.info('== Turn %d. ==' % self.turn)
            self.level.look_around('seethrough' in sys.argv)
            self.monsters.handle_monsters()
            self.level.draw_map()
            self.player.show()
            self.messenger.show()
            if len(self.monsters.monsterList) == 0:
                win = Window(self.interface, title='Congratulations!')
                win.print_at(1, 3, 'YOU WIN!', (0, 255, 0))
                win.loop(pygame.K_q)
                break
            if self.player.hitPoints < 1 and 'god' not in sys.argv:
                win = Window(self.interface, title='Game over.')
                win.print_at(1, 3, 'YOU DIED', (255, 0, 0))
                win.loop(pygame.K_q)
                break
            self.interface.refresh()
            key = self.interface.wait()
            self.messenger.clear()
            # movement:
            checkx = 0
            checky = 0
            if key in range(49, 57 + 1):
                if key in (49, 52, 55):
                    checkx -= 1
                elif key in (51, 54, 57):
                    checkx += 1
                if key > 54:
                    checky -= 1
                elif key < 52:
                    checky += 1
            elif key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                if key == pygame.K_LEFT:
                    checkx -= 1
                elif key == pygame.K_RIGHT:
                    checkx += 1
                elif key == pygame.K_UP:
                    checky -= 1
                elif key == pygame.K_DOWN:
                    checky += 1
            elif key == pygame.K_w:
                win = Window(self.interface, bg_color=(32, 32, 32))
                win.print_at(1, 3, "Test", (0, 0, 255))
                win.loop(pygame.K_q)
                win.close()
            elif key == pygame.K_q:
                logging.info('Game exit on Q press.')
            else:
                logging.warning('Key \'%d\' not supported.' % key)
                self.messenger.add('Unknown command: %s.' % key)
            self.level.movement(self.player, (checkx, checky))


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
