# -*- coding: utf-8 -*-

import random
import tcod.event

__version__ = 'v0.4.1.3'


def adjacent(fr, to):
    return abs(fr[0] - to[0]) <= 1 and abs(fr[1] - to[1]) <= 1


def roll(die_string, crit=False):
    num_die, sides, mod = decompile_dmg_die(die_string)
    if crit:
        num_die *= 2
    roll_result = sum([random.randint(1, sides) for i in range(num_die)]) + mod
    return 1 if roll_result < 1 else roll_result


def test_gauss(left, right, deviation, iterations):
    """ This should be ran before any new limits for roll_gaussian are
    introduced to tweak the standard deviation. Optimal deviations:
    1-3: 0.8
    1-5: 1.0
    1-7: 1.2
    etc. """
    offset = 0 - left
    results = [0 for i in range(right - left + 1)]
    for i in range(iterations):
        num = roll_gaussian(left, right, deviation)
        # num = roll_triangular(left, right)
        results[num + offset] += 1
    print('gauss for {}-{} is:.'.format(left, right))
    for i in range(len(results)):
        print('{}: {}'.format(i + (-1 * offset), results[i]))


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


def wait(character = None):
    while True:
        for event in tcod.event.wait():
            if event.type == 'QUIT':
                raise SystemExit
            elif event.type == 'KEYDOWN':
                if character:
                    if event.sym == character:
                        return True
                else:
                    return event.sym
