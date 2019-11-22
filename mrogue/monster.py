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
    monsterList = []

    def __init__(self, game, num):
        self.game = game
        self.log = logging.getLogger(__name__)
        with open(path.join(game.dir, 'monster_templates.json')) as f:
            monster_templates = loads(f.read())
        for i in range(num):
            Monster(self.game, random.choice(monster_templates),
                    (self.monsterList, game.level.objects_on_map,
                     game.level.units))

    def handle_monsters(self, target):
        for monster in self.monsterList:
            if monster.is_in_range(target.pos):
                # if monster.senses_or_reacts_in_some_way_to(target)
                if adjacent(monster.pos, target.pos):
                    self.log.debug('{} is in melee range - attacking {}'.format(
                        monster.name, target.name))
                    monster.path = None
                    monster.attack(target)
                else:
                    monster.approach(target.pos)
            else:
                monster.wander()
        for unit in self.game.level.units:
            unit.update()


class Monster(mrogue.unit.Unit):
    def __init__(self, game, template, groups):
        super().__init__(template['name'],
                         game,
                         (template['icon'], template['color']),
                         10,
                         template['to_hit'],
                         template['dmg_die'],
                         template['ac'],
                         roll(template['hit_die']))
        self.path = None
        self.log = logging.getLogger(__name__)
        for group in groups:
            group.append(self)
        self.log.debug('Created monster {} at {},{}'.format(
            self.name, self.pos[0], self.pos[1]))

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
