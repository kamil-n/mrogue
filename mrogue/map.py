# -*- coding: utf-8 -*-
import random
from collections import defaultdict
from os import path
from sys import argv
from typing import Callable

import numpy as np
import tcod.bsp
import tcod.map

import mrogue.io
import mrogue.item.item
import mrogue.message
import mrogue.monster
import mrogue.player
import mrogue.unit
import mrogue.utils
from mrogue import Point

tiles = {
    "wall": mrogue.io.Tile(
        walkable=False,
        transparent=False,
        lit=(0x2588, (192, 192, 192, 255), (32, 32, 32, 255)),
        dim=(0x2588, (64, 64, 64, 255), (0, 0, 0, 255)),
    ),
    "floor": mrogue.io.Tile(
        walkable=True,
        transparent=True,
        lit=(0xB7, (192, 192, 192, 255), (32, 32, 32, 255)),
        dim=(0xB7, (64, 64, 64, 255), (0, 0, 0, 255)),
    ),
    "stairs_down": mrogue.io.Tile(
        walkable=True,
        transparent=True,
        lit=(0x2265, (192, 192, 0, 255), (32, 32, 32, 255)),
        dim=(0x2265, (64, 64, 0, 255), (0, 0, 0, 255)),
    ),
    "stairs_up": mrogue.io.Tile(
        walkable=True,
        transparent=False,
        lit=(0x2264, (192, 192, 0, 255), (32, 32, 32, 255)),
        dim=(0x2264, (64, 64, 0, 255), (0, 0, 0, 255)),
    ),
}
compare = {
    "wall": np.asarray(tiles["wall"], dtype=mrogue.io.tile_dt),
    "floor": np.asarray(tiles["floor"], dtype=mrogue.io.tile_dt),
    "stairs_down": np.asarray(tiles["stairs_down"], dtype=mrogue.io.tile_dt),
    "stairs_up": np.asarray(tiles["stairs_up"], dtype=mrogue.io.tile_dt),
}


class Level:
    class Room:
        rooms_list = []

        def __init__(self, col, row, x, y, w, h):
            self.col, self.row = col, row
            self.x, self.y = col + x, row + y
            self.width, self.height = w, h
            self.is_connected = False
            self.connected = []
            Level.Room.rooms_list.append(self)

        def get_neighbors(self):
            rooms_in_row = [r for r in Level.Room.rooms_list if r.row == self.row]
            rooms_in_col = [r for r in Level.Room.rooms_list if r.col == self.col]
            row_index = rooms_in_row.index(self)
            col_index = rooms_in_col.index(self)
            neighbors = []
            for i in (row_index - 1, row_index + 1):
                if i > -1 and i < len(rooms_in_row):
                    neighbors.append(rooms_in_row[i])
            for i in (col_index - 1, col_index + 1):
                if i > -1 and i < len(rooms_in_col):
                    neighbors.append(rooms_in_col[i])
            return neighbors

        def connect(self, other, level):
            self.is_connected = other.is_connected = True
            self.connected.append(other)
            other.connected.append(self)
            level.tunnel(
                self.x + self.width // 2,
                self.y + self.height // 2,
                other.x + other.width // 2,
                other.y + other.height // 2,
            )

        def get_connected_neighbors(self):
            return list(filter(lambda x: x.is_connected, self.get_neighbors()))

    def __init__(self, dimensions: Point):
        self.mapDim = dimensions
        self.objects_on_map = []
        self.units = []
        self.pos = None
        self.floor = None

        # first, everything is solid
        self.tiles = np.empty(self.mapDim, mrogue.io.tile_dt, "F")
        self.tiles[:] = tiles["wall"]
        self.explored = np.zeros(self.mapDim, bool, "F")

    def create_level(self, first: bool = False) -> None:
        # create layout using one of the methods
        methods = [self.create_level_grid, self.create_level_bsp]
        self.floor = random.choice(methods)()

        dim = 0.2
        for x in range(self.mapDim.x):
            for y in range(self.mapDim.y):
                random_grey = random.randint(96, 128)
                one_shade_of_grey = tcod.Color(random_grey, random_grey, random_grey)
                self.tiles[x, y]["lit"][1][:3] = one_shade_of_grey  # fg
                self.tiles[x, y]["lit"][2][:3] = one_shade_of_grey * 0.2  # bg
                self.tiles[x, y]["dim"][1][:3] = one_shade_of_grey * dim  # fg
                self.tiles[x, y]["dim"][2][:3] = one_shade_of_grey * dim * 0.2  # bg

        # select coordinates for stairs and place them
        if not first:
            self.tiles[self.stairs_up_pos] = tiles["stairs_up"]
            self.pos = self.stairs_up_pos
        self.tiles[self.stairs_down_pos] = tiles["stairs_down"]

    def create_level_grid(self) -> list[tuple]:
        self.Room.rooms_list = []
        max_cell_width, max_cell_height = 18, 8
        for j in range(2, self.mapDim.y, max_cell_height + 1):
            for i in range(1, self.mapDim.x, max_cell_width + 1):
                if (i + max_cell_width + 1 < self.mapDim.x) and (
                    j + max_cell_height + 1 < self.mapDim.y
                ):
                    x, y = random.randint(0, max_cell_width // 2), random.randint(
                        0, max_cell_height // 2
                    )
                    width, height = random.randint(
                        3, max_cell_width - x
                    ), random.randint(3, max_cell_height - y)
                    self.tiles[i + x : i + x + width, j + y : j + y + height] = tiles[
                        "floor"
                    ]
                    self.Room(i, j, x, y, width, height)

        room = random.choice(self.Room.rooms_list)
        room.is_connected = True
        self.stairs_up_pos = Point(
            mrogue.utils.roll(room.x + 1, room.x + room.width - 1),
            mrogue.utils.roll(room.y + 1, room.y + room.height - 1),
        )

        unconnected_neighbors = list(
            filter(lambda x: not x.is_connected, room.get_neighbors())
        )
        while any(unconnected_neighbors):
            new_room = random.choice(unconnected_neighbors)
            room.connect(new_room, self)
            room = new_room
            unconnected_neighbors = list(
                filter(lambda x: not x.is_connected, room.get_neighbors())
            )

        unconnected_rooms = list(
            filter(lambda x: not x.is_connected, self.Room.rooms_list)
        )
        while any(unconnected_rooms):
            room = random.choice(unconnected_rooms)
            if not any(cn := room.get_connected_neighbors()):
                continue
            room.connect(random.choice(cn), self)
            unconnected_rooms = list(
                filter(lambda x: not x.is_connected, self.Room.rooms_list)
            )
        self.stairs_down_pos = Point(
            mrogue.utils.roll(room.x + 1, room.x + room.width - 1),
            mrogue.utils.roll(room.y + 1, room.y + room.height - 1),
        )

        return np.argwhere(self.tiles["walkable"])

    def create_level_bsp(self) -> list[tuple]:
        # binary space partitioning
        bsp = tcod.bsp.BSP(0, 0, self.mapDim.x, self.mapDim.y)
        bsp.split_recursive(4, 11, 8, 1.0, 1.0)

        # vector will collect node centers from childless nodes (rooms)
        vector = []
        for node in bsp.inverted_level_order():
            if not node.children:
                vector.append(Point(node.x + node.w // 2, node.y + node.h // 2))

        # place rooms
        for node_center in vector:
            w, h = random.randint(3, 5), random.randint(2, 3)
            left, top = max(node_center.x - w, 1), max(node_center.y - h, 2)
            right = min(node_center.x + w + 1, self.mapDim.x - 1)
            bottom = min(node_center.y + h + 1, self.mapDim.y - 1)
            self.tiles[left:right, top:bottom] = tiles["floor"]
        floor = np.argwhere(self.tiles["walkable"])

        # place stairs before digging tunnels
        self.stairs_up_pos = Point(*random.choice(floor))
        self.stairs_down_pos = Point(*random.choice(floor))

        # dig tunnels from opposite nodes to partition line center
        for node in bsp.inverted_level_order():
            if not node.children:
                continue
            if node.horizontal:
                partition_center = Point(node.x + node.w // 2, node.position)
            else:
                partition_center = Point(node.position, node.y + node.h // 2)
            dist_pairs = []
            for node_center in vector:
                # save the distance from node center to partition center
                dist = (partition_center.x - node_center.x) ** 2 + (
                    partition_center.y - node_center.y
                ) ** 2
                dist_pairs.append((dist, node_center))
            # pick two nodes that are closest to the partition center
            dist_pairs.sort(key=lambda d: d[0], reverse=True)
            node1 = dist_pairs.pop()
            node2 = dist_pairs.pop()
            # ensure that the second node is on the other side of the partition
            if node.horizontal:
                while (node1[1].y < partition_center.y) == (
                    node2[1].y < partition_center.y
                ):
                    node2 = dist_pairs.pop()
            else:
                while (node1[1].x < partition_center.x) == (
                    node2[1].x < partition_center.x
                ):
                    node2 = dist_pairs.pop()
            # connect node centers to their respective partition's center
            self.tunnel(*node1[1], *partition_center)
            self.tunnel(*node2[1], *partition_center)
        return floor

    def tunnel(self, x1: int, y1: int, x2: int, y2: int) -> None:
        dx = 0 if x1 == x2 else int(abs(x2 - x1) / (x2 - x1))
        dy = 0 if y1 == y2 else int(abs(y2 - y1) / (y2 - y1))
        horizontal = random.random() > 0.5
        distance = 0
        broken = 100
        self.tiles[x1, y1] = tiles["floor"]
        while x1 != x2 or y1 != y2:
            if y1 == y2 or (horizontal and x1 != x2):
                x1 += dx
            else:
                y1 += dy
            distance += 1
            # turn only after leaving the initial room
            if self.tiles[x1, y1] == compare["wall"]:
                broken = distance
            self.tiles[x1, y1] = tiles["floor"]
            # don't turn right away
            if random.random() > 0.7 and distance - broken > 1:
                horizontal = not horizontal
        self.tiles[x2, y2] = tiles["floor"]


class Dungeon:
    _levels = []
    _depth = 0
    current_level: Level
    mapTop = 1
    mapDim = None

    def __init__(self):
        self.screen = mrogue.io.Screen.get()
        Dungeon.mapDim = Point(self.screen.width, self.screen.height - 1)
        Dungeon.current_level = Level(Dungeon.mapDim)
        Dungeon.current_level.create_level(first=True)
        Dungeon._levels.append(Dungeon.current_level)

    def new_level(self, num_objects: int) -> None:
        Dungeon.current_level.pos = mrogue.player.Player.get().pos
        Dungeon.current_level = Level(self.mapDim)
        Dungeon.current_level.create_level()
        mrogue.item.manager.ItemManager.create_loot(
            num_objects
        )  # , Dungeon._depth // 4)
        mrogue.monster.MonsterManager.create_monsters(num_objects, Dungeon._depth)
        Dungeon._levels.append(Dungeon.current_level)

    def level_from_string(self, level_string: str) -> Level:
        level = Level(self.mapDim)
        level_array = level_string.split()
        i = 0
        while i < self.mapDim.y:
            level.tiles[:, i] = [ch for ch in level_array[i]]
            i += 1
        return level

    def descend(self, pos: Point, num_objects: int) -> bool:
        if Dungeon.current_level.tiles[pos] == compare["stairs_down"]:
            Dungeon._depth += 1
            mrogue.monster.MonsterManager.stop_monsters()
            # if next level exists already
            if Dungeon._depth < len(Dungeon._levels):
                Dungeon.current_level = Dungeon._levels[Dungeon._depth]
            # otherwise create a new one, use preset if it would be the final one
            else:
                if Dungeon._depth == 8:
                    import zlib

                    with open(
                        path.join(mrogue.work_dir, "data", "level8.dat"), "rb"
                    ) as f:
                        level_string = str(zlib.decompress(f.read()), "utf-8")
                    Dungeon.current_level = self.level_from_string(level_string)
                    Dungeon.current_level.pos = Point(48, 35)
                    Dungeon.current_level.tiles[48, 35] = tiles["stairs_up"]
                    mrogue.monster.MonsterManager.create_monsters(
                        num_objects, Dungeon._depth
                    )
                    Dungeon._levels.append(Dungeon.current_level)
                else:
                    self.new_level(num_objects)
            mrogue.player.Player.get().change_level(Dungeon.current_level)
            return True
        mrogue.message.Messenger.add("There are no downward stairs here.")
        return False

    @classmethod
    def depth(cls) -> int:
        return cls._depth

    @classmethod
    def ascend(cls, pos: Point) -> bool:
        if cls.current_level.tiles[pos] == compare["stairs_up"]:
            cls._depth -= 1
            mrogue.monster.MonsterManager.stop_monsters()
            cls.current_level = cls._levels[cls._depth]
            mrogue.player.Player.get().change_level(cls.current_level)
            return True
        mrogue.message.Messenger.add("There are no upward stairs here.")
        return False

    @classmethod
    def find_spot(cls) -> Point:
        free_spots = list(
            filter(lambda spot: not cls.unit_at(Point(*spot)), cls.current_level.floor)
        )
        return Point(*random.choice(free_spots))

    @classmethod
    def movement(cls, unit: mrogue.unit.Unit, check: Point) -> bool:
        # if Unit skips turn or attempts to move but is immobilized, count it as spent action
        if unit.pos == check or unit.speed == 0.0:
            unit.move(False)
            return True
        # if target is farther that 1 space
        if not mrogue.utils.adjacent(unit.pos, check):
            return False
        if not cls.current_level.tiles[check]["walkable"]:
            if not unit.player:
                mrogue.message.Messenger.add(f"{unit.name} runs into the wall.")
            else:
                mrogue.message.Messenger.add("You can't move there.")
            return False
        target = cls.unit_at(check)
        # if a Unit occupies target space, attack it
        if target:
            if unit.player and unit != target:
                unit.attack(target)
                unit.moved = False
                return True
        else:
            unit.pos = check
            unit.move()
            return True

    def automove(
        self,
        pos: Point,
        direction: int,
        render_func: Callable,
        update_func: Callable,
    ) -> bool:
        def get_front(position: Point, delta: Point) -> np.array:
            if delta.y == 1:
                return Dungeon.current_level.tiles[
                    position.x + delta.x - 1, position.y - 1 : position.y + 2
                ]["walkable"]
            elif delta.x == 1:
                return Dungeon.current_level.tiles[
                    position.x - 1 : position.x + 2, position.y + delta.y - 1
                ]["walkable"]
            else:
                return Dungeon.current_level.tiles[
                    position.x + delta.x - 1, position.y + delta.y - 1
                ]["walkable"]

        def scan(
            current_pos: Point, delta_pos: Point, original_geometry: np.array = None
        ) -> bool:
            if original_geometry is not None:
                new_geometry = get_front(current_pos, delta_pos)
                if not np.array_equal(geometry, new_geometry):
                    return True
            for unit in Dungeon.current_level.units:
                if not unit.player and mrogue.utils.adjacent(current_pos, unit.pos, 3):
                    return True
            for obj in Dungeon.current_level.objects_on_map:
                if issubclass(
                    type(obj), mrogue.item.item.Item
                ) and mrogue.utils.adjacent(current_pos, obj.pos):
                    return True
            return False

        placement = np.nonzero(mrogue.io.directions == direction)
        if placement[1] == 1 and placement[2] == 1:
            # to avoid an infinite loop. Perhaps do it in main loop
            return False
        dx = placement[2][0] - 1
        dy = placement[1][0] - 1
        if scan(pos, Point(0, 0)):  # delta unused in this case
            # attempt normal movement if there are enemies or items in range
            return self.movement(
                mrogue.player.Player.get(), Point(pos.x + dx, pos.y + dy)
            )
        geometry = get_front(pos, Point(dx + 1, dy + 1))
        while True:
            # compare new geometry to starting conditions geometry
            if scan(pos, Point(dx + 1, dy + 1), geometry):
                # if the layout changes or there are Entities, stop automatic movement
                break
            # stop movement if Player dies
            if update_func():
                break
            # update the dungeon state every step
            render_func()
            mrogue.message.Messenger.clear()
            pos = Point(pos.x + dx, pos.y + dy)
            if not Dungeon.current_level.tiles[pos]["walkable"]:
                break
            self.movement(mrogue.player.Player.get(), pos)
        return True

    @classmethod
    def look_around(cls):
        player = mrogue.player.Player.get()
        player.fov = tcod.map.compute_fov(
            cls.current_level.tiles["transparent"], player.pos, player.sight_range
        )
        cls.current_level.explored |= player.fov

    @classmethod
    def unit_at(cls, where: Point) -> mrogue.unit.Unit or None:
        for unit in cls.current_level.units:
            if unit.pos == where:
                return unit
        return None

    def draw_map(self):
        nothing = np.asarray(
            (0, (0, 0, 0, 0), (0, 0, 0, 0)), dtype=tcod.console.rgba_graphic
        )
        item_heap = (0x25, (*tcod.gray, 255), (*tcod.blue * 0.3, 255))
        self.screen.clear()
        player = mrogue.player.Player.get()
        level = Dungeon.current_level
        display_items = list(
            filter(
                lambda item: isinstance(item, mrogue.item.item.Item),
                level.objects_on_map,
            )
        )
        display_monsters = list(
            filter(
                lambda m: isinstance(m, mrogue.monster.Monster), level.objects_on_map
            )
        )
        if "debug" in argv:
            self.screen.rgba[:, 0:39] = level.tiles["lit"]
        else:
            # TODO: investigate the bug below
            display_items = list(
                filter(lambda item: item.pos and player.fov[item.pos], display_items)
            )
            display_monsters = list(
                filter(lambda m: player.fov[m.pos], display_monsters)
            )
            self.screen.rgba[:, 0:39] = np.select(
                (player.fov, level.explored),
                (level.tiles["lit"], level.tiles["dim"]),
                nothing,
            )
        items_dict = defaultdict(list)
        for i in display_items:
            items_dict[i.pos].append(i)
        for pos, item_list in items_dict.items():
            self.screen.rgba[pos] = (
                item_list[0].tile if len(item_list) == 1 else item_heap
            )
        for monster in display_monsters:
            self.screen.rgba[monster.pos] = monster.tile
        self.screen.rgba[player.pos] = player.tile

    @classmethod
    def neighbors(cls, of: Point) -> list[Point]:
        x, y = of
        results = [
            Point(x - 1, y),
            Point(x, y + 1),
            Point(x + 1, y),
            Point(x, y - 1),
            Point(x - 1, y - 1),
            Point(x + 1, y - 1),
            Point(x - 1, y + 1),
            Point(x + 1, y + 1),
        ]
        results = list(
            filter(
                lambda p: 0 < p.x <= cls.mapDim.x and 0 < p.y <= cls.mapDim.y, results
            )
        )
        results = list(
            filter(lambda p: cls.current_level.tiles[p]["walkable"], results)
        )
        return results
