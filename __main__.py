# -*- coding: utf-8 -*-

import logging
import os
import sys

from rogue.interface import Interface, Arrows, Window
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
        key = 1
        self.messenger.add(
            'Kill all monsters. Move with arrow keys or numpad. Q to exit.')
        while key != ord('Q'):
            logging.info('== Turn %d. ==' % self.turn)
            self.level.look_around('seethrough' in sys.argv)
            if not self.monsters.handle_monsters():
                win = Window(self.interface,
                             self.interface.dimensions[1] / 2 - 10,
                             self.interface.dimensions[0] / 2 - 3,
                             20,
                             6,
                             'Congratulations!',
                             'GREEN',
                             'DARKGREEN')
                win.window.addstr(3, 2, 'You`ve defeated',
                                  self.interface.colors['WHITE'])
                win.window.addstr(4, 2, 'all monsters!',
                                  self.interface.colors['WHITE'])
                win.loop()
                win.close()
                self.interface.close()
                break
            self.level.draw_map()
            self.player.draw()
            self.messenger.show()
            self.player.show_status()
            self.turn += 1
            if self.player.hitPoints < 1 and 'god' not in sys.argv:
                win = Window(self.interface,
                             int(self.interface.dimensions[1] / 2 - 10),
                             int(self.interface.dimensions[0] / 2 - 3),
                             20,
                             5,
                             'Defeat!',
                             'RED',
                             'DARKRED')
                win.window.addstr(3, 2, 'YOU DIED',
                                  self.interface.colors['RED'])
                win.loop()
                win.close()
                self.interface.close()
                break
            key = self.interface.stdscr.getch()
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
            elif key in (Arrows.LEFT, Arrows.RIGHT, Arrows.UP, Arrows.DOWN):
                if key == Arrows.LEFT:
                    checkx -= 1
                elif key == Arrows.RIGHT:
                    checkx += 1
                elif key == Arrows.UP:
                    checky -= 1
                elif key == Arrows.DOWN:
                    checky += 1
            elif key == ord('w'):
                win = Window(self.interface)
                win.loop()
                win.close()
                # self.level.drawMap()
            elif key == ord('Q'):
                logging.info('Game exit on Q press.')
            else:
                keychar = ''
                if key < 256:
                    keychar = chr(key)
                logging.warning('Key \'%s\' (%d) not supported.' % (keychar,
                                                                    key))
                self.messenger.add('Unknown command.')
            self.level.movement(self.player, (checkx, checky))
            self.interface.stdscr.refresh()


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
