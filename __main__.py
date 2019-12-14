# -*- coding: utf-8 -*-

from os import path
import sys
from numpy import nonzero
import tcod
import tcod.console
import tcod.event
from mrogue import __version__, wait, key_is, mod_is, directions
from mrogue.map import Dungeon
from mrogue.message import Messenger
from mrogue.item import ItemManager
from mrogue.monster import MonsterManager
from mrogue.player import Player
from mrogue.timers import Timer


def direction_from(key, x, y):
    placement = nonzero(directions == key)
    return x + placement[2][0]-1, y + placement[1][0]-1


def help_screen():
    help_contents = [
        'Kill all monsters. To attack, \'walk\' into them.',
        'Move with keyboard arrows, numpad or number keys.',
        'Directions for number keys:',
        '7\\ 8 /9',
        '4- @ -6      (press 5 to pass turn)',
        '1/ 2 \\3',
        'Shift + direction = autorun.',
        'Other keys:',
        'e - open equipment screen. Press slot hotkeys to unequip items.',
        'i - open inventory screen. Press hotkeys to manage items.',
        ', (comma) - pick up items',
        '> - descend to next level while standing on this icon.',
        '< - ascend back to previous level while standing on this icon.',
        'M - show message history.',
        'H - show this help screen.',
        'Q - close game when on main screen',
        '',
        'Esc - close pop-up windows like this one.'
    ]
    win = tcod.console.Console(65, len(help_contents) + 2, 'F')
    win.draw_frame(0, 0, 65, len(help_contents) + 2,
                   'Welcome to MRogue {}!'.format(__version__), False)
    for i in range(len(help_contents)):
        win.print(1, i + 1, help_contents[i])
    return win


def message_screen(screen, messages):
    window = tcod.console.Console(65, 12, 'F')
    scroll = len(messages) - 10 if len(messages) > 10 else 0
    while True:
        window.clear()
        window.draw_frame(0, 0, 65, 12, 'Messages')
        if scroll > 0:
            window.print(0, 1, chr(24), tcod.black, tcod.white)
        for i in range(len(messages)):
            if i > 10 - 1:
                break
            window.print(1, 1 + i, messages[i+scroll])
        if 10 + scroll < len(messages):
            window.print(0, 10, chr(25), tcod.black, tcod.white)
        window.blit(screen, 12, 12, bg_alpha=0.95)
        tcod.console_flush()
        key = wait()
        if key_is(key, 27):
            return False
        elif key_is(key, tcod.event.K_DOWN):
            scroll += 1 if 10 + scroll < len(messages) else 0
        elif key_is(key, tcod.event.K_UP):
            scroll -= 1 if scroll > 0 else 0


class Rogue(object):
    turn = 0
    num_objects = 10

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
        self.dungeon = Dungeon(self)
        self.items = ItemManager(self)
        self.monsters = MonsterManager(self,)
        self.monsters.create_monsters(self.num_objects)
        self.messenger = Messenger(self)
        self.player = Player(self)
        self.items.create_loot(self.num_objects)

    def update_dungeon(self):
        self.turn += 1
        Timer.update()
        while True:
            if self.monsters.handle_monsters(self.player):
                break
        self.dungeon.look_around()
        if self.player.current_HP < 1 and 'debug' not in sys.argv:
            win = tcod.console.Console(20, 4, 'F')
            win.draw_frame(0, 0, 20, 4, 'Game over.', False)
            win.print(6, 2, 'YOU DIED', tcod.red)
            self.dungeon.draw_map()
            self.player.show_stats()
            self.messenger.show()
            win.blit(self.screen, 10, 10)
            tcod.console_flush()
            wait(tcod.event.K_ESCAPE)
            return True
        return False

    def draw_dungeon(self):
        self.dungeon.draw_map()
        self.player.show_stats()
        self.messenger.show()
        tcod.console_flush()

    def handle_input(self, key):
        if key_is(key, tcod.event.K_i):
            if self.items.show_inventory():
                return True
        elif key_is(key, tcod.event.K_e):
            if self.items.show_equipment():
                return True
        elif key_is(key, tcod.event.K_COMMA):
            if self.player.pickup_item(
                    self.items.get_item_on_map(self.player.pos)):
                return True
        elif key_is(key, tcod.event.K_PERIOD, tcod.event.KMOD_SHIFT):
            if self.dungeon.descend(self.player.pos):
                return True
        elif key_is(key, tcod.event.K_COMMA, tcod.event.KMOD_SHIFT):
            if self.dungeon.ascend(self.player.pos):
                return True
        elif key[0] in directions and mod_is(key[1], tcod.event.KMOD_SHIFT):
            if self.dungeon.automove(self.player.pos, key[0]):
                return True
        elif key[0] in directions:
            if self.dungeon.movement(
                    self.player, direction_from(
                        key[0], *self.player.pos)):
                return True
        elif key_is(key, tcod.event.K_m, tcod.event.KMOD_SHIFT):
            message_screen(self.screen, self.messenger.message_history)
        elif key_is(key, tcod.event.K_h, tcod.event.KMOD_SHIFT):
            win = help_screen()
            win.blit(self.screen, 12, 12, bg_alpha=0.95)
            tcod.console_flush()
            wait(tcod.event.K_ESCAPE)
        elif key_is(key, tcod.event.K_q, tcod.event.KMOD_SHIFT):
            return True
        else:
            self.messenger.add('Unknown command: {}{}'.format(
                'mod+' if key[1] else '',
                chr(key[0]) if key[0] < 256 else '<?>'))
        return False

    def mainloop(self):
        key = (0, 0)
        while not key_is(key, tcod.event.K_q, tcod.event.KMOD_SHIFT):
            if self.update_dungeon():
                break
            while True:
                self.draw_dungeon()
                key = wait()
                self.messenger.clear()
                self.player.moved = False
                if self.handle_input(key):
                    break


if __name__ == '__main__':
    rogue = Rogue()
    try:
        rogue.mainloop()
    except Exception:
        raise
