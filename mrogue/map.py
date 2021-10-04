# -*- coding: utf-8 -*-
"""Creation and display of the map for the whole game, consisting of 8 dungeon levels.

Globals:
    * tiles - dictionary of all the elements that the map is made of
    * compare - casting those tiles to numpy arrays for array values comparison that works
Classes:
    * Level - represents one floor of the dungeon
    * Dungeon - a collection of Levels
"""
import random
import numpy as np
from os import path
from sys import argv
from typing import Callable
import tcod.bsp
import tcod.map
import mrogue.io
import mrogue.item
import mrogue.message
import mrogue.monster
import mrogue.player
import mrogue.unit
import mrogue.utils
from mrogue import Point

tiles = {
    'wall': mrogue.io.Tile(
        walkable=False, transparent=False,
        lit=(0x2588, (192, 192, 192, 128), (32, 32, 32, 128)),
        dim=(0x2588, (64, 64, 64, 128), (0, 0, 0, 128))),
    'floor': mrogue.io.Tile(
        walkable=True, transparent=True,
        lit=(0xB7, (192, 192, 192, 128), (32, 32, 32, 128)),
        dim=(0xB7, (64, 64, 64, 64), (0, 0, 0, 128))),
    'stairs_down': mrogue.io.Tile(
        walkable=True, transparent=True,
        lit=(0x2265, (192, 192, 0, 128), (32, 32, 32, 128)),
        dim=(0x2265, (64, 64, 0, 64), (0, 0, 0, 128))),
    'stairs_up': mrogue.io.Tile(
        walkable=True, transparent=False,
        lit=(0x2264, (192, 192, 0, 128), (32, 32, 32, 128)),
        dim=(0x2264, (64, 64, 0, 64), (0, 0, 0, 128)))
}
compare = {
    'wall': np.asarray(tiles['wall'], dtype=mrogue.io.tile_dt),
    'floor': np.asarray(tiles['floor'], dtype=mrogue.io.tile_dt),
    'stairs_down': np.asarray(tiles['stairs_down'], dtype=mrogue.io.tile_dt),
    'stairs_up': np.asarray(tiles['stairs_up'], dtype=mrogue.io.tile_dt)
}


class Level:
    """Creates a stores a single floor of the dungeon that fits on the screen.

    Object attributes:
        * mapDim - width and height of the available space to dig in
        * objects_on_map - list of all the Entities that are tied to a particular Level
        * units - list of all the Units that walk on a particular Level
        * pos - position (coordinates) where Player should appear initially
        * tiles - numpy array keeping all structural information: walkability, transparency, tile type
        * explored - remembers the explored tiles per level
        * floor - a list of coordinates for empty tiles (rooms only)
    Methods:
        * create_level() - creates rooms and corridors, places stairs
        * tunnel() - connects two points by making a broken line
    """

    def __init__(self, dimensions: Point):
        """Creates an empty level using the BSP algorithm."""
        self.mapDim = dimensions
        self.objects_on_map = []
        self.units = []
        self.pos = None
        self.floor = None

        # first, everything is solid
        self.tiles = np.empty(self.mapDim, mrogue.io.tile_dt, 'F')
        self.tiles[:] = tiles['wall']
        self.explored = np.zeros(self.mapDim, bool, 'F')

    def create_level(self,  first: bool = False) -> None:
        """
        Fill the level with rooms and structures.

        :param first: True if this is the first level created at start
        """
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
            if random.random() <= .7:
                w, h = random.randint(3, 5), random.randint(2, 3)
                left, top = max(node_center.x - w, 1), max(node_center.y - h, 2)
                right = min(node_center.x + w + 1, self.mapDim.x - 1)
                bottom = min(node_center.y + h + 1, self.mapDim.y - 1)
                self.tiles[left:right, top:bottom] = tiles['floor']
        self.floor = np.argwhere(self.tiles['walkable'])

        # select coordinates for stairs before corridors so they would be placed only in rooms
        stairs_up = None
        if not first:
            stairs_up = Point(*random.choice(self.floor))
            self.pos = stairs_up
        stairs_down = Point(*random.choice(self.floor))

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
                dist = (partition_center.x - node_center.x) ** 2 + (partition_center.y - node_center.y) ** 2
                dist_pairs.append((dist, node_center))
            # pick two nodes that are closest to the partition center
            dist_pairs.sort(key=lambda d: d[0], reverse=True)
            node1 = dist_pairs.pop()
            node2 = dist_pairs.pop()
            # ensure that the second node is on the other side of the partition
            if node.horizontal:
                while (node1[1].y < partition_center.y) == (node2[1].y < partition_center.y):
                    node2 = dist_pairs.pop()
            else:
                while (node1[1].x < partition_center.x) == (node2[1].x < partition_center.x):
                    node2 = dist_pairs.pop()
            # connect node centers to their respective partition's center
            self.tunnel(*node1[1], *partition_center)
            self.tunnel(*node2[1], *partition_center)

        # TODO:  check if this can be done in a more elegant way
        for x in range(self.mapDim.x):
            for y in range(self.mapDim.y):
                random_grey = random.randint(64, 128)
                one_shade_of_grey = tcod.Color(random_grey, random_grey, random_grey)
                self.tiles[x, y]['lit'][1][:3] = one_shade_of_grey
                self.tiles[x, y]['dim'][1][:3] = one_shade_of_grey * 0.3

        # place stairs last so they won't be overwritten
        if stairs_up:
            self.tiles[stairs_up] = tiles['stairs_up']
        self.tiles[stairs_down] = tiles['stairs_down']

    def tunnel(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Connect two points, doing one turn after random amount of steps"""
        dx = 0 if x1 == x2 else int(abs(x2 - x1) / (x2 - x1))
        dy = 0 if y1 == y2 else int(abs(y2 - y1) / (y2 - y1))
        horizontal = random.random() > 0.5
        distance = 0
        broken = 100
        self.tiles[x1, y1] = tiles['floor']
        while x1 != x2 or y1 != y2:
            if y1 == y2 or (horizontal and x1 != x2):
                x1 += dx
            else:
                y1 += dy
            distance += 1
            # turn only after leaving the initial room
            if self.tiles[x1, y1] == compare['wall']:
                broken = distance
            self.tiles[x1, y1] = tiles['floor']
            # don't turn right away
            if random.random() > 0.7 and distance - broken > 1:
                horizontal = not horizontal
        self.tiles[x2, y2] = tiles['floor']


class Dungeon:
    """Keeps all the floors of the dungeon and implements field of view and other utility methods.

    Class attributes:
        * _levels - a list of all dungeon Levels
        * _depth - current depth in a Dungeon
        * current_level - for easy access by external classes
        * mapTop - which line to start printing the map
        * mapDim - width and height of the map itself
    Object attributes:
        * screen - main Screen object used by all the rendering methods
    Methods:
        * new_level() - creates a new Level and makes it current
        * level_from_string() - loads preset level map from a binary file
        * descend() - changes current level to previously visited one or creates a new one
        * depth() - sometimes just the current floor number is needed
        * ascend() - loads one of previously generated levels
        * find_spot() - finds an unoccupied space on the map
        * movement() - handles movements attempts by a Unit
        * automove() - crude implementation of automatic movement
        * scan() - checks for changes in the layout of traversed terrain
        * look_around() - reveals the map around the player using a field of view algorithm
        * unit_at() - returns a Unit at target coordinates
        * draw_map() - renders the map on screen
        * neighbors() - returns all the walkable cells around target coordinates
    """

    _levels = []
    _depth = 0
    current_level = None
    mapTop = 1
    mapDim = None

    def __init__(self):
        """Creates initial Level at the game start"""
        self.screen = mrogue.io.Screen.get()
        Dungeon.mapDim = Point(self.screen.width, self.screen.height - 1)
        Dungeon.current_level = Level(Dungeon.mapDim)
        Dungeon.current_level.create_level(first=True)
        Dungeon._levels.append(Dungeon.current_level)

    def new_level(self, num_objects: int) -> None:
        """Create new level, new monster list and new item list

        :param num_objects: how many monsters and items should pre-populate the level
        """
        Dungeon.current_level.pos = mrogue.player.Player.get().pos
        Dungeon.current_level = Level(self.mapDim)
        Dungeon.current_level.create_level()
        mrogue.item.ItemManager.create_loot(num_objects)  # , Dungeon._depth // 4)
        mrogue.monster.MonsterManager.create_monsters(num_objects, Dungeon._depth)
        Dungeon._levels.append(Dungeon.current_level)

    def level_from_string(self, level_string: str) -> Level:
        """Creates a level from binary file as a string

        :param level_string: read from a zipped binary file
        :return: Level instance
        """
        level = Level(self.mapDim)
        level_array = level_string.split()
        i = 0
        while i < self.mapDim.y:
            level.tiles[:, i] = [ch for ch in level_array[i]]
            i += 1
        return level

    def descend(self, pos: Point, num_objects: int) -> bool:
        """Switch current level for the one below it, creating a new one if necessary

        :param pos: check if there are stairs at this position
        :param num_objects: how many monsters and items to create
        :return: False if there are no stairs, True if level was switched
        """
        if Dungeon.current_level.tiles[pos] == compare['stairs_down']:
            Dungeon._depth += 1
            mrogue.monster.MonsterManager.stop_monsters()
            # if next level exists already
            if Dungeon._depth < len(Dungeon._levels):
                Dungeon.current_level = Dungeon._levels[Dungeon._depth]
            # otherwise create a new one, use preset if it would be the final one
            else:
                if Dungeon._depth == 8:
                    import zlib
                    with open(path.join(mrogue.work_dir, 'level8.dat'), 'rb') as f:
                        level_string = str(zlib.decompress(f.read()), 'utf-8')
                    Dungeon.current_level = self.level_from_string(level_string)
                    Dungeon.current_level.pos = Point(48, 35)
                    Dungeon.current_level.tiles[48, 35] = tiles['stairs_up']
                    mrogue.monster.MonsterManager.create_monsters(num_objects, Dungeon._depth)
                    Dungeon._levels.append(Dungeon.current_level)
                else:
                    self.new_level(num_objects)
            mrogue.player.Player.get().change_level(Dungeon.current_level)
            return True
        mrogue.message.Messenger.add('There are no downward stairs here.')
        return False

    @classmethod
    def depth(cls) -> int:
        return cls._depth

    @classmethod
    def ascend(cls, pos: Point) -> bool:
        """Switch current level for the one above it

        :param pos: check if there are stairs at this position
        :return: False if there are no stairs, True if level was switched
        """
        if cls.current_level.tiles[pos] == compare['stairs_up']:
            cls._depth -= 1
            mrogue.monster.MonsterManager.stop_monsters()
            cls.current_level = cls._levels[cls._depth]
            mrogue.player.Player.get().change_level(cls.current_level)
            return True
        mrogue.message.Messenger.add('There are no upward stairs here.')
        return False

    @classmethod
    def find_spot(cls) -> Point:
        """Return a random available cell

        :return: coordinates of an unoccupied, walkable cell
        """
        free_spots = list(filter(lambda spot: not cls.unit_at(Point(*spot)), cls.current_level.floor))
        return Point(*random.choice(free_spots))

    @classmethod
    def movement(cls, unit: mrogue.unit.Unit, check: Point) -> bool:
        """Check if movement to target cell is possible and perform an action

        :param unit: Unit that attempts movement
        :param check: target cell
        :return: False if something is preventing movement to target cell, True if movement or attack action was taken
        """
        # if Unit skips turn or attempts to move but is immobilized, count it as spent action
        if unit.pos == check or unit.speed == 0.0:
            unit.move(False)
            return True
        # if target is farther that 1 space
        if not mrogue.utils.adjacent(unit.pos, check):
            return False
        if not cls.current_level.tiles[check]['walkable']:
            if not unit.player:
                mrogue.message.Messenger.add(f'{unit.name} runs into the wall.')
            else:
                mrogue.message.Messenger.add('You can\'t move there.')
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

    def automove(self, pos: Point, direction: tcod.event.KeyDown, render_func: Callable, update_func: Callable) -> bool:
        """Attempt to move repeatedly unless state of the surroundings changed

        :param pos: starting point on the map
        :param direction: one of 8 directions to move along
        :param render_func: reference to screen rendering function from the game's main loop
        :param update_func: reference to passage of time function from the game's main loop
        :return: False if auto movement can't be initiated, True if performed successfully
        """
        def get_front(position: Point, delta: Point) -> np.array:
            """Get just the front strip of where player is facing for more reliable environment tracking"""
            if delta.y == 1:
                return Dungeon.current_level.tiles[position.x + delta.x - 1, position.y - 1:position.y + 2]['walkable']
            elif delta.x == 1:
                return Dungeon.current_level.tiles[position.x - 1:position.x + 2, position.y + delta.y - 1]['walkable']
            else:
                return Dungeon.current_level.tiles[position.x + delta.x - 1, position.y + delta.y - 1]['walkable']

        def scan(current_pos: Point, delta_pos: Point, original_geometry: np.array = None) -> bool:
            """Check if the map layout changed or if there is a Unit or Item """
            if original_geometry is not None:
                new_geometry = get_front(current_pos, delta_pos)
                if not np.array_equal(geometry, new_geometry):
                    return True
            for unit in Dungeon.current_level.units:
                if not unit.player and mrogue.utils.adjacent(current_pos, unit.pos, 3):
                    return True
            for obj in Dungeon.current_level.objects_on_map:
                if issubclass(type(obj), mrogue.item.Item) and mrogue.utils.adjacent(current_pos, obj.pos):
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
            return self.movement(mrogue.player.Player.get(), Point(pos.x + dx, pos.y + dy))
        geometry = get_front(pos, Point(dx+1, dy+1))
        while True:
            # compare new geometry to starting conditions geometry
            if scan(pos, Point(dx+1, dy+1), geometry):
                # if the layout changes or there are Entities, stop automatic movement
                break
            # stop movement if Player dies
            if update_func():
                break
            # update the dungeon state every step
            render_func()
            mrogue.message.Messenger.clear()
            pos = Point(pos.x + dx, pos.y + dy)
            if not Dungeon.current_level.tiles[pos]['walkable']:
                break
            self.movement(mrogue.player.Player.get(), pos)
        return True

    @classmethod
    def look_around(cls):
        """Mark dungeon tiles in range as visited using a field of view algorithm"""
        player = mrogue.player.Player.get()
        player.fov = tcod.map.compute_fov(cls.current_level.tiles['transparent'], player.pos, player.sight_range)
        cls.current_level.explored |= player.fov

    @classmethod
    def unit_at(cls, where: Point) -> mrogue.unit.Unit or None:
        """Get a single Unit occupying target space or None"""
        for unit in cls.current_level.units:
            if unit.pos == where:
                return unit
        return None

    def draw_map(self):
        """Directly transplant tiles to tcod.Console's memory, then render Entities"""
        nothing = np.asarray((0, (0, 0, 0, 0), (0, 0, 0, 0)), dtype=tcod.console.rgba_graphic)
        self.screen.clear()
        player = mrogue.player.Player.get()
        level = Dungeon.current_level
        if 'debug' in argv:
            self.screen.tiles_rgb[:, 0:39] = level.tiles['lit']
        else:
            self.screen.tiles_rgb[:, 0:39] = np.select(
                (player.fov, level.explored),
                (level.tiles['lit'], level.tiles['dim']),
                nothing)
        priority = []
        for thing in level.objects_on_map:
            if player.fov[thing.pos] or 'debug' in argv:
                if thing.layer < 2:
                    priority.append(thing)
                else:
                    self.screen.print(*thing.pos, thing.icon, thing.color)
        for thing in priority:
            self.screen.print(*thing.pos, thing.icon, thing.color)
        self.screen.print(*player.pos, player.icon, player.color)

    @classmethod
    def neighbors(cls, of: Point) -> list[Point]:
        """Get the list of tiles reachable immediately from a location

        :param of: center tile to get the neighbours of
        :return: a list of all reachable tiles around the center
        """
        x, y = of
        results = [Point(x-1, y), Point(x, y+1), Point(x+1, y), Point(x, y-1),
                   Point(x-1, y-1), Point(x+1, y-1), Point(x-1, y+1), Point(x+1, y+1)]
        results = list(filter(lambda p: 0 < p.x <= cls.mapDim.x and 0 < p.y <= cls.mapDim.y, results))
        results = list(filter(lambda p: cls.current_level.tiles[p]['walkable'], results))
        return results
