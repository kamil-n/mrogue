# -*- coding: utf-8 -*-
"""Module providing a layer on top of libTCOD events and screen / console communication.

Globals:
    * directions - a 3D array for easy keypress to direction mapping
    * ignore_keys - a list of keyboard buttons that should be ignored as keys
    * ignore_mods - a list of keyboard buttons that should be ignored as modifiers
    * tile_dt - data format for numpy arrays
Functions:
    * direction_from() - calculates new coordinates from current coordinates and a keypress
    * key_is() - compares a pressed key against a target (expected) key
    * mod_is() - checks if a modifier is pressed
    * wait() - freezes everything until a specific key (or any key) is pressed
    * help_screen() - prints key bindings on the screen
    * select_action() - prints lines of available actions and performs the selected one
Classes:
    * Tile - a tuple-like structure to hold tile data for the map
    * Glyph - a base class for any entity that shall be printed on screen (item or unit)
    * Screen - a singleton keeping the main window=screen and the context information
"""
import string
from typing import NamedTuple, Tuple, Callable
import numpy as np
import tcod.event
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

# type hints
KEY = tcod.event.KeyDown
MOD = tcod.event.Modifier


def direction_from(key: KEY, pos: mrogue.Point) -> mrogue.Point:
    """Calculate new (x, y) position from a key and previous position

    :param key: a tcod.event key code
    :param pos: current coordinates
    :return: a set of new x, y coordinates
    """
    placement = np.nonzero(directions == key)
    return mrogue.Point(pos.x + placement[2][0]-1, pos.y + placement[1][0]-1)


def key_is(key: tuple[KEY, MOD], target_key: KEY, target_mod: MOD = tcod.event.KMOD_NONE) -> bool:
    """Check if a pressed, modified key equals target key code and modifier

    :param key: raw keypress (a tuple of key code and modifier)
    :param target_key: expected key code
    :param target_mod: expected modifier, default = None
    :return: True if key and mod are equal to expected
    """
    if key[0] == target_key:
        # if modifier is pressed but it is in the ignore list - remove the modifier
        if key[1] & ignore_mods == ignore_mods:
            key = (key[0], key[1] - ignore_mods)
        # if no modifier is expected and none was pressed
        if not target_mod and not key[1]:
            return True
        elif target_mod and key[1] and key[1] | target_mod == target_mod:
            return True
    return False


def mod_is(mod: MOD, target_mod: MOD = tcod.event.KMOD_NONE) -> bool:
    """Check if a specific modifier(s) are pressed. By default expect no modifier

    :param mod: pressed modifier or multiple
    :param target_mod: expected modifier or multiple
    :return: True if pressed modifier key(s) match expected state
    """
    # if any pressed modifiers are in the ignore list - remove them
    if mod & ignore_mods == ignore_mods:
        mod = mod - ignore_mods
    # if no modifiers are left and we expect none - report success
    if not target_mod and not mod:
        return True
    # if one or more modifiers are left but we expect them - report success
    elif target_mod and mod and mod | target_mod == target_mod:
        return True
    return False


def wait(character: KEY = None, mod: MOD = tcod.event.KMOD_NONE) -> tuple[KEY, MOD]:
    """Either wait until a specific key is pressed or wait until any key is pressed

    :param character: wait for this specific key
    :param mod: check if a specific modifier is also pressed
    :return: pressed key/modifier combination
    """
    while True:
        for event in tcod.event.wait():
            if event.type == 'QUIT':
                raise SystemExit
            # don't consider modifiers to be key presses
            elif event.type == 'KEYDOWN' and event.sym not in ignore_keys:
                if character:
                    if key_is((event.sym, event.mod), character, mod):
                        return event.sym, event.mod
                else:
                    return event.sym, event.mod


def help_screen() -> None:
    """Print key bindings on the screen and wait for 'Escape" key"""
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


def select_action(options: list[tuple[str, object, Callable]]) -> tuple[bool, bool or None]:
    """Present a small sub-window with a range of available options to perform on an object

    :param options: a list of options as tuples: (action description, Item)
    :return: (False, _) if callback wasn't executed, (True, Callback result) otherwise
    """
    w, h = 23, len(options) + 2
    dialog = tcod.console.Console(w, h, 'F')
    dialog.draw_frame(0, 0, w, h, 'Select an action:')
    for row, option in enumerate(options):
        dialog.print(2, row + 1, f'{string.ascii_letters[row]}) {option[0]}')
        dialog.blit(Screen.get(), 4 + 10, 4 + 1)
        Screen.get().present()
    while True:
        selection = mrogue.io.wait()
        if mrogue.io.key_is(selection, tcod.event.K_ESCAPE):
            return False, None
        elif selection[0] in range(97, 97 + len(options)):
            selected = selection[0] - 97
            return True, options[selected][2](options[selected][1])


tile_dt = np.dtype([
        ('walkable', bool),
        ('transparent', bool),
        ('lit', tcod.console.rgba_graphic),
        ('dim', tcod.console.rgba_graphic)
    ])


class Tile(NamedTuple):
    walkable: bool
    transparent: bool
    lit: Tuple[int, Tuple[int, int, int, int], Tuple[int, int, int, int]]
    dim: Tuple[int, Tuple[int, int, int, int], Tuple[int, int, int, int]]


class Glyph:
    """Any entity that will be printed on the screen (a Unit or an Item) has to extend this

    Object attributes:
        * icon - should preferably be an extended byte code ( chr(0x0000) etc.)
        * color - should preferably be a named color from tcod.constants, or a (r,g,b) tuple
    """

    def __init__(self, default: Tuple[int, Tuple[int, int, int, int], Tuple[int, int, int, int]] =
                 (0, (*tcod.white, 255), (*tcod.black, 255))):
        self.icon = default[0]
        self.color = default[1][:3]
        self.fg_alpha = default[1][3]
        self.background = default[2][:3]
        self.bg_alpha = default[2][3]

    @property
    def tile(self):
        return self.icon, (*self.color, self.fg_alpha), (*self.background, self.bg_alpha)

    @tile.setter
    def tile(self, tile_tuple: Tuple[int, Tuple[int, int, int, int], Tuple[int, int, int, int]]):
        self.icon = tile_tuple[0]
        self.color = tile_tuple[1][:3]
        self.fg_alpha = tile_tuple[1][3]
        self.background = tile_tuple[2][:3]
        self.bg_alpha = tile_tuple[2][3]


class Screen(tcod.Console):
    """Holds the reference to the main console window ('screen') as well as the context (SDL binding)

    Extends:
        * the Console class from libTCOD
    Class attributes:
        * _instance - a singleton object of this class
        * _context - SDL context for displaying the main console
    Methods:
        * get - acquire the one and only screen object for the game
        * present - render any sub console from anywhere in the code
    """
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
