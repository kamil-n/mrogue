# -*- coding: utf-8 -*-

import random

__version__ = 'v0.2.1.1'


def adjacent(fr, to):
    return abs(fr[0] - to[0]) <= 1 and abs(fr[1] - to[1]) <= 1


def roll(die_string, crit=False):
    num_die, sides, mod = decompile_dmg_die(die_string)
    if crit:
        num_die *= 2
    roll_result = sum([random.randint(1, sides) for i in range(num_die)]) + mod
    return 1 if roll_result < 1 else roll_result


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
