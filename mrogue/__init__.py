# -*- coding: utf-8 -*-

import random
import string
from numpy import asarray
import tcod.console
import tcod.event

__version__ = 'v0.4.8.1'


directions = asarray([
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


class Char:
    def __init__(self):
        self.icon = ''
        self.color = tcod.white
        self._groups = []

    def add(self, *groups):
        for group in groups:
            if group is not None:
                group.append(self)
                if group not in self._groups:
                    self._groups.append(group)

    def remove(self, *groups):
        for group in groups:
            if self in group:
                group.remove(self)
            if group in self._groups:
                self._groups.remove(group)

    def kill(self):
        for group in self._groups:
            group.remove(self)
            self._groups.remove(group)


def adjacent(fr, to, range=1):
    return abs(fr[0] - to[0]) <= range and abs(fr[1] - to[1]) <= range


def roll(die_string, crit=False):
    num_die, sides, mod = decompile_dmg_die(die_string)
    if crit:
        num_die *= 2
    roll_result = sum([random.randint(1, sides) for i in range(num_die)]) + mod
    return 1 if roll_result < 1 else roll_result


def roll_gaussian(left, right, deviation=1.0):
    return min(right, max(left, round(random.gauss((right - left) // 2 + 1,
                                                   deviation))))


def roll_triangular(left, right):
    return round(random.triangular(left, right))


def decompile_dmg_die(die_string):
    separator_index = die_string.index('d')
    num_die = int(die_string[:separator_index])
    sides = die_string[separator_index + 1:]
    modifier = 0
    modifier_index = -1
    if '-' in sides:
        modifier_index = sides.index('-')
    elif '+' in sides:
        modifier_index = sides.index('+')
    if not modifier_index == -1:
        modifier = int(sides[modifier_index:])
        sides = int(sides[:modifier_index])
    else:
        sides = int(sides)
    return num_die, sides, modifier


def compile_dmg_die(num_die, sides, modifier):
    die_string = '{}d{}'.format(num_die, sides)
    if modifier != 0:
        die_string += '{:+d}'.format(modifier)
    return die_string


def die_range(die_string):
    num, sides, mod = decompile_dmg_die(die_string)
    return num + mod if num + mod > 0 else 1, num * sides + mod


def cap(word):
    return word[0].upper() + word[1:]


ignore_keys = (
    tcod.event.K_LALT, tcod.event.K_RALT,
    tcod.event.K_LSHIFT, tcod.event.K_RSHIFT,
    tcod.event.K_LCTRL, tcod.event.K_RCTRL)


ignore_mods = tcod.event.KMOD_NUM


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


def select_option(screen, context, options):
    num_options = len(options)
    w, h = 23, num_options + 2
    dialog = tcod.console.Console(w, h, 'F')
    dialog.draw_frame(0, 0, w, h, 'Select an action:')
    for i in range(num_options):
        dialog.print(2, i + 1, '{}) {}'.format(options[i][0], options[i][1]))
    dialog.blit(screen, 4 + 10, 4 + 1)
    context.present(screen)


def random_scroll_name():
    name = ''
    for i in range(random.randint(1, 3)):
        for j in range(random.randint(3, 5)):
            name += random.choice(string.ascii_uppercase)
        name += ' '
    return name.rstrip()
