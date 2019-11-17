# -*- coding: utf-8 -*-

import logging
from os import path
import sys
import tcod
import tcod.console
import tcod.event
from modules import __version__, wait
from modules.map import RogueMap
from modules.message import Messenger
from modules.item import ItemManager
from modules.monster import Menagerie
from modules.player import Player


def direction_from(key, x, y):
    if key in (49, 52, 55) or key in (257, 260, 263) or key == tcod.event.K_LEFT:
        x -= 1
    elif key in (51, 54, 57) or key in (259, 262, 265) or key == tcod.event.K_RIGHT:
        x += 1
    if key in (55, 56, 57) or key in (263, 264, 265) or key == tcod.event.K_UP:
        y -= 1
    elif key in (49, 50, 51) or key in (257, 258, 259) or key == tcod.event.K_DOWN:
        y += 1
    return x, y


class Rogue(object):
    turn = 0

    def __init__(self):
        logging.basicConfig(filename='modules.log', level=logging.DEBUG, filemode='w',
                            format='%(name)s - %(levelname)s - %(message)s')
        self.log = logging.getLogger(__name__)
        self.log.info('Welcome to MRogue {}!'.format(__version__))
        basedir = path.dirname(path.abspath(__file__))
        tcod.console_set_custom_font(path.join(basedir, 'terminal10x16_gs_ro.png'), tcod.FONT_LAYOUT_ASCII_INROW | tcod.FONT_TYPE_GREYSCALE)
        self.screen = tcod.console_init_root(100, 40, 'MRogue {}'.format(__version__), renderer=tcod.RENDERER_SDL2, order='F', vsync=True)
        self.level = RogueMap(self)
        self.items = ItemManager(self, 10)
        self.player = Player(self)
        self.monsters = Menagerie(self, 10)
        self.messenger = Messenger(self)
        self.messenger.add('Kill all monsters. Move with arrow keys or numpad. Press q to exit.')

    def mainloop(self):
        key = 0
        while key != tcod.event.K_q:
            self.turn += 1
            self.log.info('== Turn %d. ==' % self.turn)
            self.monsters.handle_monsters(self.player)
            self.player.check_if_items_on_ground()
            self.level.look_around()
            self.level.draw_map()
            self.player.show_stats()
            self.messenger.show()
            tcod.console_flush()
            if len(self.monsters.monsterList) == 0:
                win = tcod.console.Console(20, 4, 'F')
                win.draw_frame(0, 0, 20, 4, 'Congratulations.', False)
                win.print(6, 2, 'YOU WIN!', tcod.green)
                win.blit(self.screen, 10, 10)
                tcod.console_flush()
                wait(tcod.event.K_q)
                break
            if self.player.current_HP < 1 and 'debug' not in sys.argv:
                win = tcod.console.Console(20, 4, 'F')
                win.draw_frame(0, 0, 20, 4, 'Game over.', False)
                win.print(6, 2, 'YOU DIED', tcod.red,)
                win.blit(self.screen, 10, 10)
                tcod.console_flush()
                wait(tcod.event.K_q)
                break
            key = wait()
            self.messenger.clear()
            if key == tcod.event.K_i:
                self.items.show_inventory()
            elif key == tcod.event.K_e:
                self.items.show_equipment()
            elif key == tcod.event.K_COMMA:
                self.player.pickup_item(self.items.get_item_on_map(self.player.pos))
            elif key in range(49, 57 + 1) or key in (tcod.event.K_DOWN, tcod.event.K_UP, tcod.event.K_LEFT, tcod.event.K_RIGHT):
                self.level.movement(self.player, direction_from(key, *self.player.pos))
            elif key == tcod.event.K_h:
                win = tcod.console.Console(65, 16, 'F')
                win.draw_frame(0, 0, 65, 16, 'Welcome to MRogue {}!'.format(__version__), False)
                win.print(1, 1, 'Kill all monsters. To attack, \'walk\' into them.')
                win.print(1, 2, 'Move with keyboard arrows, numpad or number keys.')
                win.print(1, 3, 'Directions for number keys:')
                win.print(1, 4, '7\\ 8 /9')
                win.print(1, 5, '4- @ -6      (press 5 to pass turn)')
                win.print(1, 6, '1/ 2 \\3')
                win.print(1, 7, 'Other keys:')
                win.print(1, 8, 'e - open equipment screen. Press slot hotkeys to unequip items.')
                win.print(1, 9, 'i - open inventory screen. Press hotkeys to manage items.')
                win.print(1, 10, ', (comma) - pick up items')
                win.print(1, 11, 'h - show this help screen.')
                win.print(1, 12, 'q - close game when on main screen or when game is finished.')
                win.print(1, 14, 'Esc - close pop-up windows like this one.')
                win.blit(self.screen, 12, 12, 0, 0, 65, 16, 1.0, 0.95)
                tcod.console_flush()
                wait(tcod.event.K_ESCAPE)
            elif key == tcod.event.K_q:
                self.log.info('Game exit on Q press.')
            else:
                self.log.warning('Key \'{}\' not supported.'.format(key))
                self.messenger.add('Unknown command: \'%s\'.' % chr(key))


if __name__ == '__main__':
    rogue = Rogue()
    try:
        rogue.mainloop()
    except Exception:
        rogue.log.exception(sys.exc_info()[1])
        raise
