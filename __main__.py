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

    def mainloop(self):
        key = pygame.K_UNKNOWN
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        self.messenger.add(
            'Kill all monsters. Move with arrow keys or numpad. Q to exit.')
        while key != pygame.K_q:
            logging.info('== Turn %d. ==' % self.turn)
            self.level.look_around('seethrough' in sys.argv)
            if not self.monsters.handle_monsters():
                # win condition
                break
            self.level.draw_map()
            self.player.draw()
            self.player.show_status()
            self.messenger.show()
            self.turn += 1
            if self.player.hitPoints < 1 and 'god' not in sys.argv:
                # lose condition
                break
            pygame.event.clear()
            while True:
                event = pygame.event.wait()
                if event.type == pygame.QUIT:
                    self.interface.close()
                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    break
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
                win = Window(self.interface)
                win.loop(pygame.K_q)
                win.close()
            elif key == pygame.K_q:
                logging.info('Game exit on Q press.')
            else:
                logging.warning('Key \'%d\' not supported.' % key)
                self.messenger.add('Unknown command: %s.' % key)
            self.level.movement(self.player, (checkx, checky))
            self.interface.refresh()


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
