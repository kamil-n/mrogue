# -*- coding: utf-8 -*-

import random
import string


def adjacent(fr, to, distance=1):
    return abs(fr[0] - to[0]) <= distance and abs(fr[1] - to[1]) <= distance


def find_in(where, attribute, like, many=False):
    results = []
    for element in where:
        if getattr(element, attribute) == like:
            if many:
                results.append(element)
            else:
                return element
    return results or None


def roll(die_string, critical=False):
    num_die, sides, mod = decompile_dmg_die(die_string)
    if critical:
        num_die *= 2
    roll_result = sum([random.randint(1, sides) for _ in range(num_die)]) + mod
    return 1 if roll_result < 1 else roll_result


def roll_gaussian(left, right, deviation=1.0):
    return min(right, max(left, round(random.gauss((right - left) // 2 + 1, deviation))))


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


def random_scroll_name():
    name = ''
    for i in range(random.randint(1, 3)):
        for j in range(random.randint(3, 5)):
            name += random.choice(string.ascii_uppercase)
        name += ' '
    return name.rstrip()
