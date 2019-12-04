# -*- coding: utf-8 -*-

from numpy import asarray
from os import path
import sys
import tcod
import tcod.console
import tcod.event
from mrogue import __version__, wait, key_is
from mrogue.map import MapManager
from mrogue.message import Messenger
from mrogue.item import ItemManager
from mrogue.monster import MonsterManager
from mrogue.player import Player
from mrogue.timers import Timer


directions4 = [
    tcod.event.K_LEFT, tcod.event.K_RIGHT, tcod.event.K_UP, tcod.event.K_DOWN
]
directions8 = asarray([
    [
        [tcod.event.K_KP_1, tcod.event.K_KP_2, tcod.event.K_KP_3],
        [tcod.event.K_KP_4, tcod.event.K_KP_5, tcod.event.K_KP_6],
        [tcod.event.K_KP_7, tcod.event.K_KP_8, tcod.event.K_KP_9]
    ],
    [
        [49, 50, 51],
        [52, 53, 54],
        [55, 56, 57]
    ]
])


def direction_from(key, x, y):
    if key in directions8[:, :, 0] or key == tcod.event.K_LEFT:
        x -= 1
    elif key in directions8[:, :, 2] or key == tcod.event.K_RIGHT:
        x += 1
    if key in directions8[:, 2, :] or key == tcod.event.K_UP:
        y -= 1
    elif key in directions8[:, 0, :] or key == tcod.event.K_DOWN:
        y += 1
    return x, y


def help_screen():
    win = tcod.console.Console(65, 16, 'F')
    win.draw_frame(0, 0, 65, 16, 'Welcome to MRogue {}!'.format(__version__),
                   False)
    win.print(1, 1, 'Kill all monsters. To attack, \'walk\' into them.')
    win.print(1, 2, 'Move with keyboard arrows, numpad or number keys.')
    win.print(1, 3, 'Directions for number keys:')
    win.print(1, 4, '7\\ 8 /9')
    win.print(1, 5, '4- @ -6      (press 5 to pass turn)')
    win.print(1, 6, '1/ 2 \\3')
    win.print(1, 7, 'Other keys:')
    win.print(1, 8,
              'e - open equipment screen. Press slot hotkeys to unequip items.')
    win.print(1, 9, 'i - open inventory screen. Press hotkeys to manage items.')
    win.print(1, 10, ', (comma) - pick up items')
    win.print(1, 11, 'H - show this help screen.')
    win.print(1, 12,
              'Q - close game when on main screen or when game is finished.')
    win.print(1, 14, 'Esc - close pop-up windows like this one.')
    return win


class Rogue(object):
    turn = 0

    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.dir = path.dirname(sys.executable)
        else:
            self.dir = path.dirname(__file__)
        tcod.console_set_custom_font(
            path.join(self.dir, 'terminal10x16_gs_ro.png'),
            tcod.FONT_LAYOUT_ASCII_INROW | tcod.FONT_TYPE_GREYSCALE)
        self.screen = tcod.console_init_root(
            100, 40,
            'MRogue {}'.format(__version__),
            renderer=tcod.RENDERER_SDL2,
            order='F',
            vsync=True)
        self.dungeon = MapManager(self)
        self.level = self.dungeon.get_level()
        self.items = ItemManager(self, 10)
        self.messenger = Messenger(self)
        self.player = Player(self)
        self.monsters = MonsterManager(self, 10)

    def mainloop(self):
        key = (0, 0)
        while not key_is(key, tcod.event.K_q, tcod.event.KMOD_SHIFT):
            self.turn += 1
            Timer.update()
            while True:
                if self.monsters.handle_monsters(self.player):
                    break
            self.level.look_around()
            if len(self.level.units) == 1:
                win = tcod.console.Console(20, 4, 'F')
                win.draw_frame(0, 0, 20, 4, 'Congratulations.', False)
                win.print(6, 2, 'YOU WIN!', tcod.green)
                self.level.draw_map()
                self.player.show_stats()
                self.messenger.show()
                win.blit(self.screen, 10, 10)
                tcod.console_flush()
                wait(tcod.event.K_ESCAPE)
                break
            if self.player.current_HP < 1 and 'debug' not in sys.argv:
                win = tcod.console.Console(20, 4, 'F')
                win.draw_frame(0, 0, 20, 4, 'Game over.', False)
                win.print(6, 2, 'YOU DIED', tcod.red)
                self.level.draw_map()
                self.player.show_stats()
                self.messenger.show()
                win.blit(self.screen, 10, 10)
                tcod.console_flush()
                wait(tcod.event.K_ESCAPE)
                break
            while True:
                self.level.draw_map()
                self.player.show_stats()
                self.messenger.show()
                tcod.console_flush()
                key = wait()
                self.messenger.clear()
                if key_is(key, tcod.event.K_i):
                    if self.items.show_inventory():
                        break
                elif key_is(key, tcod.event.K_e):
                    if self.items.show_equipment():
                        break
                elif key_is(key, tcod.event.K_COMMA):
                    if self.player.pickup_item(
                            self.items.get_item_on_map(self.player.pos)):
                        break
                elif key[0] in directions4 or key[0] in directions8:
                    if self.level.movement(
                            self.player, direction_from(
                                key[0], *self.player.pos)):
                        break
                elif key_is(key, tcod.event.K_h, tcod.event.KMOD_SHIFT):
                    win = help_screen()
                    win.blit(self.screen, 12, 12, bg_alpha=0.95)
                    tcod.console_flush()
                    wait(tcod.event.K_ESCAPE)
                elif key_is(key, tcod.event.K_q, tcod.event.KMOD_SHIFT):
                    break
                else:
                    self.messenger.add('Unknown command: {}{}'.format(
                        'mod+' if key[1] else '',
                        chr(key[0]) if key[0] < 256 else '<?>'))


if __name__ == '__main__':
    rogue = Rogue()
    try:
        rogue.mainloop()
    except Exception:
        raise
