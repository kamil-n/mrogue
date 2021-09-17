# -*- coding: utf-8 -*-

import tcod.event
import numpy as np
import mrogue

directions = np.asarray([
    [
        [0, tcod.event.K_UP, 0],
        [tcod.event.K_LEFT, 0, tcod.event.K_RIGHT],
        [0, tcod.event.K_DOWN, 0]
    ],
    [
        [tcod.event.K_KP_7, tcod.event.K_KP_8, tcod.event.K_KP_9],
        [tcod.event.K_KP_4, tcod.event.K_KP_5, tcod.event.K_KP_6],
        [tcod.event.K_KP_1, tcod.event.K_KP_2, tcod.event.K_KP_3]
    ],
    [
        [55, 56, 57],
        [52, 53, 54],
        [49, 50, 51]
    ]
])

ignore_keys = (
    tcod.event.K_LALT, tcod.event.K_RALT,
    tcod.event.K_LSHIFT, tcod.event.K_RSHIFT,
    tcod.event.K_LCTRL, tcod.event.K_RCTRL)

ignore_mods = tcod.event.KMOD_NUM


def direction_from(key, x, y):
    placement = np.nonzero(directions == key)
    return x + placement[2][0]-1, y + placement[1][0]-1


def key_is(key, target_key, target_mod=tcod.event.KMOD_NONE):
    if key[0] == target_key:
        if key[1] & ignore_mods == ignore_mods:
            key = (key[0], key[1] - ignore_mods)
        if not target_mod and not key[1]:
            return True
        elif target_mod and key[1] and key[1] | target_mod == target_mod:
            return True
    return False


def mod_is(mod, target_mod=tcod.event.KMOD_NONE):
    if mod & ignore_mods == ignore_mods:
        mod = mod - ignore_mods
    if not target_mod and not mod:
        return True
    elif target_mod and mod and mod | target_mod == target_mod:
        return True
    return False


def wait(character=None, mod=tcod.event.KMOD_NONE):
    while True:
        for event in tcod.event.wait():
            if event.type == 'QUIT':
                raise SystemExit
            elif event.type == 'KEYDOWN' and event.sym not in ignore_keys:
                if character:
                    if key_is((event.sym, event.mod), character, mod):
                        return True
                else:
                    return event.sym, event.mod


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
    window = tcod.Console(65, len(help_contents) + 2, 'F')
    window.draw_frame(0, 0, 65, len(help_contents) + 2, f'Welcome to MRogue {mrogue.__version__}!', False)
    for i in range(len(help_contents)):
        window.print(1, i + 1, help_contents[i])
    window.blit(Screen.get(), 12, 12, bg_alpha=0.95)
    Screen.get().present()
    wait(tcod.event.K_ESCAPE)


class Glyph:
    def __init__(self):
        self.icon = ''
        self.color = tcod.white


class Screen(tcod.Console):
    _instance = None
    _context = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Screen, cls).__new__(cls)
        return cls._instance

    def __init__(self, width, height, font):
        super().__init__(width, height, 'F')
        Screen._context = tcod.context.new(
            columns=width, rows=height, tileset=font,
            renderer=tcod.RENDERER_SDL2, title=f'MRogue {mrogue.__version__}')

    @classmethod
    def get(cls):
        return cls._instance

    @classmethod
    def present(cls, *args, **kwargs):
        cls._context.present(Screen._instance, *args, **kwargs)
