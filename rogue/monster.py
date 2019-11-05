# -*- coding: utf-8 -*-

import json
import logging
import os
import random
from pygame import sprite
from rogue import roll, adjacent
import rogue.unit
from rogue.map import Pathfinder


class Menagerie(object):
    game = None
    monsterList = sprite.Group()

    def __init__(self, game, num):
        self.game = game
        basedir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(basedir, 'monster_templates.json')) as f:
            monster_templates = json.loads(f.read())
        for i in range(num):
            Monster(self.game, random.choice(monster_templates),
                    (self.monsterList, game.interface.objects_on_map,
                     game.interface.units))

    def handle_monsters(self, target):
        for monster in self.monsterList:
            if monster.is_in_range(target.pos):
                # if monster.senses_or_reacts_in_some_way_to(target)
                if adjacent(monster.pos, target.pos):
                    logging.debug('{} is in melee range - attacking {}'.format(
                        monster.name, target.name))
                    monster.path = None
                    monster.attack(target)
                else:
                    monster.approach(target.pos)


class Monster(rogue.unit.Unit):
    path = None

    def __init__(self, game, template, groups):
        super().__init__(template['name'], game, template['tile'], 5,
                         template['to_hit'], template['dmg_die'],
                         template['ac'], roll(template['hit_die']))
        if 'wields' in template:
            self.image.blit(game.interface.tileset[template['wields']], (-2, 6))
        self.add(groups)
        logging.debug('Created monster {} at {},{}'.format(
            self.name, self.pos[0], self.pos[1]))

    def is_in_range(self, target_position):
        return abs(self.pos[0] - target_position[0]) <= self.sight_range and \
               abs(self.pos[1] - target_position[1]) <= self.sight_range

    def approach(self, goal):
        if self.path:  # if already on a path
            if goal != self.path[-1]:  # if target moved, find new path
                self.path = Pathfinder(self.game.level, self.pos).find(goal).path(self.pos, goal)
        else:  # find a path to target
            self.path = Pathfinder(self.game.level, self.pos).find(goal).path(self.pos, goal)
        if self.game.interface.unit_at(self.path[0]):
            tiles = self.game.level.neighbors(self.pos)
            tiles = list(filter(lambda p: not self.game.interface.unit_at(p), tiles))
            pairs = [(abs(goal[0] - x), abs(goal[1] - y), (x, y)) for x, y in tiles]
            if not pairs:
                return
            nearest = min(pairs, key=lambda v: v[0] * v[0] + v[1] * v[1])[2]
            self.game.level.movement(self, nearest)
            return
        self.game.level.movement(self, self.path.pop(0))
