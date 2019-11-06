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
            self.monsters.handle_monsters(self.player)
            self.interface.objects_on_map.update()  # TODO: refactor
            self.level.look_around()
            self.level.draw_map()
            self.interface.show_objects()
            self.player.show_stats()
            self.messenger.show()
            if len(self.monsters.monsterList) == 0:
                win = PygameWindow(self.interface, title='Congratulations!',
                                   left=self.interface.dimensions[0] // 2 - 5,
                                   top=self.interface.dimensions[1] // 2 - 2)
                win.print_at(1, 2, 'YOU WIN!', (0, 255, 0))
                win.loop(pygame.K_q)
                break
            if self.player.current_HP < 1 and 'god' not in sys.argv:
                win = PygameWindow(self.interface, title='Game over.',
                                   left=self.interface.dimensions[0] // 2 - 5,
                                   top=self.interface.dimensions[1] // 2 - 2)
                win.print_at(1, 2, 'YOU DIED', (255, 0, 0))
                win.loop(pygame.K_q)
                break
            # pathfinding visualisation
            if 'debug' in sys.argv:
                for monster in self.monsters.monsterList:
                    if monster.path:
                        previous = monster.pos
                        for step in monster.path:
                            pygame.draw.line(self.interface.screen, (0, 255, 0),
                                             (previous[0] * 32 + 16,
                                              previous[1] * 32 + 16),
                                             (step[0] * 32 + 15,
                                              step[1] * 32 + 16))
                            previous = step
            self.interface.refresh()
            key = self.interface.wait()
            self.messenger.clear()
            # movement:
            if key in range(257, 266 + 1):
                x, y = self.player.pos
                if key in (257, 260, 263):
                    x -= 1
                elif key in (259, 262, 265):
                    x += 1
                if key > 262:
                    y -= 1
                elif key < 260:
                    y += 1
                self.level.movement(self.player, (x, y))
            elif key in (
                    pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                x, y = self.player.pos
                if key == pygame.K_LEFT:
                    x -= 1
                elif key == pygame.K_RIGHT:
                    x += 1
                elif key == pygame.K_UP:
                    y -= 1
                elif key == pygame.K_DOWN:
                    y += 1
                self.level.movement(self.player, (x, y))
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
