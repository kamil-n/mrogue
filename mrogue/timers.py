# -*- coding: utf-8 -*-
"""implements Timer class and nothing else

Classes:
    * Timer - keeping time for various Effects
"""
from typing import Callable


class Timer:
    """Updates and applies Effects after certain amount of turns passes

    Class attributes:
        * all_timers - list of all active Timers
    Object attributes:
        * duration - how many turns left until action is taken
        * action - what to do when Timer expires
    Methods:
        * update() - advances time on a Timer
        * tick() - takes action and expires a Timer when it's time comes
    """
    all_timers = []

    def __init__(self, duration: int, action: Callable):
        self._duration = duration
        self._action = action
        Timer.all_timers.append(self)

    @classmethod
    def update(cls) -> None:
        """Advance the time (turns) for each active Timer"""
        for t in cls.all_timers:
            t.tick()

    def tick(self) -> None:
        """Decrease the remaining turns and perform scheduled action when they reach 0, then remove self"""
        self._duration -= 1
        if self._duration < 1:
            self._action()
            self.all_timers.remove(self)
