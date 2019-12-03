# -*- coding: utf-8 -*-

from json import loads
import logging
from os import path
import random
from mrogue import roll, adjacent
import mrogue.unit
from mrogue.map import Pathfinder


class Menagerie(object):
    game = None
    act_order = None
    ticks_passed = 0

    def __init__(self, game, num):
        self.game = game
        self.log = logging.getLogger(__name__)
        with open(path.join(game.dir, 'monster_templates.json')) as f:
            monster_templates = loads(f.read())
        for i in range(num):
            Monster(self.game, random.choice(monster_templates),
                    (game.level.objects_on_map, game.level.units))

    def handle_monsters(self, target):
        if self.act_order:
            for unit in self.act_order:
                unit.ticks_left = unit.ticks_left - self.ticks_passed
            self.act_order = None
        if not self.act_order:
            self.ticks_passed = min(m.ticks_left for m in self.game.level.units)
            self.act_order = sorted(self.game.level.units, key=lambda m: m.ticks_left)
        while self.act_order and self.act_order[0].ticks_left == self.ticks_passed:
            unit = self.act_order.pop(0)
            if unit.name != 'Player':
                unit.act(target)
            else:
                for unit in self.game.level.units:
                    unit.update()
                self.game.player.ticks_left = int(self.game.player.speed * 100)
                return True
        return False


class Monster(mrogue.unit.Unit):
    def __init__(self, game, template, groups):
        super().__init__(template['name'],
                         game,
                         (template['icon'], template['color']),
                         10,
                         template['speed'],
                         template['to_hit'],
                         template['dmg_die_unarmed'],
                         template['ac'],
                         roll(template['hit_die']))
        self.path = None
        self.log = logging.getLogger(__name__)
        if 'weapon' in template:
            self.game.items.random_item(template['weapon'], self.inventory)
        for item in self.inventory:
            self.equip(item, True)
        for group in groups:
            group.append(self)
        self.log.debug('Created monster {} at {},{}'.format(
            self.name, self.pos[0], self.pos[1]))

    def act(self, target):
        if self.is_in_range(target.pos):
            # if self.senses_or_reacts_in_some_way_to(target)
            if adjacent(self.pos, target.pos):
                self.log.debug('{} is in melee range - attacking {}'.format(
                    self.name, target.name))
                self.path = None
                self.attack(target)
            else:
                self.approach(target.pos)
        else:
            self.wander()
        self.ticks_left = int(self.speed * 100)

    def is_in_range(self, target_position):
        return abs(self.pos[0] - target_position[0]) <= self.sight_range and \
               abs(self.pos[1] - target_position[1]) <= self.sight_range

    def approach(self, goal):
        if self.path:  # if already on a path
            if goal != self.path[-1]:  # if target moved, find new path
                self.path = Pathfinder(self.game.level,
                                       self.pos).find(goal).path(self.pos, goal)
        else:  # find a path to target
            self.path = Pathfinder(self.game.level,
                                   self.pos).find(goal).path(self.pos, goal)
        if self.game.level.unit_at(self.path[0]):
            tiles = self.game.level.neighbors(self.pos)
            tiles = list(filter(lambda p: not self.game.level.unit_at(p),
                                tiles))
            pairs = [(abs(goal[0] - x), abs(goal[1] - y), (x, y))
                     for x, y in tiles]
            if not pairs:
                return
            nearest = min(pairs, key=lambda v: v[0] * v[0] + v[1] * v[1])[2]
            self.game.level.movement(self, nearest)
            return
        self.game.level.movement(self, self.path.pop(0))

    def wander(self):
        self.game.level.movement(
            self,
            random.choice(list(filter(lambda p: not self.game.level.unit_at(p),
                                      self.game.level.neighbors(self.pos)))))
