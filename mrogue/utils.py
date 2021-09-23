# -*- coding: utf-8 -*-
""" A collection of small functions used in the whole project"""
import random
import string


def adjacent(fr: tuple[int, int], to: tuple[int, int], distance: int = 1) -> bool:
    """Check if target is right next to source cell

    :param fr: source cell coordinates
    :param to: target cell coordinates
    :param distance: optional, can check longer distances than immediate vicinity
    :return: True if target is next to source, False otherwise
    """
    return abs(fr[0] - to[0]) <= distance and abs(fr[1] - to[1]) <= distance


def find_in(where: list or tuple, attribute: str, like: object,
            instance: type = None, many: bool = False) -> object or list[object]:
    """Generic function to find an item (or multiple) within an iterable with specific attribute

    :param where: collection to search in
    :param attribute: name of the attribute to compare
    :param like: value to compare against
    :param instance: optional: only consider object of this class
    :param many: if the function should return a list of multiple matches or just the first one
    :return: either a list of found elements, a single element or nothing
    """
    # print(f"finding in {where}\n object with attr {attribute}, matching {like}, must be {instance}, many={many}:")
    results = []
    if instance:
        where = filter(lambda x: isinstance(x, instance), where)
    for element in where:
        if getattr(element, attribute) == like:
            if many:
                results.append(element)
            else:
                return element
    return results or None


def roll(dice_string: str, critical: bool = False) -> int:
    """Roll the dice. Dice string must be in the format "<how_many>d<sided-dice>[+<modifier>]"

    :param dice_string: what to roll: string formated as <num>d<sided>[+/-<mod>]
    :param critical: according to DnD rules, if critical success, roll the dice twice
    :return: a random number but no less than 1
    """
    num_dice, sides, mod = decompile_dmg_dice(dice_string)
    if critical:
        num_dice *= 2
    roll_result = sum([random.randint(1, sides) for _ in range(num_dice)]) + mod
    return 1 if roll_result < 1 else roll_result


def roll_gaussian(left: int, right: int, deviation: float = 1.0) -> int:
    """Random number with more even distribution

    :param left: minimum number to pick
    :param right: maximum number to pick
    :param deviation: the standard deviation for the gaussian distribution
    :return: the random number but weighted according to gaussian distribution
    """
    return min(right, max(left, round(random.gauss((right - left) // 2 + 1, deviation))))


def decompile_dmg_dice(dice_string: str) -> tuple[int, int, int]:
    """Transform dice string into a tuple of integers for each component

    :param dice_string: string formatted as <x>d<y>[+/-<z>]
    :return: a tuple containing the components as integers
    """
    separator_index = dice_string.index('d')
    num_dice = int(dice_string[:separator_index])
    sides = dice_string[separator_index + 1:]
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
    return num_dice, sides, modifier


def compile_dmg_dice(num_dice: int, sides: int, modifier: int) -> str:
    """Make a dice string out of a tuple of integers

    :param num_dice: number of dice
    :param sides: type of dice (how many sides)
    :param modifier: flat modifier to be added or subtracted from the roll
    :return: a string in the format of <num_dice>d<sides>[+/-<modifier>]
    """
    return f'{num_dice}d{sides}' + (f'{modifier:+d}' if modifier else '')


def random_scroll_name() -> str:
    """Create one to three words made of random letters

    :return: 1 -3 words 3-5 letters each separated by single spaces
    """
    name = ''
    for i in range(random.randint(1, 3)):
        for j in range(random.randint(3, 5)):
            name += random.choice(string.ascii_uppercase)
        name += ' '
    return name.rstrip()


def print_result(func):
    """A decorator to print return value from a function/method"""
    def decorator(*args, **kwargs):
        value = func(*args, **kwargs)
        print(f'{func.__name__}: {value}')
        return value
    return decorator
