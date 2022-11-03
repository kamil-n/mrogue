# -*- coding: utf-8 -*-
import random

import tcod

import mrogue.item.manager
import mrogue.map
import mrogue.monster_data
import mrogue.player
import mrogue.unit
import mrogue.utils
from mrogue import Point


class Monster(mrogue.unit.Unit):
    def __init__(self, template, groups):
        super().__init__(
            template["name"],
            (template["icon"], template["color"]),
            10,
            template["ability_scores"],
            template["keywords"],
            template["speed"],
            template["proficiency"],
            template["dmg_range_unarmed"],
            template["ac_bonus"],
            mrogue.utils.roll(*template["hp_range"]),
        )
        self.background = tcod.red * 0.3
        self.path = None
        if "weapon" in template and random.randint(0, 1):
            mrogue.item.manager.ItemManager.random_item(
                template["weapon"], self.inventory
            )
        for group in groups:
            group.append(self)

    def __repr__(self):
        return f"Monster('{self.name}', 0x{self.icon:x})"  # ", {self.color})"

    def act(self, target: mrogue.unit.Unit) -> None:
        if mrogue.utils.adjacent(self.pos, target.pos):
            self.path = None
            self.attack(target)
        else:
            monster_fov = None
            if self.is_in_range(target.pos):
                monster_fov = tcod.map.compute_fov(
                    mrogue.map.Dungeon.current_level.tiles["transparent"],
                    self.pos,
                    self.sight_range,
                )
            if (
                monster_fov is not None
                and monster_fov[target.pos]
                or self.sight_range == 100
            ):
                self.approach(target.pos)
            else:
                if random.random() > 0.5:
                    self.wander()

    def is_in_range(self, target_position: Point) -> bool:
        return (
            abs(self.pos.x - target_position.x) <= self.sight_range
            and abs(self.pos.y - target_position.y) <= self.sight_range
        )

    def approach(self, goal: Point) -> None:
        if self.path:  # if already on a path
            if goal != self.path[-1]:  # if target moved, find new path
                self.path = mrogue.player.Player.get().dijkstra_map.get_path(*self.pos)
                self.path.pop()
        else:  # find a path to target
            self.path = mrogue.player.Player.get().dijkstra_map.get_path(*self.pos)
            self.path.pop()
        if mrogue.map.Dungeon.unit_at(self.path[-1]):
            self.wander(goal)
            return
        mrogue.map.Dungeon.movement(self, Point(*self.path.pop()))

    def wander(self, towards: Point = None):
        free_spots = list(
            filter(
                lambda p: not mrogue.map.Dungeon.unit_at(p),
                mrogue.map.Dungeon.neighbors(self.pos),
            )
        )
        if len(free_spots) > 0:
            to = None
            if towards:
                pairs = [
                    (abs(towards.x - x), abs(towards.y - y), Point(x, y))
                    for x, y in free_spots
                ]
                if pairs:
                    to = min(pairs, key=lambda v: v[0] * v[0] + v[1] * v[1])[2]
            else:
                to = random.choice(free_spots)
            mrogue.map.Dungeon.movement(self, to)


class MonsterManager:
    order = None
    acting_initiative = 0
    selection_for_level = []

    def __init__(self):
        for i in range(8 + 1):
            this_level = []
            for group, data in mrogue.monster_data.templates.items():
                if i in data["occurrences"].keys():
                    this_level.append(group)
            self.selection_for_level.append(this_level)

    @classmethod
    def create_monsters(cls, num: int, depth: int) -> None:
        level = mrogue.map.Dungeon.current_level
        for i in range(num + depth):
            group = random.choice(cls.selection_for_level[depth])
            template = random.choices(
                mrogue.monster_data.templates[group]["subtypes"],
                mrogue.monster_data.templates[group]["occurrences"][depth],
            )[0]
            Monster(template, (level.objects_on_map, level.units))

    @classmethod
    def spawn_monster(cls, depth: int, **kwargs) -> None:
        level = mrogue.map.Dungeon.current_level
        group = random.choice(cls.selection_for_level[depth])
        template = random.choices(
            mrogue.monster_data.templates[group]["subtypes"],
            mrogue.monster_data.templates[group]["occurrences"][depth],
        )[0]
        m = Monster(template, (level.objects_on_map, level.units))
        while True:
            pos = Point(*random.choice(level.floor))
            if not mrogue.player.Player.get().fov[pos]:
                break
        setattr(m, "pos", pos)
        if kwargs:
            for key, val in kwargs.items():
                setattr(m, key, val)

    @classmethod
    def handle_monsters(cls, target: mrogue.unit.Unit) -> None:
        player = mrogue.player.Player.get()
        while True:
            if cls.order:
                for unit in cls.order:
                    unit.initiative -= cls.acting_initiative
            cls.order = sorted(
                mrogue.map.Dungeon.current_level.units, key=lambda m: m.initiative
            )
            cls.acting_initiative = cls.order[0].initiative
            while cls.order[0].initiative == cls.acting_initiative:
                unit = cls.order.pop(0)
                unit.update()
                if not unit.player and player.current_HP > 0:
                    unit.act(target)
                else:
                    return

    @classmethod
    def stop_monsters(cls) -> None:
        for monster in mrogue.map.Dungeon.current_level.units:
            if hasattr(monster, "path"):
                monster.path = None
        cls.order.clear()
