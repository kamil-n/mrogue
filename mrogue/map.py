# -*- coding: utf-8 -*-

import numpy
import random
from sys import argv
from os import path
import tcod.bsp
import tcod.map
from mrogue import adjacent, directions
from mrogue.item import Item


tileset = {
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
        self.tiles = numpy.full((self.mapDim[0], self.mapDim[1]),
                                tileset['wall'], order='F')
        temp = []
        for i in range(self.mapDim[0]):
            row = []
            for j in range(self.mapDim[1]):
                r = random.randint(64, 128)
                row.append(tcod.Color(r, r, r))
            temp.append(row)
        self.colors = numpy.empty((self.mapDim[0], self.mapDim[1]),
                                  object, order='F')
        self.colors[...] = temp
        self.explored = numpy.zeros((self.mapDim[0], self.mapDim[1]),
                                    bool, order='F')
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
        stairs_up = None
        stairs_down = None
        # place stairs up
        if not first:
            while True:
                x = random.randint(1, self.mapDim[0] - 1)
                y = random.randint(2, self.mapDim[1] - 1)
                if self.tiles[x][y] == tileset['floor']:
                    stairs_up = (x, y)
                    break
        # place stairs down
        while True:
            x = random.randint(1, self.mapDim[0] - 1)
            y = random.randint(2, self.mapDim[1] - 1)
            if self.walkable[x][y] and self.tiles[x][y] != tileset['stairs_up']:
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
                dist = (partition_center[0] - node_center[0]) ** 2 + \
                       (partition_center[1] - node_center[1]) ** 2
                dist_pairs.append((dist, node_center))
            dist_pairs.sort(key=lambda d: d[0], reverse=True)
            node1 = dist_pairs.pop()
            node2 = dist_pairs.pop()
            if node.horizontal:
                while (node1[1][1] < partition_center[1]) == \
                        (node2[1][1] < partition_center[1]):
                    node2 = dist_pairs.pop()
            else:
                while (node1[1][0] < partition_center[0]) == \
                        (node2[1][0] < partition_center[0]):
                    node2 = dist_pairs.pop()
            self._dig_tunnel(*node1[1], *partition_center)
            self._dig_tunnel(*node2[1], *partition_center)
        if not first:
            self.tiles[stairs_up[0]][stairs_up[1]] = tileset['stairs_up']
            self.colors[stairs_up[0]][stairs_up[1]] = tcod.yellow
            self.pos = stairs_up
        self.tiles[stairs_down[0]][stairs_down[1]] = tileset['stairs_down']
        self.colors[stairs_down[0]][stairs_down[1]] = tcod.yellow

    def _dig_tunnel(self, x1, y1, x2, y2):
        absx = abs(x2 - x1)
        absy = abs(y2 - y1)
        dx = 0 if x1 == x2 else int(absx / (x2 - x1))
        dy = 0 if y1 == y2 else int(absy / (y2 - y1))
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
            if self.tiles[x1][y1] == tileset['wall']:
                broken = distance
            self._dig(x1, y1)
            if random.random() > 0.7 and distance - broken > 1:
                horizontal = not horizontal
        self._dig(x2, y2)

    def _dig(self, x, y, tile=tileset['floor'], color=None,
             transparent=True, walkable=True):
        self.tiles[x][y] = tile
        if not color:
            r = random.randint(64, 128)
            color = tcod.Color(r, r, r)
        self.colors[x][y] = color
        self.transparent[x][y] = transparent
        self.walkable[x][y] = walkable


class Dungeon:
    levels = []
    depth = 0
    game = None
    mapTop = 1

    def __init__(self, game):
        self.mapDim = (game.screen.width, game.screen.height - 1)
        self.level = Level(self.mapDim, True)
        self.levels.append(self.level)
        self.game = game

    def new_level(self):
        self.level.pos = self.game.player.pos
        self.level = Level(self.mapDim)
        self.game.items.create_loot(self.game.num_objects, self.depth // 4)
        self.game.monsters.create_monsters(self.game.num_objects + self.depth)
        self.levels.append(self.level)

    def level_from_string(self, level_string):
        tcod_map = tcod.map.Map(self.mapDim[0], self.mapDim[1], 'F')
        tcod_map.objects_on_map = []
        tcod_map.units = []
        tcod_map.tiles = numpy.full((self.mapDim[0], self.mapDim[1]), tileset['wall'], order='F')
        temp = []
        for i in range(self.mapDim[0]):
            row = []
            for j in range(self.mapDim[1]):
                r = random.randint(64, 128)
                row.append(tcod.Color(r, r, r))
            temp.append(row)
        tcod_map.colors = numpy.empty((self.mapDim[0], self.mapDim[1]), object, order='F')
        tcod_map.colors[...] = temp
        tcod_map.explored = numpy.zeros((self.mapDim[0], self.mapDim[1]), bool, order='F')
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

    def descend(self, pos):
        if self.level.tiles[pos[0]][pos[1]] == tileset['stairs_down']:
            self.depth += 1
            self.game.monsters.stop_monsters()
            if self.depth < len(self.levels):
                self.level = self.levels[self.depth]
            else:
                if self.depth == 8:
                    import zlib
                    with open(path.join(self.game.dir, 'level8.dat'), 'rb') as f:
                        level_string = str(zlib.decompress(f.read()), 'utf-8')
                    self.level = self.level_from_string(level_string)
                    self.level.pos = (48, 35)
                    self.level.walkable[48, 35] = self.level.transparent[48, 35] = True
                    self.game.monsters.create_monsters(self.game.num_objects + self.depth)
                    self.levels.append(self.level)
                else:
                    self.new_level()
            self.game.player.change_level(self.level)
            return True
        self.game.messenger.add('There are no downward stairs here.')
        return False

    def ascend(self, pos):
        if self.level.tiles[pos[0]][pos[1]] == tileset['stairs_up']:
            self.depth -= 1
            self.game.monsters.stop_monsters()
            self.level = self.levels[self.depth]
            self.game.player.change_level(self.level)
            return True
        self.game.messenger.add('There are no upward stairs here.')
        return False

    def find_spot(self):
        while True:
            x = random.randint(1, self.mapDim[0] - 1)
            y = random.randint(self.mapTop + 1,
                               self.mapDim[1] - 1)
            if self.level.walkable[x][y] and not self.unit_at((x, y)):
                return x, y

    def movement(self, unit, check):
        if unit.pos == check or unit.speed == 0.0:
            unit.move(False)
            return True
        if not adjacent(unit.pos, check):
            return False
        if not self.level.walkable[check[0]][check[1]]:
            if not unit.player:
                self.game.messenger.add(
                    '{} runs into the wall.'.format(unit.name))
                return
            else:
                self.game.messenger.add('You can\'t move there.')
                return False
        target = self.unit_at(check)
        if target:
            if unit.player and unit != target:
                unit.attack(target)
                unit.moved = False
                return True
        else:
            unit.pos = check
            unit.move()
            return True

    def automove(self, pos, direction):
        if self.scan(*pos, None):
            return False
        placement = numpy.nonzero(directions == direction)
        dx = placement[2][0] - 1
        dy = placement[1][0] - 1
        x = pos[0]
        y = pos[1]
        geometry = self.level.walkable[x-1:x+2, y-1:y+2].sum()
        while True:
            if self.scan(x, y, geometry):
                break
            if self.game.update_dungeon():
                break
            self.game.draw_dungeon()
            self.game.messenger.clear()
            x += dx
            y += dy
            if not self.level.walkable[x][y]:
                break
            self.movement(self.game.player, (x, y))
        return True

    def scan(self, x, y, original_geometry):
        if original_geometry:
            geometry = self.level.walkable[x-1:x+2, y-1:y+2].sum()
            if geometry != original_geometry:
                return True
        for unit in self.level.units:
            if not unit.player and self.level.fov[unit.pos[0]][unit.pos[1]]:
                return True
        for obj in self.level.objects_on_map:
            if issubclass(type(obj), Item) and adjacent((x, y), obj.pos):
                return True

    def look_around(self):
        radius = self.game.player.sight_range
        pos = self.game.player.pos
        self.level.compute_fov(*pos, radius, algorithm=tcod.FOV_BASIC)

    def unit_at(self, where: tuple):
        for unit in self.level.units:
            if unit.pos == where:
                return unit
        return None

    def draw_map(self):
        self.game.screen.clear()
        if 'debug' in argv:
            for x in range(0, self.mapDim[0]):
                for y in range(1, self.mapDim[1]):
                    self.game.screen.print(x, y, self.level.tiles[x][y],
                                           self.level.colors[x][y] * 1.00)
        else:
            for x in range(0, self.mapDim[0]):
                for y in range(1, self.mapDim[1]):
                    if self.level.fov[x][y]:
                        self.level.explored[x][y] = True
                        self.game.screen.print(x, y, self.level.tiles[x][y],
                                               self.level.colors[x][y] * 1.00)
                    elif self.level.explored[x][y]:
                        self.game.screen.print(x, y, self.level.tiles[x][y],
                                               self.level.colors[x][y] * 0.35)
        priority = []
        for thing in self.level.objects_on_map:
            if self.level.fov[thing.pos[0]][thing.pos[1]] or 'debug' in argv:
                if thing.layer < 2:
                    priority.append(thing)
                else:
                    self.game.screen.print(*thing.pos, thing.icon, thing.color)
        for thing in priority:
            self.game.screen.print(*thing.pos, thing.icon, thing.color)
        self.game.screen.print(*self.game.player.pos, self.game.player.icon,
                               self.game.player.color)

    def neighbors(self, of):
        x, y = of
        results = [(x-1, y), (x, y+1), (x+1, y), (x, y-1),
                   (x-1, y-1), (x+1, y-1), (x-1, y+1), (x+1, y+1)]
        results = list(filter(lambda p: 0 < p[0] <= self.mapDim[0] and
                              0 < p[1] <= self.mapDim[1], results))
        results = list(filter(lambda p: self.level.walkable[p[0]][p[1]],
                              results))
        return results
