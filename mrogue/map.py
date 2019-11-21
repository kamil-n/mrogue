# -*- coding: utf-8 -*-

import logging
import numpy
from queue import PriorityQueue
import random
from sys import argv
import tcod.bsp
import tcod.map
from mrogue import adjacent, wait

tileset = {'wall': '#', 'floor': '.'}


class RogueMap(tcod.map.Map):
    game = None
    mapTop = 1

    def __init__(self, game):
        self.mapDim = (game.screen.width, game.screen.height - 1)
        super().__init__(self.mapDim[0], self.mapDim[1], 'F')
        self.tiles = numpy.full((self.mapDim[0], self.mapDim[1]), tileset['wall'], order='F')
        temp = []
        for i in range(self.mapDim[0]):
            row = []
            for j in range(self.mapDim[1]):
                r = random.randint(64, 128)
                row.append(tcod.Color(r, r, r))
            temp.append(row)
        self.colors = numpy.empty((self.mapDim[0], self.mapDim[1]), object, order='F')
        self.colors[...] = temp
        self.explored = numpy.zeros((self.mapDim[0], self.mapDim[1]), bool, order='F')
        self.game = game
        self.objects_on_map = []
        self.units = []
        self.log = logging.getLogger(__name__)
        bsp = tcod.bsp.BSP(0, 0, self.mapDim[0], self.mapDim[1])
        bsp.split_recursive(4, 11, 8, 1.0, 1.0)
        vector = []
        # collect node centers from childless nodes
        for node in bsp.inverted_level_order():
            if not node.children:
                vector.append((node.x + node.w // 2, node.y + node.h // 2))
            for x in range(node.x, node.x + node.w):
                self.colors[x][node.y] = tcod.red
            for y in range(node.y, node.y + node.h):
                self.colors[node.x][y] = tcod.red
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
                            self.dig(x, y)
                self.dig(nx, ny, '$', tcod.yellow)
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
                print('horizontal; {} <=> {} <=> {}'.format(node1[1][1], partition_center[1], node2[1][1]))
                while node1[1][1] < partition_center[1] and node2[1][1] < partition_center[1]:
                    node2 = dist_pairs.pop()
                    print('   drawing another: {}'.format(node2[1][1]))
            else:
                print('vertical; {} <=> {} <=> {}'.format(node1[1][0], partition_center[0], node2[1][0]))
                while node2[1][0] < partition_center[0] and node2[1][0] < partition_center[0]:
                    node2 = dist_pairs.pop()
                    print('   drawing another: {}'.format(node2[1][0]))
            self.dig_tunnel(*node1[1], *partition_center)
            self.dig_tunnel(*node2[1], *partition_center)
            self.dig(*partition_center, '%', tcod.yellow)
            ###############
            for x in range(0, self.mapDim[0]):
                for y in range(1, self.mapDim[1]):
                    self.game.screen.print(x, y, self.tiles[x][y], self.colors[x][y] * 1.00)
            tcod.console_flush()
            wait()
            ###############

    def dig_tunnel(self, x1, y1, x2, y2):
        absx = abs(x2 - x1)
        absy = abs(y2 - y1)
        dx = 0 if x1 == x2 else int(absx / (x2 - x1))
        dy = 0 if y1 == y2 else int(absy / (y2 - y1))
        horizontal = random.random() > 0.5
        distance = 0
        broken = 100
        self.dig(x1, y1)
        while x1 != x2 or y1 != y2:
            if y1 == y2 or (horizontal and x1 != x2):
                x1 += dx
            else:
                y1 += dy
            distance += 1
            if self.tiles[x1][y1] == tileset['wall']:
                broken = distance
            self.dig(x1, y1)
            if random.random() > 0.7 and distance - broken > 1:
                horizontal = not horizontal
        self.dig(x2, y2)

    def dig(self, x, y, tile=tileset['floor'], color=None, transparent=True, walkable=True):
        self.tiles[x][y] = tile
        if not color:
            r = random.randint(64, 128)
            color = tcod.Color(r, r, r)
        self.colors[x][y] = color
        self.transparent[x][y] = transparent
        self.walkable[x][y] = walkable

    def find_spot(self):
        while True:
            x = random.randint(1, self.mapDim[0] - 1)
            y = random.randint(self.mapTop + 1,
                               self.mapDim[1] - 1)
            if self.walkable[x][y] and not self.unit_at((x, y)):
                return x, y

    def movement(self, unit, check):
        if not adjacent(unit.pos, check):
            self.log.warning('{} tried to move more than 1 cell!'.format(unit.name))
            return
        if not self.walkable[check[0]][check[1]]:
            self.game.messenger.add('{} runs into the wall.'.format(unit.name))
            return
        target = self.unit_at(check)
        if target:
            if unit.name == 'Player' and unit != target:
                self.log.debug('{} engaged {}.'.format(unit.name, target.name))
                unit.attack(target)
                return
        else:
            unit.last_pos = unit.pos
            unit.pos = check

    def look_around(self):
        radius = 0  # self.game.player.sight_range
        pos = self.game.player.pos
        self.compute_fov(*pos, radius, algorithm=tcod.FOV_BASIC)

    def unit_at(self, where: tuple):
        for unit in self.units:
            if unit.pos == where:
                return unit
        return None

    def draw_map(self):
        self.game.screen.clear()
        if 'debug' in argv:
            for x in range(0, self.mapDim[0]):
                for y in range(1, self.mapDim[1]):
                    self.game.screen.print(x, y, self.tiles[x][y], self.colors[x][y] * 1.00)
        else:
            for x in range(0, self.mapDim[0]):
                for y in range(1, self.mapDim[1]):
                    if self.fov[x][y]:
                        self.explored[x][y] = True
                        self.game.screen.print(x, y, self.tiles[x][y], self.colors[x][y] * 1.00)
                    elif self.explored[x][y]:
                        self.game.screen.print(x, y, self.tiles[x][y], self.colors[x][y] * 0.20)
        for item in self.game.items.items_on_ground:
            if self.fov[item.pos[0]][item.pos[1]] or 'debug' in argv:
                self.game.screen.print(*item.pos, item.icon, item.color)
        for monster in self.game.monsters.monsterList:
            if self.fov[monster.pos[0]][monster.pos[1]] or 'debug' in argv:
                self.game.screen.print(*monster.pos, monster.icon, monster.color)
        self.game.screen.print(*self.game.player.pos, self.game.player.icon, self.game.player.color)

    def neighbors(self, of):
        x, y = of
        results = [(x-1, y), (x, y+1), (x+1, y), (x, y-1),
                   (x-1, y-1), (x+1, y-1), (x-1, y+1), (x+1, y+1)]
        results = list(filter(lambda p: 0 < p[0] <= self.mapDim[0] and 0 < p[1] <= self.mapDim[1], results))
        results = list(filter(lambda p: self.walkable[p[0]][p[1]], results))
        return results


class Pathfinder(object):
    def __init__(self, level, start):
        self.log = logging.getLogger(__name__)
        self.frontier = PriorityQueue()
        self.came_from = {}
        self.cost_so_far = {}
        self.level = level
        self.frontier.put((0, start))
        self.came_from[start] = None
        self.cost_so_far[start] = 0

    def heuristic(self, goal, current):
        dx = abs(current[0] - goal[0])
        dy = abs(current[1] - goal[1])
        return dx + dy - min(dx, dy) / 2

    def cost(self, fr, to):
        if abs(fr[0] - to[0]) == 0 or abs(fr[1] - to[1]) == 0:
            return 1
        return 1.5

    def find(self, goal):
        while not self.frontier.empty():
            current = self.frontier.get()[1]
            if current == goal:
                break
            for nxt in self.level.neighbors(current):
                new_cost = self.cost_so_far[current] + self.cost(current, nxt)
                if nxt not in self.cost_so_far or new_cost < self.cost_so_far[nxt]:
                    self.cost_so_far[nxt] = new_cost
                    priority = new_cost + self.heuristic(goal, nxt)
                    self.frontier.put((priority, nxt))
                    self.came_from[nxt] = current
        return self

    def path(self, start, goal):
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = self.came_from[current]
        path.reverse()
        self.log.debug('Pathfinder {} -> {}: {}'.format(start, goal, path))
        return path
