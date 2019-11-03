# -*- coding: utf-8 -*-

import logging
import math
import random
from rogue.pgame import MapImage

min_room_size = (6, 3)
max_room_size = (12, 6)


class Room(object):
    width = 0
    height = 0
    x = 0
    y = 0

    def __init__(self, dungeon, num):
        while True:
            self.width = random.randint(min_room_size[0], max_room_size[0])
            self.height = random.randint(min_room_size[1], max_room_size[1])
            self.x = random.randint(1, dungeon.mapDim[0] - self.width - 1)
            self.y = random.randint(dungeon.mapTop + 1,
                                    dungeon.mapDim[1] - self.height - 1)
            if not dungeon.already_taken(self.x, self.y,
                                         self.x + self.width,
                                         self.y + self.height):
                break
        self.num = num
        self.connected = []
        logging.debug('Created room %d (w%d h%d) ( %d,%d - %d,%d )' % (
            num, self.width, self.height, self.x, self.y,
            self.x + self.width, self.y + self.height))
        for i in range(self.x, self.x + self.width):
            for j in range(self.y, self.y + self.height):
                dungeon.mapArray[j][i] = {'type': dungeon.tiles['floor'],
                                          'visible': False,
                                          'blockMove': False,
                                          'blockLOS': False}

    @property
    def __str__(self):
        return 'room {} ({},{})'.format(self.num, self.x, self.y)

    @property
    def __repr__(self):
        return 'room ' + str(self.num)


class RogueMap(object):
    game = None
    mapArray = []
    rooms = []
    mapDim = (0, 0)
    map_image = None
    mapTop = 1
    min_rooms = 1
    max_rooms = 1
    tiles = {}

    def __init__(self, game):
        self.mapDim = (game.interface.dimensions[0],
                       game.interface.dimensions[1] - 1)
        self.map_image = MapImage(self.mapDim[0], self.mapDim[1])
        self.game = game
        self.min_rooms = 5
        self.max_rooms = int(self.mapDim[0] / max_room_size[0] *
                             self.mapDim[1] / max_room_size[1]) - self.min_rooms
        logging.debug('self.max_rooms is {}'.format(self.max_rooms))
        self.tiles = {
            'wall': self.game.interface.tileset[854],
            'floor': self.game.interface.tileset[861]}
        self.create_map()

    def create_map(self):
        self.mapArray = [
            [
                {'type': self.tiles['wall'],
                 'visible': False,
                 'blockMove': True,
                 'blockLOS': True}
                for x in range(self.mapDim[0])
            ] for y in range(self.mapDim[1])]
        num_rooms = random.randint(self.min_rooms, self.max_rooms)
        self.rooms = [Room(self, i) for i in range(num_rooms)]
        logging.info('Trying with ' + str(len(self.rooms)) + ' rooms...')
        self.connect_rooms()
        self.check_connections()

    def connect_rooms(self):
        for first in self.rooms:
            if len(first.connected) > 0:
                continue
            second = self.get_nearest_room(first, self.rooms)[0]
            x1 = random.randint(first.x + 1, first.x + first.width - 2)
            y1 = random.randint(first.y + 1, first.y + first.height - 2)
            x2 = random.randint(second.x + 1, second.x + second.width - 2)
            y2 = random.randint(second.y + 1, second.y + second.height - 2)
            self.dig_tunnel(x1, y1, x2, y2)
            first.connected.append(second.num)
            second.connected.append(first.num)
            logging.debug('Connected rooms %d and %d' % (first.num, second.num))

    def get_nearest_room(self, source, room_list):
        vectors = [(abs(source.x - r.x), abs(source.y - r.y), r.num) for r in
                   room_list if r.num != source.num]
        nearest = min(vectors, key=lambda v: sum(p * p for p in v))
        return next((r for r in self.rooms if r.num == nearest[2]), None), int(
            math.sqrt(nearest[0] * nearest[0] + nearest[1] * nearest[1]))

    def collect_connected_rooms(self, room, bag_of_rooms):
        if len(bag_of_rooms) == 0:
            bag_of_rooms.add(room.num)
        if set(room.connected).issubset(bag_of_rooms):
            return bag_of_rooms
        else:
            for r in room.connected:
                if r not in bag_of_rooms:
                    bag_of_rooms.add(r)
                    self.collect_connected_rooms(self.rooms[r], bag_of_rooms)

    def check_connections(self):
        room_groups = []
        for room in self.rooms:
            temp_set = set()
            self.collect_connected_rooms(room, temp_set)
            if temp_set not in room_groups:
                room_groups.append(temp_set)
        logging.info('Number of room groups: %d.' % len(room_groups))
        if len(room_groups) > 1:
            matching = []
            for num, thisGroup in enumerate(room_groups):
                group_candidates = []
                for thisRoom in thisGroup:
                    room_candidates = []
                    for enum, thatGroup in enumerate(room_groups):
                        if thisGroup == thatGroup:
                            continue
                        room_candidates.append(
                            (self.get_nearest_room(self.rooms[thisRoom],
                                                   [self.rooms[r] for r in
                                                    thatGroup]),
                             enum,
                             thisRoom))
                    (candidate, dist), group, source = \
                        min(room_candidates, key=lambda v: v[0][1])
                    group_candidates.append((candidate, dist, group, source))
                result, distance, group, source = min(group_candidates,
                                                      key=lambda v: v[1])
                logging.debug('connection between room %2d - group %d and %d - '
                              'is room %2d with distance %d.'
                              % (source, num, group, result.num, distance))
                matching.append(({num, group}, {source, result.num}, distance))
            logging.debug(matching)
            dungeon = []
            for groupPair, roomPair, distance in matching:
                if groupPair not in [pair[0] for pair in dungeon]:
                    dungeon.append((groupPair, roomPair, distance))
                else:
                    stored = next(
                        (tup for tup in dungeon if tup[0] == groupPair))
                    if distance < stored[2]:
                        dungeon[dungeon.index(stored)] = (groupPair,
                                                          roomPair,
                                                          distance)
            logging.debug('Number of necessary connections: %d.' % len(dungeon))
            for room1, room2 in [tup[1] for tup in dungeon]:
                first = self.rooms[room1]
                second = self.rooms[room2]
                x1 = random.randint(first.x + 1, first.x + first.width - 2)
                y1 = random.randint(first.y + 1, first.y + first.height - 2)
                x2 = random.randint(second.x + 1, second.x + second.width - 2)
                y2 = random.randint(second.y + 1, second.y + second.height - 2)
                self.dig_tunnel(x1, y1, x2, y2)
                first.connected.append(second.num)
                second.connected.append(first.num)

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
            if self.mapArray[y1][x1]['type'] == self.tiles['wall']:
                broken = distance
            self.mapArray[y1][x1] = {'type': self.tiles['floor'],
                                     'visible': False,
                                     'blockMove': False,
                                     'blockLOS': False}
            if random.random() > 0.7 and distance - broken > 1:
                horizontal = not horizontal

    def find_spot(self):
        while True:
            x = random.randint(1, self.mapDim[0] - 1)
            y = random.randint(self.mapTop + 1,
                               self.mapDim[1] - 1)
            if not self.mapArray[y][x]['blockMove']:
                return x, y

    def already_taken(self, x1, y1, x2, y2):
        for x in range(x1 - 1, x2 + 1):
            for y in range(y1 - 1, y2 + 1):
                if self.mapArray[y][x]['type'] == self.tiles['floor']:
                    return True
        return False

    def movement(self, unit, check):
        if self.mapArray[unit.pos[1] + check[1]][
            unit.pos[0] + check[0]]['blockMove']:
            if unit.name == 'Player':
                self.game.messenger.add('You can\'t move there.')
            return False
        monster = None
        for mon in self.game.monsters.monsterList:
            if mon.pos == (unit.pos[0] + check[0], unit.pos[1] + check[1]):
                monster = mon
        if monster:
            if unit.name is 'Player':
                logging.debug('Engaged %s.' % monster.name)
                unit.attack(monster)
                return False
            else:
                return False
        # elif Player.get_pos() == ( unit.pos[0] + check[0],
        # unit.pos[1] + check[1] ) and unit.control is 'ai':
        unit.pos = (unit.pos[0] + check[0], unit.pos[1] + check[1])
        return True

    def look_around(self):
        radius = self.game.player.sight_range
        pos = self.game.player.pos
        for x in range(pos[0] - radius - 1, pos[0] + radius + 2):
            for y in range(pos[1] - radius - 1, pos[1] + radius + 2):
                if 0 < x >= self.mapDim[0] or 0 < y >= self.mapDim[1]:
                    continue
                self.mapArray[y][x]['visible'] = False
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                if x == 0 and y == 0:
                    continue
                if x * x + y * y > radius * radius or \
                        x * x + y * y < radius * radius - radius - 1:
                    continue
                self.line_of_sight(pos[0], pos[1], pos[0] + x, pos[1] + y)

    def line_of_sight(self, origin_x, origin_y, target_x, target_y):
        target_x += 0.5 if target_x < origin_x else -0.5
        target_y += 0.5 if target_y < origin_y else -0.5
        dx = target_x - origin_x
        dy = target_y - origin_y
        length = max(abs(dx), abs(dy))
        dx /= length
        dy /= length
        xx = origin_x
        yy = origin_y
        while length > 0:
            ix = int(xx + 0.5)
            iy = int(yy + 0.5)
            self.mapArray[iy][ix]['visible'] = True
            self.map_image.add(self.mapArray[iy][ix]['type'], (ix, iy))
            if self.mapArray[iy][ix]['blockLOS'] or (
                    ix == target_x and iy == target_y):
                break
            xx += dx
            yy += dy
            length -= 1

    def is_los_between(self, source, target_do_not_modify):
        if source is target_do_not_modify:
            return True
        targetx, targety = target_do_not_modify
        targetx += 0.5 if targetx < source[0] else -0.5
        targety += 0.5 if targety < source[1] else -0.5
        dx = targetx - source[0]
        dy = targety - source[1]
        length = max(abs(dx), abs(dy))
        dx /= length
        dy /= length
        xx = source[0]
        yy = source[1]
        there_is = False
        while length > 0:
            ix = int(xx + 0.5)
            iy = int(yy + 0.5)
            if self.mapArray[iy][ix]['blockLOS'] or (
                    ix == targetx and iy == targety):
                there_is = False
                break
            there_is = True
            xx += dx
            yy += dy
            length -= 1
        return there_is

    def draw_map(self):
        itfc = self.game.interface
        radius = self.game.player.sight_range
        pos = self.game.player.pos
        self.map_image.show(itfc.screen)
        for x in range(pos[0] - radius, pos[0] + radius + 1):
            for y in range(pos[1] - radius, pos[1] + radius + 1):
                if 0 < x >= self.mapDim[0] or 0 < y >= self.mapDim[1]:
                    continue
                if self.mapArray[y][x]['visible']:
                    itfc.print_at(x, y, itfc.highlight)
        # TODO: move this out
        for mon in self.game.monsters.monsterList:
            if self.mapArray[mon.pos[1]][mon.pos[0]]['visible']:
                itfc.print_at(mon.pos[0], mon.pos[1], mon.tile)
