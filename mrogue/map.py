# -*- coding: utf-8 -*-
"""Creation and display of the map for the whole game, consisting of 8 dungeon levels.

Globals:
    * tiles - dictionary of all the elements that the map is made of
Functions:
    * random_gray() - selects a random shade of gray
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
           'wall': chr(0x2588),
           'floor': chr(0xB7),
           'stairs_down': chr(0x2265),
           'stairs_up': chr(0x2264)}


def random_gray(lo: int, hi: int) -> tcod.Color:
    """Create a random shade of gray for the dungeon tile"""
    val = random.randint(lo, hi)
    return tcod.Color(val, val, val)


class Level(tcod.map.Map):
    """Creates a stores a single floor of the dungeon that fits on the screen.

    Extends:
        * tcod.map.Map
    Object attributes:
        * mapDim - width and height of the available space to dig in
        * objects_on_map - list of all the Entities that are tied to a particular Level
        * units - list of all the Units that walk on a particular Level
        * colors - mapping of tile colors
        * explored - remembers the explored tiles
    Methods:
        * _dig_tunnel() - connects two points by making a broken line
        * _dig() - changes solid tiles (walls) to empty space
    """

    def __init__(self, dimensions: Point, first: bool = False):
        """Creates a level using the BSP algorithm."""
        self.mapDim = dimensions
        self.objects_on_map = []
        self.units = []
        super().__init__(self.mapDim.x, self.mapDim.y, 'F')

        # first, everything is solid
        self.tiles = np.full((self.mapDim.x, self.mapDim.y), tiles['wall'], order='F')

        # some tricks are needed to pick a random shade of gray for each tile
        temp = [[random_gray(64, 128) for _ in range(self.mapDim.y)] for _ in range(self.mapDim.x)]
        self.colors = np.empty((self.mapDim.x, self.mapDim.y), object, order='F')
        self.colors[...] = temp

        self.explored = np.zeros((self.mapDim.x, self.mapDim.y), bool, order='F')

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
        floor_mask = (self.tiles == '·')
        self.walkable[:] = floor_mask
        self.transparent[:] = floor_mask
        self.floor = np.argwhere(self.tiles == tiles['floor'])

        # select coordinates for stairs before corridors so they would be placed only in rooms
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
            self._dig_tunnel(*node1[1], *partition_center)
            self._dig_tunnel(*node2[1], *partition_center)

        # place stairs last so they won't be overwritten
        if not first:
            self._dig(stairs_up.x, stairs_up.y, tiles['stairs_up'], tcod.yellow, False)
        self._dig(stairs_down.x, stairs_down.y, tiles['stairs_down'], tcod.yellow)
        # experimenting with noise map:
        # noise = tcod.noise.Noise(dimensions=2, algorithm=tcod.noise.Algorithm.WAVELET, seed=42)
        # samples = noise[tcod.noise.grid(shape=(self.mapDim.y, self.mapDim.x), scale=0.1, origin=(0, 0))]
        # samples = (samples + 1.0) * 0.5
        # threshold = 0.4
        # self.tiles = np.select([samples < threshold, samples >= threshold], [tiles['wall'], tiles['floor']])
        # self.transparent[:] = np.select([samples < threshold, samples >= threshold], [False, True])
        # self.walkable[:] = np.select([samples < threshold, samples >= threshold], [False, True])

    def _dig_tunnel(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Connect two points, doing one turn after random amount of steps"""
        dx = 0 if x1 == x2 else int(abs(x2 - x1) / (x2 - x1))
        dy = 0 if y1 == y2 else int(abs(y2 - y1) / (y2 - y1))
        horizontal = random.random() > 0.5
        distance = 0
        broken = 100
        self._dig(x1, y1)
        while x1 != x2 or y1 != y2:
            if y1 == y2 or (horizontal and x1 != x2):
                x1 += dx
            else:
                y1 += dy
            distance += 1
            # turn only after leaving the initial room
            if self.tiles[x1, y1] == tiles['wall']:
                broken = distance
            self._dig(x1, y1)
            # don't turn right away
            if random.random() > 0.7 and distance - broken > 1:
                horizontal = not horizontal
        self._dig(x2, y2)

    def _dig(self, x: int, y: int,
             tile: str = tiles['floor'],
             color: tcod.Color = None,
             transparent: bool = True,
             walkable: bool = True) -> None:
        """Change solid tile (wall) into space

        :param x: x coordinate of the tile
        :param y: y coordinate of the tile
        :param tile: what to set instead of the wall
        :param color: color of the new space
        :param transparent: if it doesn't break line of sight
        :param walkable: if it doesn't break movement
        """
        self.tiles[x, y] = tile
        if not color:
            # random shade of gray
            r = random.randint(64, 128)
            color = tcod.Color(r, r, r)
        self.colors[x, y] = color
        self.transparent[x, y] = transparent
        self.walkable[x, y] = walkable


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
        Dungeon.current_level = Level(Dungeon.mapDim, True)
        Dungeon._levels.append(Dungeon.current_level)

    def new_level(self, num_objects: int) -> None:
        """Create new level, new monster list and new item list

        :param num_objects: how many monsters and items should pre-populate the level
        """
        Dungeon.current_level.pos = mrogue.player.Player.get().pos
        Dungeon.current_level = Level(self.mapDim)
        mrogue.item.ItemManager.create_loot(num_objects)  # , Dungeon._depth // 4)
        mrogue.monster.MonsterManager.create_monsters(num_objects, Dungeon._depth)
        Dungeon._levels.append(Dungeon.current_level)

    def level_from_string(self, level_string: str) -> tcod.map.Map:
        """Creates a level from binary file as a string

        :param level_string: read from a zipped binary file
        :return: level as base tcod.map.Map, not Level
        """
        tcod_map = tcod.map.Map(self.mapDim.x, self.mapDim.y, 'F')
        tcod_map.objects_on_map = []
        tcod_map.units = []
        tcod_map.tiles = np.full((self.mapDim.x, self.mapDim.y), tiles['wall'], order='F')
        temp = [[random_gray(64, 128) for _ in range(self.mapDim.y)] for _ in range(self.mapDim.x)]
        tcod_map.colors = np.empty((self.mapDim.x, self.mapDim.y), object, order='F')
        tcod_map.colors[...] = temp
        tcod_map.explored = np.zeros((self.mapDim.x, self.mapDim.y), bool, order='F')
        level_array = level_string.split()
        i = 0
        while i < self.mapDim.y:
            tcod_map.tiles[:, i] = [ch for ch in level_array[i]]
            i += 1
        floor_mask = (tcod_map.tiles == '·')
        tcod_map.walkable[:] = floor_mask
        tcod_map.transparent[:] = floor_mask
        return tcod_map

    def descend(self, pos: Point, num_objects: int) -> bool:
        """Switch current level for the one below it, creating a new one if necessary

        :param pos: check if there are stairs at this position
        :param num_objects: how many monsters and items to create
        :return: False if there are no stairs, True if level was switched
        """
        if Dungeon.current_level.tiles[pos] == tiles['stairs_down']:
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
                    Dungeon.current_level.walkable[48, 35] = Dungeon.current_level.transparent[48, 35] = True
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
        if cls.current_level.tiles[pos] == tiles['stairs_up']:
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
        if not cls.current_level.walkable[check]:
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
                return Dungeon.current_level.walkable[position.x + delta.x - 1, position.y - 1:position.y + 2]
            elif delta.x == 1:
                return Dungeon.current_level.walkable[position.x - 1:position.x + 2, position.y + delta.y - 1]
            else:
                return Dungeon.current_level.walkable[position.x + delta.x - 1, position.y + delta.y - 1]

        def scan(current_pos: Point, delta_pos: Point, original_geometry: np.array = None) -> bool:
            """Check if the map layout changed or if there is a Unit or Item """
            if original_geometry is not None:
                new_geometry = get_front(current_pos, delta_pos)
                if not np.array_equal(geometry, new_geometry):
                    return True
            for unit in Dungeon.current_level.units:
                if not unit.player and mrogue.utils.adjacent(current_pos, unit.pos, 2):
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
            if not Dungeon.current_level.walkable[pos]:
                break
            self.movement(mrogue.player.Player.get(), pos)
        return True

    @classmethod
    def look_around(cls):
        """Mark dungeon tiles in range as visited using a field of view algorithm"""
        radius = mrogue.player.Player.get().sight_range
        pos = mrogue.player.Player.get().pos
        cls.current_level.compute_fov(*pos, radius, algorithm=tcod.FOV_BASIC)

    @classmethod
    def unit_at(cls, where: Point) -> mrogue.unit.Unit or None:
        """Get a single Unit occupying target space or None"""
        for unit in cls.current_level.units:
            if unit.pos == where:
                return unit
        return None

    def draw_map(self):
        """Loop through all cells on the map and render them either visited (darker) or visible, then render Entities"""
        self.screen.clear()
        level = Dungeon.current_level
        # TODO: get rid of nested loops
        if 'debug' in argv:
            for x in range(0, self.mapDim.x):
                for y in range(1, self.mapDim.y):
                    self.screen.print(x, y, level.tiles[x][y],  level.colors[x][y] * 1.00)
        else:
            for x in range(0, self.mapDim.x):
                for y in range(1, self.mapDim.y):
                    if level.fov[x][y]:
                        level.explored[x][y] = True
                        self.screen.print(x, y, level.tiles[x][y], level.colors[x][y] * 1.00)
                    elif level.explored[x][y]:
                        self.screen.print(x, y, level.tiles[x][y], level.colors[x][y] * 0.35)
        priority = []
        for thing in level.objects_on_map:
            if level.fov[thing.pos] or 'debug' in argv:
                if thing.layer < 2:
                    priority.append(thing)
                else:
                    self.screen.print(*thing.pos, thing.icon, thing.color)
        for thing in priority:
            self.screen.print(*thing.pos, thing.icon, thing.color)
        player = mrogue.player.Player.get()
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
        results = list(filter(lambda p: cls.current_level.walkable[p], results))
        # double filter is twice faster than the following:
        # results = [Point(*p) for p in np.argwhere(cls.current_level.walkable[x-1:x+2, y-1:y+2]) + [x, y]]
        return results
