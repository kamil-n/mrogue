# -*- coding: utf-8 -*-


class Timer:
    all_timers = []

    def __init__(self, duration, action):
        self.duration = duration
        self.action = action
        self.all_timers.append(self)

    @classmethod
    def update(cls):
        for t in cls.all_timers:
            t.tick()

    def tick(self):
        self.duration -= 1
        if self.duration < 0:
            self.action()
            self.all_timers.remove(self)
