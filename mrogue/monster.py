# -*- coding: utf-8 -*-

import random
import mrogue.item
import mrogue.map
import mrogue.monster_data
import mrogue.player
import mrogue.unit
import mrogue.utils


class MonsterManager:
    order = None
    ticks_passed = 0
    selection_for_level = []

    def __init__(self):
        for i in range(8+1):
            this_level = []
            for group, data in mrogue.monster_data.templates.items():
                if i in data['occurrences'].keys():
                    this_level.append(group)
            self.selection_for_level.append(this_level)

    @classmethod
    def create_monsters(cls, num, depth, **kwargs):
        level = mrogue.map.Dungeon.current_level
        for i in range(num + depth):
            group = random.choice(cls.selection_for_level[depth])
            template = random.choices(
                mrogue.monster_data.templates[group]['subtypes'],
                mrogue.monster_data.templates[group]['occurrences'][depth])[0]
            m = Monster(template, (level.objects_on_map, level.units))
            if kwargs:
                for key, val in kwargs.items():
                    setattr(m, key, val)

    @classmethod
    def handle_monsters(cls, target):
        if cls.order:
            for monster in cls.order:
                monster.ticks_left = monster.ticks_left - cls.ticks_passed
            cls.order = None
        if not cls.order:
            cls.ticks_passed = min(m.ticks_left for m in mrogue.map.Dungeon.current_level.units)
            cls.order = sorted(mrogue.map.Dungeon.current_level.units, key=lambda m: m.ticks_left)
        player = mrogue.player.Player.get()
        while cls.order and cls.order[0].ticks_left == cls.ticks_passed:
            monster = cls.order.pop(0)
            if not monster.player and player.current_HP > 0:
                monster.act(target)
            else:
                for monster in mrogue.map.Dungeon.current_level.units:
                    monster.update()
                if player.speed != 0.0:
                    player.ticks_left = int(
                        player.speed * 100)
                else:
                    player.ticks_left = 100.0
                return True
        return False

    @classmethod
    def stop_monsters(cls):
        for monster in mrogue.map.Dungeon.current_level.units:
            if hasattr(monster, 'path'):
                monster.path = None
        cls.order.clear()


class Monster(mrogue.unit.Unit):
    def __init__(self, template, groups):
        super().__init__(template['name'],
                         (template['icon'], template['color']),
                         10,
                         template['ability_scores'],
                         template['keywords'],
                         template['speed'],
                         template['proficiency'],
                         template['dmg_die_unarmed'],
                         template['ac_bonus'],
                         mrogue.utils.roll(template['hit_die']))
        self.path = None
        if 'weapon' in template and random.randint(0, 1):
            mrogue.item.ItemManager.random_item(template['weapon'], self.inventory)
        for group in groups:
            group.append(self)

    def act(self, target):
        if self.is_in_range(target.pos):
            # if self.senses_or_reacts_in_some_way_to(target)
            if mrogue.utils.adjacent(self.pos, target.pos):
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
        player = mrogue.player.Player.get()
        if self.path:  # if already on a path
            if goal != self.path[-1]:  # if target moved, find new path
                self.path = player.dijsktra_map.get_path(*self.pos)
                self.path.pop()
        else:  # find a path to target
            self.path = player.dijsktra_map.get_path(*self.pos)
            self.path.pop()
        if mrogue.map.Dungeon.unit_at(self.path[-1]):
            self.wander(goal)
            return
        mrogue.map.Dungeon.movement(self, self.path.pop())

    def wander(self, towards=None):
        free_spots = list(filter(
                lambda p: not mrogue.map.Dungeon.unit_at(p),
                mrogue.map.Dungeon.neighbors(self.pos)))
        if len(free_spots) > 0:
            to = None
            if towards:
                pairs = [(abs(towards[0] - x), abs(towards[1] - y), (x, y)) for x, y in free_spots]
                if pairs:
                    to = min(pairs, key=lambda v: v[0] * v[0] + v[1] * v[1])[2]
            else:
                to = random.choice(free_spots)
            mrogue.map.Dungeon.movement(self, to)
