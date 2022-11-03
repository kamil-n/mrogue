# -*- coding: utf-8 -*-
import string
from os import path
from typing import Callable, NamedTuple, Tuple

import numpy as np
import tcod.event

import mrogue

directions = np.asarray(
    [
        [
            [0, tcod.event.K_UP, 0],
            [tcod.event.K_LEFT, 0, tcod.event.K_RIGHT],
            [0, tcod.event.K_DOWN, 0],
        ],
        [
            [tcod.event.K_KP_7, tcod.event.K_KP_8, tcod.event.K_KP_9],
            [tcod.event.K_KP_4, tcod.event.K_KP_5, tcod.event.K_KP_6],
            [tcod.event.K_KP_1, tcod.event.K_KP_2, tcod.event.K_KP_3],
        ],
        [[55, 56, 57], [52, 53, 54], [49, 50, 51]],
    ]
)

ignore_keys = (
    tcod.event.K_LALT,
    tcod.event.K_RALT,
    tcod.event.K_LSHIFT,
    tcod.event.K_RSHIFT,
    tcod.event.K_LCTRL,
    tcod.event.K_RCTRL,
)

ignore_mods = tcod.event.KMOD_NUM

# type hints
KEY = tcod.event.KeyDown
MOD = tcod.event.Modifier


def direction_from(key: KEY, pos: mrogue.Point) -> mrogue.Point:
    placement = np.nonzero(directions == key)
    return mrogue.Point(pos.x + placement[2][0] - 1, pos.y + placement[1][0] - 1)


def key_is(
    key: tuple[KEY, MOD], target_key: KEY, target_mod: MOD = tcod.event.KMOD_NONE
) -> bool:
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
    while True:
        for event in tcod.event.wait():
            if event.type == "QUIT":
                raise SystemExit
            # don't consider modifiers to be key presses
            elif event.type == "KEYDOWN" and event.sym not in ignore_keys:
                if character:
                    if key_is((event.sym, event.mod), character, mod):
                        return event.sym, event.mod
                else:
                    return event.sym, event.mod


def help_screen() -> None:
    help_contents = [
        "Kill all monsters. To attack, 'walk' into them.",
        "Move with keyboard arrows, numpad or number keys.",
        "Directions for number keys:",
        "7\\ 8 /9",
        "4- @ -6      (press 5 to pass turn)",
        "1/ 2 \\3",
        "Shift + direction = autorun.",
        "Other keys:",
        "e  - open equipment screen. Press slot hotkeys to unequip items.",
        "i  - open inventory screen. Press hotkeys to manage items.",
        ", (comma) - pick up items",
        ">  - descend to next level while standing on this icon.",
        "<  - ascend back to previous level while standing on this icon.",
        "M  - show message history.",
        "H  - show this help screen.",
        "Q  - close game when on main screen",
        "^R - cycle tileset (font)",
        "",
        "Esc - close pop-up windows like this one.",
    ]
    width = 2 + max([len(line) for line in help_contents])
    height = 2 + len(help_contents)
    window = tcod.Console(width, height, "F")
    window.draw_frame(
        0, 0, width, height, f"Welcome to MRogue {mrogue.__version__}!", False
    )
    for i in range(len(help_contents)):
        window.print(1, i + 1, help_contents[i])
    window.blit(Screen.get(), 12, 12, bg_alpha=0.95)
    Screen.get().present()
    wait(tcod.event.K_ESCAPE)


def select_action(
    options: list[tuple[str, object, Callable]]
) -> tuple[bool, bool or None]:
    w, h = 23, len(options) + 2
    dialog = tcod.console.Console(w, h, "F")
    dialog.draw_frame(0, 0, w, h, "Select an action:")
    for row, option in enumerate(options):
        dialog.print(2, row + 1, f"{string.ascii_letters[row]}) {option[0]}")
        dialog.blit(Screen.get(), 4 + 10, 4 + 1)
        Screen.get().present()
    while True:
        selection = mrogue.io.wait()
        if mrogue.io.key_is(selection, tcod.event.K_ESCAPE):
            return False, None
        elif selection[0] in range(97, 97 + len(options)):
            selected = selection[0] - 97
            return True, options[selected][2](options[selected][1])


tile_dt = np.dtype(
    [
        ("walkable", bool),
        ("transparent", bool),
        ("lit", tcod.console.rgba_graphic),
        ("dim", tcod.console.rgba_graphic),
    ]
)


class Tile(NamedTuple):
    walkable: bool
    transparent: bool
    lit: Tuple[int, Tuple[int, int, int, int], Tuple[int, int, int, int]]
    dim: Tuple[int, Tuple[int, int, int, int], Tuple[int, int, int, int]]


class Glyph:
    def __init__(
        self,
        default: Tuple[int, Tuple[int, int, int, int], Tuple[int, int, int, int]] = (
            0,
            (*tcod.white, 255),
            (*tcod.black, 255),
        ),
    ):
        self.icon = default[0]
        self.color = default[1][:3]
        self.fg_alpha = default[1][3]
        self.background = default[2][:3]
        self.bg_alpha = default[2][3]

    @property
    def tile(self):
        return (
            self.icon,
            (*self.color, self.fg_alpha),
            (*self.background, self.bg_alpha),
        )

    @tile.setter
    def tile(
        self,
        tile_tuple: Tuple[int, Tuple[int, int, int, int], Tuple[int, int, int, int]],
    ):
        self.icon = tile_tuple[0]
        self.color = tile_tuple[1][:3]
        self.fg_alpha = tile_tuple[1][3]
        self.background = tile_tuple[2][:3]
        self.bg_alpha = tile_tuple[2][3]


class Screen(tcod.Console):
    _instance = None
    _context = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Screen, cls).__new__(cls)
        return cls._instance

    def __init__(self, width, height, font):
        super().__init__(width, height, "F")
        Screen._context = tcod.context.new(
            columns=width,
            rows=height,
            tileset=font,
            renderer=tcod.RENDERER_SDL2,
            title=f"MRogue {mrogue.__version__}",
        )
        Screen.cols, Screen.rows = width, height

    @classmethod
    def get(cls):
        return cls._instance

    @classmethod
    def present(cls, *args, **kwargs):
        cls._context.present(Screen._instance, *args, **kwargs)

    @classmethod
    def change_font(cls, font):
        new_font = tcod.tileset.load_tilesheet(
            path.join(mrogue.work_dir, "data", font[0]),
            16,
            16,
            tcod.tileset.CHARMAP_CP437,
        )
        cls._context.change_tileset(new_font)
        cls._context.sdl_window.size = cls.cols * font[1][0], cls.rows * font[1][1]
        # cls._instance = cls._context.new_console(order='F')
