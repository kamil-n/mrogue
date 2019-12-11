# -*- coding: utf-8 -*-

from json import loads
from os import path
import random
from mrogue import roll, adjacent
import mrogue.unit


class MonsterManager(object):
    game = None
    order = None
    ticks_passed = 0

    def __init__(self, game):
        self.game = game
        with open(path.join(game.dir, 'monster_templates.json')) as f:
            self.monster_templates = loads(f.read())

    def create_monsters(self, num):
        for i in range(num):
            Monster(self.game, random.choice(self.monster_templates),
                    (self.game.level.objects_on_map, self.game.level.units))

    def handle_monsters(self, target):
        if self.order:
            for unit in self.order:
                unit.ticks_left = unit.ticks_left - self.ticks_passed
            self.order = None
        if not self.order:
            self.ticks_passed = min(
                m.ticks_left for m in self.game.dungeon.level.units)
            self.order = sorted(self.game.dungeon.level.units,
                                key=lambda m: m.ticks_left)
        while self.order and self.order[0].ticks_left == self.ticks_passed:
            unit = self.order.pop(0)
            if unit.name != 'Player' and self.game.player.current_HP > 0:
                unit.act(target)
            else:
                for unit in self.game.dungeon.level.units:
                    unit.update()
                if self.game.player.speed != 0.0:
                    self.game.player.ticks_left = int(
                        self.game.player.speed * 100)
                else:
                    self.game.player.ticks_left = 100.0
                return True
        return False

    def stop_monsters(self):
        for unit in self.game.dungeon.level.units:
            if hasattr(unit, 'path'):
                unit.path = None
        self.order.clear()


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
        if 'weapon' in template and random.randint(0, 1):
            self.game.items.random_item(template['weapon'], self.inventory)
        for group in groups:
            group.append(self)

    def act(self, target):
        if self.is_in_range(target.pos):
            # if self.senses_or_reacts_in_some_way_to(target)
            if adjacent(self.pos, target.pos):
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
                self.path = self.game.player.dijsktra_map.get_path(*self.pos)
                self.path.pop()
        else:  # find a path to target
            self.path = self.game.player.dijsktra_map.get_path(*self.pos)
            self.path.pop()
        if self.game.dungeon.unit_at(self.path[-1]):
            tiles = self.game.dungeon.neighbors(self.pos)
            tiles = list(filter(lambda p: not self.game.dungeon.unit_at(p),
                                tiles))
            pairs = [(abs(goal[0] - x), abs(goal[1] - y), (x, y))
                     for x, y in tiles]
            if pairs:
                nearest = min(pairs, key=lambda v: v[0] * v[0] + v[1] * v[1])[2]
                self.game.dungeon.movement(self, nearest)
            return
        self.game.dungeon.movement(self, self.path.pop())

    def wander(self):
        self.game.dungeon.movement(
            self,
            random.choice(list(filter(
                lambda p: not self.game.dungeon.unit_at(p),
                self.game.dungeon.neighbors(self.pos)))))
