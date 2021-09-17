# -*- coding: utf-8 -*-

import random
import numpy as np
from sys import argv
from os import path
import tcod.bsp
import tcod.map
import mrogue.io
import mrogue.item
import mrogue.message
import mrogue.monster
import mrogue.player
import mrogue.utils

tiles = {
           'wall': chr(0x2588),
           'floor': chr(0xB7),
           'stairs_down': chr(0x2265),
           'stairs_up': chr(0x2264)}


class Level(tcod.map.Map):
    def __init__(self, dimensions, first=False):
        self.mapDim = dimensions
        self.objects_on_map = []
        self.units = []
        super().__init__(self.mapDim[0], self.mapDim[1], 'F')
        self.tiles = np.full((self.mapDim[0], self.mapDim[1]), tiles['wall'], order='F')
        temp = []
        for i in range(self.mapDim[0]):
            row = []
            for j in range(self.mapDim[1]):
                r = random.randint(64, 128)
                row.append(tcod.Color(r, r, r))
            temp.append(row)
        self.colors = np.empty((self.mapDim[0], self.mapDim[1]), object, order='F')
        self.colors[...] = temp
        self.explored = np.zeros((self.mapDim[0], self.mapDim[1]), bool, order='F')
        bsp = tcod.bsp.BSP(0, 0, self.mapDim[0], self.mapDim[1])
        bsp.split_recursive(4, 11, 8, 1.0, 1.0)
        vector = []
        # collect node centers from childless nodes
        for node in bsp.inverted_level_order():
            if not node.children:
                vector.append((node.x + node.w // 2, node.y + node.h // 2))
        # place rooms
        for node in bsp.inverted_level_order():
            if not node.children:  # and random.random() <= 1.0:
                nx = node.x + node.w // 2
                ny = node.y + node.h // 2
                w = random.randint(3, 5)
                h = random.randint(2, 3)
                for x in range(nx - w, nx + w + 1):
                    for y in range(ny - h, ny + h + 1):
                        if 1 < x < self.mapDim[0] - 1 and 1 < y < self.mapDim[1] - 1:
                            self._dig(x, y)
        # place stairs up
        if not first:
            while True:
                x = random.randint(1, self.mapDim[0] - 1)
                y = random.randint(2, self.mapDim[1] - 1)
                if self.tiles[x][y] == tiles['floor']:
                    stairs_up = (x, y)
                    break
        # place stairs down
        while True:
            x = random.randint(1, self.mapDim[0] - 1)
            y = random.randint(2, self.mapDim[1] - 1)
            if self.walkable[x][y] and self.tiles[x][y] != tiles['stairs_up']:
                stairs_down = (x, y)
                break
        # dig tunnels from opposite nodes to partition line center
        for node in bsp.inverted_level_order():
            if not node.children:
                continue
            if node.horizontal:
                partition_center = (node.x + node.w // 2, node.position)
            else:
                partition_center = (node.position, node.y + node.h // 2)
            dist_pairs = []
            for node_center in vector:
                dist = (partition_center[0] - node_center[0]) ** 2 + (partition_center[1] - node_center[1]) ** 2
                dist_pairs.append((dist, node_center))
            dist_pairs.sort(key=lambda d: d[0], reverse=True)
            node1 = dist_pairs.pop()
            node2 = dist_pairs.pop()
            if node.horizontal:
                while (node1[1][1] < partition_center[1]) == (node2[1][1] < partition_center[1]):
                    node2 = dist_pairs.pop()
            else:
                while (node1[1][0] < partition_center[0]) == (node2[1][0] < partition_center[0]):
                    node2 = dist_pairs.pop()
            self._dig_tunnel(*node1[1], *partition_center)
            self._dig_tunnel(*node2[1], *partition_center)
        if not first:
            self.tiles[stairs_up[0]][stairs_up[1]] = tiles['stairs_up']
            self.colors[stairs_up[0]][stairs_up[1]] = tcod.yellow
            self.pos = stairs_up
        self.tiles[stairs_down[0]][stairs_down[1]] = tiles['stairs_down']
        self.colors[stairs_down[0]][stairs_down[1]] = tcod.yellow

    def _dig_tunnel(self, x1, y1, x2, y2):
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
            if self.tiles[x1][y1] == tiles['wall']:
                broken = distance
            self._dig(x1, y1)
            if random.random() > 0.7 and distance - broken > 1:
                horizontal = not horizontal
        self._dig(x2, y2)

    def _dig(self, x, y, tile=tiles['floor'], color=None, transparent=True, walkable=True):
        self.tiles[x][y] = tile
        if not color:
            r = random.randint(64, 128)
            color = tcod.Color(r, r, r)
        self.colors[x][y] = color
        self.transparent[x][y] = transparent
        self.walkable[x][y] = walkable


class Dungeon:
    _levels = []
    _depth = 0
    current_level = None
    mapTop = 1
    mapDim = None

    def __init__(self):
        self.screen = mrogue.io.Screen.get()
        Dungeon.mapDim = (self.screen.width, self.screen.height - 1)
        Dungeon.current_level = Level(self.mapDim, True)
        Dungeon._levels.append(Dungeon.current_level)

    def new_level(self, num_objects):
        Dungeon.current_level.pos = mrogue.player.Player.get().pos
        Dungeon.current_level = Level(self.mapDim)
        mrogue.item.ItemManager.create_loot(num_objects)  # , Dungeon._depth // 4)
        mrogue.monster.MonsterManager.create_monsters(num_objects, Dungeon._depth)
        Dungeon._levels.append(Dungeon.current_level)

    def level_from_string(self, level_string):
        tcod_map = tcod.map.Map(self.mapDim[0], self.mapDim[1], 'F')
        tcod_map.objects_on_map = []
        tcod_map.units = []
        tcod_map.tiles = np.full((self.mapDim[0], self.mapDim[1]), tiles['wall'], order='F')
        temp = []
        for i in range(self.mapDim[0]):
            row = []
            for j in range(self.mapDim[1]):
                r = random.randint(64, 128)
                row.append(tcod.Color(r, r, r))
            temp.append(row)
        tcod_map.colors = np.empty((self.mapDim[0], self.mapDim[1]), object, order='F')
        tcod_map.colors[...] = temp
        tcod_map.explored = np.zeros((self.mapDim[0], self.mapDim[1]), bool, order='F')
        level_array = level_string.split()
        i = 0
        while i < self.mapDim[1]:
            line = [ch for ch in level_array[i]]
            tcod_map.tiles[:, i] = line
            i += 1
        floor_mask = (tcod_map.tiles == '·')
        tcod_map.walkable[:] = floor_mask
        tcod_map.transparent[:] = floor_mask
        return tcod_map

    def descend(self, pos, num_objects):
        if Dungeon.current_level.tiles[pos[0]][pos[1]] == tiles['stairs_down']:
            Dungeon._depth += 1
            mrogue.monster.MonsterManager.stop_monsters()
            if Dungeon._depth < len(Dungeon._levels):
                Dungeon.current_level = Dungeon._levels[Dungeon._depth]
            else:
                if Dungeon._depth == 8:
                    import zlib
                    with open(path.join(mrogue.work_dir, 'level8.dat'), 'rb') as f:
                        level_string = str(zlib.decompress(f.read()), 'utf-8')
                    Dungeon.current_level = self.level_from_string(level_string)
                    Dungeon.current_level.pos = (48, 35)
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
    def depth(cls):
        return cls._depth

    @classmethod
    def ascend(cls, pos):
        if cls.current_level.tiles[pos[0]][pos[1]] == tiles['stairs_up']:
            cls._depth -= 1
            mrogue.monster.MonsterManager.stop_monsters()
            cls.current_level = cls._levels[cls._depth]
            mrogue.player.Player.get().change_level(cls.current_level)
            return True
        mrogue.message.Messenger.add('There are no upward stairs here.')
        return False

    @classmethod
    def find_spot(cls):
        while True:
            x = random.randint(1, cls.mapDim[0] - 1)
            y = random.randint(cls.mapTop + 1,
                               cls.mapDim[1] - 1)
            if cls.current_level.walkable[x][y] and not cls.unit_at((x, y)):
                return x, y

    @classmethod
    def movement(cls, unit, check):
        if unit.pos == check or unit.speed == 0.0:
            unit.move(False)
            return True
        if not mrogue.utils.adjacent(unit.pos, check):
            return False
        if not cls.current_level.walkable[check[0]][check[1]]:
            if not unit.player:
                mrogue.message.Messenger.add(f'{unit.name} runs into the wall.')
                return
            else:
                mrogue.message.Messenger.add('You can\'t move there.')
                return False
        target = cls.unit_at(check)
        if target:
            if unit.player and unit != target:
                unit.attack(target)
                unit.moved = False
                return True
        else:
            unit.pos = check
            unit.move()
            return True

    ''' temporarily disabled due to calling unreachable methods
    def automove(self, pos, direction):
        if self.scan(*pos, None):
            return False
        placement = np.nonzero(mrogue.io.directions == direction)
        dx = placement[2][0] - 1
        dy = placement[1][0] - 1
        x = pos[0]
        y = pos[1]
        geometry = Dungeon.current_level.walkable[x-1:x+2, y-1:y+2].sum()
        while True:
            if self.scan(x, y, geometry):
                break
            if GAME.update_dungeon():
                break
            GAME.draw_dungeon()
            Messenger.clear()
            x += dx
            y += dy
            if not Dungeon.current_level.walkable[x][y]:
                break
            self.movement(Player.get(), (x, y))
        return True'''

    @classmethod
    def scan(cls, x, y, original_geometry):
        if original_geometry:
            geometry = cls.current_level.walkable[x-1:x+2, y-1:y+2].sum()
            if geometry != original_geometry:
                return True
        for unit in cls.current_level.units:
            if not unit.player and cls.current_level.fov[unit.pos[0]][unit.pos[1]]:
                return True
        for obj in cls.current_level.objects_on_map:
            if issubclass(type(obj), mrogue.item.Item) and mrogue.utils.adjacent((x, y), obj.pos):
                return True

    @classmethod
    def look_around(cls):
        radius = mrogue.player.Player.get().sight_range
        pos = mrogue.player.Player.get().pos
        cls.current_level.compute_fov(*pos, radius, algorithm=tcod.FOV_BASIC)

    @classmethod
    def unit_at(cls, where: tuple):
        for unit in cls.current_level.units:
            if unit.pos == where:
                return unit
        return None

    def draw_map(self):
        self.screen.clear()
        level = Dungeon.current_level
        if 'debug' in argv:
            for x in range(0, self.mapDim[0]):
                for y in range(1, self.mapDim[1]):
                    self.screen.print(x, y, level.tiles[x][y],  level.colors[x][y] * 1.00)
        else:
            for x in range(0, self.mapDim[0]):
                for y in range(1, self.mapDim[1]):
                    if level.fov[x][y]:
                        level.explored[x][y] = True
                        self.screen.print(x, y, level.tiles[x][y], level.colors[x][y] * 1.00)
                    elif level.explored[x][y]:
                        self.screen.print(x, y, level.tiles[x][y], level.colors[x][y] * 0.35)
        priority = []
        for thing in level.objects_on_map:
            if level.fov[thing.pos[0]][thing.pos[1]] or 'debug' in argv:
                if thing.layer < 2:
                    priority.append(thing)
                else:
                    self.screen.print(*thing.pos, thing.icon, thing.color)
        for thing in priority:
            self.screen.print(*thing.pos, thing.icon, thing.color)
        player = mrogue.player.Player.get()
        self.screen.print(*player.pos, player.icon, player.color)

    @classmethod
    def neighbors(cls, of):
        x, y = of
        results = [(x-1, y), (x, y+1), (x+1, y), (x, y-1), (x-1, y-1), (x+1, y-1), (x-1, y+1), (x+1, y+1)]
        results = list(filter(lambda p: 0 < p[0] <= cls.mapDim[0] and 0 < p[1] <= cls.mapDim[1], results))
        results = list(filter(lambda p: cls.current_level.walkable[p[0]][p[1]], results))
        return results
