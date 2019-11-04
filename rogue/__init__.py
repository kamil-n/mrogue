# -*- coding: utf-8 -*-

import logging
import random


def adjacent(fr, to):
    return abs(fr[0] - to[0]) <= 1 and abs(fr[1] - to[1]) <= 1


def roll(die_string, crit=False):
    separator_index = die_string.index('d')
    num_die = int(die_string[:separator_index])
    type_die = die_string[separator_index + 1:]
    if crit:
        num_die *= 2
        die_string = str(num_die) + die_string[separator_index:]
    modifier = 0
    modifier_index = -1
    if '-' in type_die:
        modifier_index = type_die.index('-')
    elif '+' in type_die:
        modifier_index = type_die.index('+')
    if not modifier_index == -1:
        modifier = int(type_die[modifier_index:])
        type_die = int(type_die[:modifier_index])
    else:
        type_die = int(type_die)
    roll_result = 0
    result_string = ''
    for i in range(num_die):
        cast = random.randint(1, type_die)
        result_string += str(cast) + '+'
        roll_result += cast
    roll_result += modifier
    result_string = result_string[:-1]
    if roll_result < 1:
        roll_result = 1
    if modifier < 0:
        result_string += str(modifier)
    elif modifier > 0:
        result_string += '+' + str(modifier)
    # logging.debug('rolling {}: {} = {}'.format(die_string, result_string, roll_result))
    return roll_result
