# -*- coding: utf-8 -*-
from __future__ import annotations

import random
import string
from typing import TYPE_CHECKING, Any, Callable, Iterator, Sequence

if TYPE_CHECKING:
    from mrogue import Point


def adjacent(fr: Point, to: Point, distance: int = 1) -> bool:
    return abs(fr.x - to.x) <= distance and abs(fr.y - to.y) <= distance


def find_in(
    where: Sequence[Any],
    attribute: str,
    like: Any,
    instance: type = None,
    many: bool = False,
) -> Any:
    # print(f"finding in {where}\n object with attr {attribute}," \
    #       f"matching {like}, must be {instance}, many={many}:")
    results = []
    if instance:
        where = filter(lambda x: isinstance(x, instance), where)  # type: ignore
    for element in where:
        value = getattr(element, attribute)
        if (type(value) if type(like) == type else value) == like:
            if many:
                results.append(element)
            else:
                return element
    return results or None


def print_result(func: Callable[..., Any]) -> Callable[..., Any]:
    def decorator(*args: Any, **kwargs: Any) -> Any:
        value = func(*args, **kwargs)
        print(f"{func.__name__}{args}: {value}")
        return value

    return decorator


def roll(left: int, right: int, critical: bool = False) -> int:
    roll_result = random.randint(max(0, left), max(0, right))
    return roll_result + (roll_result // 2 if critical else 0)


def random_scroll_name() -> str:
    name = ""
    for i in range(random.randint(1, 3)):
        for j in range(random.randint(3, 5)):
            name += random.choice(string.ascii_uppercase)
        name += " "
    return name.rstrip()


def circular(sequence: Sequence[Any]) -> Iterator[Any]:
    while sequence:
        for element in sequence:
            yield element
