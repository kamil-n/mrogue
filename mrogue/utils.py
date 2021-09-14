# -*- coding: utf-8 -*-

import random
import string
from mrogue.io import Char


def adjacent(fr, to, range=1):
    return abs(fr[0] - to[0]) <= range and abs(fr[1] - to[1]) <= range


def find_in(where, attribute, like, many=False):
    results = []
    for element in where:
        if getattr(element, attribute) == like:
            if many:
                results.append(element)
            else:
                return element
    return results or None


def roll(die_string, crit=False):
    num_die, sides, mod = decompile_dmg_die(die_string)
    if crit:
        num_die *= 2
    roll_result = sum([random.randint(1, sides) for i in range(num_die)]) + mod
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


def cap(word):
    return word[0].upper() + word[1:]


def random_scroll_name():
    name = ''
    for i in range(random.randint(1, 3)):
        for j in range(random.randint(3, 5)):
            name += random.choice(string.ascii_uppercase)
        name += ' '
    return name.rstrip()


class Instance(Char):
    def __init__(self):
        super().__init__()
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
