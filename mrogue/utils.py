# -*- coding: utf-8 -*-
""" A collection of small functions used in the whole project"""
from __future__ import annotations

import random
import string
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mrogue import Point


def adjacent(fr: Point, to: Point, distance: int = 1) -> bool:
    """Check if target is right next to source cell

    :param fr: source cell coordinates
    :param to: target cell coordinates
    :param distance: optional, can check longer distances than immediate vicinity
    :return: True if target is next to source, False otherwise
    """
    return abs(fr.x - to.x) <= distance and abs(fr.y - to.y) <= distance


def find_in(
    where: list or tuple,
    attribute: str,
    like: object,
    instance: type = None,
    many: bool = False,
) -> object or list[object]:
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


def print_result(func):
    """A decorator to print return value from a function/method"""

    def decorator(*args, **kwargs):
        value = func(*args, **kwargs)
        print(f"{func.__name__}{args}: {value}")
        return value

    return decorator


def roll(left: int, right: int, critical: bool = False) -> int:
    """Return a random number in the requested range

    :param left: min possible value
    :param right: max possible value
    :param critical: add half the value
    :return: a random number but no less than 1
    """
    roll_result = random.randint(max(0, left), max(0, right))
    return roll_result + (roll_result // 2 if critical else 0)


def random_scroll_name() -> str:
    """Create one to three words made of random letters

    :return: 1 -3 words 3-5 letters each separated by single spaces
    """
    name = ""
    for i in range(random.randint(1, 3)):
        for j in range(random.randint(3, 5)):
            name += random.choice(string.ascii_uppercase)
        name += " "
    return name.rstrip()


def circular(sequence):
    """Pick next item from the sequence indefinitely"""
    while sequence:
        for element in sequence:
            yield element
