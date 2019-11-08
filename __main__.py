# -*- coding: utf-8 -*-

import logging
import sys
import pygame
from rogue import __version__
from rogue.pgame import PygameHelper, PygameWindow
from rogue.map import RogueMap
from rogue.message import Messenger
from rogue.item import ItemManager
from rogue.monster import Menagerie
from rogue.player import Player


def direction_from(key, x, y):
    if key in (49, 52, 55) or key in (257, 260, 263) or key == 276:
        x -= 1
    elif key in (51, 54, 57) or key in (259, 262, 265) or key == 275:
        x += 1
    if key in (55, 56, 57) or key in (263, 264, 265) or key == 273:
        y -= 1
    elif key in (49, 50, 51) or key in (257, 258, 259) or key == 274:
        y += 1
    return x, y


class Rogue(object):
    turn = 0

    def __init__(self):
        logging.basicConfig(filename='rogue.log', level=logging.DEBUG, filemode='w',
                            format='%(name)s - %(levelname)s - %(message)s')
        self.log = logging.getLogger(__name__)
        self.log.info('Welcome to Rogue {}!'.format(__version__))
        self.interface = PygameHelper()
        self.level = RogueMap(self)
        self.items = ItemManager(self)
        self.player = Player(self)
        self.monsters = Menagerie(self, 10)
        self.messenger = Messenger(self)
        self.messenger.add('Kill all monsters. Move with arrow keys or numpad. Press q to exit.')

    def mainloop(self):
        key = pygame.K_UNKNOWN
        while key != pygame.K_q:
            self.turn += 1
            self.log.info('== Turn %d. ==' % self.turn)
            self.monsters.handle_monsters(self.player)
            self.interface.objects_on_map.update()  # TODO: refactor
            self.level.look_around()
            self.level.draw_map()
            self.interface.show_objects()
            self.player.show_stats()
            self.messenger.show()
            self.interface.refresh()
            if len(self.monsters.monsterList) == 0:
                win = PygameWindow(self.interface, title='Congratulations!',
                                   left=self.interface.dimensions[0] // 2 - 5,
                                   top=self.interface.dimensions[1] // 2 - 2)
                win.print_at(1, 2, 'YOU WIN!', (0, 255, 0))
                win.loop(pygame.K_q)
                break
            if self.player.current_HP < 1 and 'debug' not in sys.argv:
                win = PygameWindow(self.interface, title='Game over.',
                                   left=self.interface.dimensions[0] // 2 - 5,
                                   top=self.interface.dimensions[1] // 2 - 2)
                win.print_at(1, 2, 'YOU DIED', (255, 0, 0))
                win.loop(pygame.K_q)
                break
            self.interface.refresh()
            key = self.interface.wait()
            self.messenger.clear()
            if key == pygame.K_i:
                self.items.show_inventory()
            elif key == pygame.K_e:
                self.items.show_equipment()
            elif key in range(257, 266 + 1) or key in range(49, 57 + 1) or key in range(273, 276 + 1):
                self.level.movement(self.player, direction_from(key, *self.player.pos))
            elif key == pygame.K_q:
                self.log.info('Game exit on Q press.')
            else:
                self.log.warning('Key \'{}\' not supported.'.format(chr(key)))
                self.messenger.add('Unknown command: \'%s\'.' % chr(key))


if __name__ == '__main__':
    rogue = Rogue()
    try:
        rogue.mainloop()
    except Exception:
        rogue.log.exception(sys.exc_info()[1])
        rogue.interface.close()
        raise
    else:
        rogue.interface.close()
