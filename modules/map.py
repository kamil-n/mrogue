# -*- coding: utf-8 -*-

import logging
import numpy
from queue import PriorityQueue
import random
import tcod.bsp
import tcod.map
from modules import adjacent


class RogueMap(tcod.map.Map):
    game = None
    mapTop = 1

    def __init__(self, game):
        self.mapDim = (game.screen.width, game.screen.height - 1)
        super().__init__(self.mapDim[0], self.mapDim[1], 'F')
        self.tiles = numpy.full((self.mapDim[0], self.mapDim[1]), '#', order='F')
        self.explored = numpy.zeros((self.mapDim[0], self.mapDim[1]), bool, order='F')
        self.game = game
        self.objects_on_map = []
        self.units = []
        self.log = logging.getLogger(__name__)
        self.tileset = {'wall': '#', 'floor': '.'}
        bsp = tcod.bsp.BSP(0, 0, self.mapDim[0], self.mapDim[1])
        bsp.split_recursive(5, 15, 10, 2.0, 0.1)
        offset = 2
        for node in bsp.pre_order():
            '''if node.horizontal:
                for x in range(node.x, node.x + node.w):
                    self.tiles[x][node.position] = 'o'
            else:
                for y in range(node.y, node.y + node.h):
                    self.tiles[node.position][y] = 'o'''''
            if node.children:
                n1, n2 = node.children
                x1, y1 = n1.x + n1.w // 2, n1.y + n1.h // 2
                x2, y2 = n2.x + n2.w // 2, n2.y + n2.h // 2
                self.dig_tunnel(x1, y1, x2, y2)
            else:
                if random.random() < 0.5:
                    for x in range(node.x+offset+1, node.x+node.w-offset):
                        for y in range(node.y+offset+1, node.y + node.h-offset):
                            self.tiles[x][y] = self.tileset['floor']
                            self.transparent[x][y] = True
                            self.walkable[x][y] = True

    def dig_tunnel(self, x1, y1, x2, y2):
        absx = abs(x2 - x1)
        absy = abs(y2 - y1)
        dx = 0 if x1 == x2 else int(absx / (x2 - x1))
        dy = 0 if y1 == y2 else int(absy / (y2 - y1))
        horizontal = random.random() > 0.5
        distance = 0
        broken = 100
        while x1 != x2 or y1 != y2:
            if y1 == y2 or (horizontal and x1 != x2):
                x1 += dx
            else:
                y1 += dy
            distance += 1
            if self.tiles[x1][y1] == self.tileset['wall']:
                broken = distance
            self.tiles[x1][y1] = self.tileset['floor']
            self.transparent[x1][y1] = True
            self.walkable[x1][y1] = True
            if random.random() > 0.7 and distance - broken > 1:
                horizontal = not horizontal

    def find_spot(self):
        while True:
            x = random.randint(1, self.mapDim[0] - 1)
            y = random.randint(self.mapTop + 1,
                               self.mapDim[1] - 1)
            if self.walkable[x][y]:  # and not self.game.interface.unit_at((x, y)):
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
        for x in range(0, self.mapDim[0]):
            for y in range(1, self.mapDim[1]):
                if self.fov[x][y]:
                    self.explored[x][y] = True
                    self.game.screen.print(x, y, self.tiles[x][y], (160, 160, 160))
                elif self.explored[x][y]:
                    self.game.screen.print(x, y, self.tiles[x][y], (64, 64, 64))
        for item in self.game.items.items_on_ground:
            if self.fov[item.pos[0]][item.pos[1]]:
                self.game.screen.print(*item.pos, item.icon, item.color)
        for monster in self.game.monsters.monsterList:
            if self.fov[monster.pos[0]][monster.pos[1]]:
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
