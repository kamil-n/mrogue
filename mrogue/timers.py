# -*- coding: utf-8 -*-

all_timers = []


class Timer(object):
    def __init__(self, duration, action):
        self.duration = duration
        self.action = action
        all_timers.append(self)

    @staticmethod
    def update():
        for t in all_timers:
            t.tick()

    def tick(self):
        self.duration -= 1
        if self.duration < 0:
            self.action()
            all_timers.remove(self)
