# -*- coding: utf-8 -*-

import logging
import os
import sys

# from rogue.interface import Interface
import curses
from rogue.curse import CursesWindow, CursesHelper
from rogue.map import RogueMap
from rogue.message import Messenger
from rogue.monster import Menagerie
from rogue.player import Player


class Rogue:
    turn = 0
    player = None
    level = None
    interface = None
    monsters = None
    messenger = None

    def __init__(self):
        if os.path.isfile('rogue.log'):
            os.remove('rogue.log')
        logging.basicConfig(filename='rogue.log', level=logging.DEBUG)
        logging.info('======== Game start. ========')
        self.interface = CursesHelper()
        self.mapDim = (self.interface.dimensions[1],
                       self.interface.dimensions[0] - 1)
        self.statusLine = 0
        self.messageLine = self.mapDim[1]
        self.level = RogueMap(self.mapDim)
        self.player = Player()
        self.monsters = Menagerie(10)
        self.messenger = Messenger(self.mapDim)
        self.interface.print_at(0, self.statusLine, 'HP:',
                                self.interface.colors['WHITE'])
        self.interface.print_at(12, self.statusLine, 'AC:',
                                self.interface.colors['WHITE'])
        self.interface.print_at(21, self.statusLine, 'ATK:',
                                self.interface.colors['WHITE'])

    def mainloop(self):
        key = 1
        self.messenger.add(
            'Kill all monsters. Move with arrow keys or numpad. Q to exit.')
        while key != ord('Q'):
            logging.info('== Turn %d. ==' % self.turn)
            self.level.look_around(self.player.pos,
                                   self.player.range,
                                   'seethrough' in sys.argv)
            if not self.monsters.handle_monsters():
                win = CursesWindow(self.mapDim[0] / 2 - 10,
                                   self.mapDim[1] / 2 - 3,
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
            self.interface.print_at(self.player.pos[0],
                                    self.player.pos[1],
                                    '@',
                                    self.player.color)
            self.messenger.show(self.messageLine)
            self.player.show_status(self.statusLine)
            self.turn += 1
            if self.player.hitPoints < 1 and 'god' not in sys.argv:
                win = CursesWindow(int(self.mapDim[0] / 2 - 10),
                                   int(self.mapDim[1] / 2 - 3),
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
            self.messenger.clear(self.messageLine)
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
            elif key in (curses.KEY_LEFT, curses.KEY_RIGHT,
                         curses.KEY_UP, curses.KEY_DOWN):
                if key == curses.KEY_LEFT:
                    checkx -= 1
                elif key == curses.KEY_RIGHT:
                    checkx += 1
                elif key == curses.KEY_UP:
                    checky -= 1
                elif key == curses.KEY_DOWN:
                    checky += 1
            elif key == ord('w'):
                win = CursesWindow()
                win.loop()
                win.close()
                # self.level.drawMap()
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
