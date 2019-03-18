# -*- coding: utf-8 -*-

import random, math, logging;
from rogue import types;
from rogue.curse import CursesHelper as Curses;
from rogue.message import Messenger;

min_room_size = ( 6, 3 );
max_room_size = ( 19, 6 );

class Room:
    width = 0;
    height = 0;
    x = 0;
    y = 0;

    def __init__( self, dungeon, num ):
        while True:
            self.width = random.randint( min_room_size[0], max_room_size[0] );
            self.height = random.randint( min_room_size[1], max_room_size[1] );
            self.x = random.randint( 1, dungeon.mapDim[0] - self.width - 1 );
            self.y = random.randint( dungeon.mapTop + 1, dungeon.mapDim[1] - self.height - 1 );
            if not dungeon.alreadyTaken( self.x, self.y, self.x + self.width, self.y + self.height ):
                break;
        self.num = num;
        self.connected = [];
        logging.debug( 'Created room %d (w%d h%d) ( %d,%d - %d,%d )' % ( num, self.width, self.height, self.x, self.y,  self.x + self.width, self.y + self.height ) );
        for i in range( self.x, self.x + self.width ):
            for j in range( self.y, self.y + self.height ):
                dungeon.mapArray[j][i] = { 'type':types['floor'], 'visible':False, 'seen':False, 'blockMove':False, 'blockLOS':False };

    def __str__( self ):
        return 'room ' + str( self.num ) + '(' + str( self.x ) + ',' + str( self.y ) + ')';

    def __repr__( self ):
        return 'room ' + str( self.num );



class RogueMap:
    _instance = None;
    mapArray = [];
    rooms = [];
    mapDim = ( 0, 0 );
    mapTop = 1;
    min_rooms = 1;
    max_rooms = 1;

    def __init__( self, dimensions ):
        self.mapDim = dimensions;
        self.min_rooms = 5;
        self.max_rooms = self.mapDim[0] / max_room_size[0] * self.mapDim[1] / max_room_size[1];
        self.create_map();
        RogueMap._instance = self;



    def create_map( self ):
        self.mapArray = [
            [
                { 'type': '#', 'visible': False, 'seen': False, 'blockMove': True, 'blockLOS': True }
                for x in range( self.mapDim[0] )
            ] for y in range( self.mapDim[1] )];
        self.rooms = [ Room( self, i ) for i in range( random.randint( self.min_rooms, self.max_rooms ) ) ];
        logging.info( 'Trying with ' + str( len( self.rooms ) ) + ' rooms...' );
        self.connect_rooms();
        self.check_connections();



    def connect_rooms( self ):
        for first in self.rooms:
            if len( first.connected ) > 0:
                continue;
            second = self.get_nearest_room( first, self.rooms )[0];
            x1 = random.randint( first.x + 1, first.x + first.width - 2 );
            y1 = random.randint( first.y + 1, first.y + first.height - 2 );
            x2 = random.randint( second.x + 1, second.x + second.width - 2 );
            y2 = random.randint( second.y + 1, second.y + second.height - 2 );
            self.dig_tunnel( x1, y1, x2, y2 );
            first.connected.append( second.num );
            second.connected.append( first.num );
            logging.debug( 'Connected rooms %d and %d' % ( first.num, second.num ) );



    def get_nearest_room( self, source, roomList ):
        vectors = [ ( abs( source.x - r.x ), abs( source.y - r.y ), r.num ) for r in roomList if r.num != source.num ];
        nearest = min( vectors, key=lambda v: sum(p*p for p in v ));
        return next( ( r for r in self.rooms if r.num == nearest[2] ), None ), int( math.sqrt( nearest[0]*nearest[0] + nearest[1] * nearest[1] ) );



    def collect_connected_rooms( self, room, bagOfRooms ):
        if len( bagOfRooms ) == 0:
            bagOfRooms.add( room.num );
        if set( room.connected ).issubset( bagOfRooms ):
            return bagOfRooms;
        else:
            for r in room.connected:
                if r not in bagOfRooms:
                    bagOfRooms.add( r );
                    self.collect_connected_rooms( self.rooms[r], bagOfRooms );



    def check_connections( self ):
        roomGroups = [];
        for room in self.rooms:
            tempSet = set();
            self.collect_connected_rooms( room, tempSet );
            if tempSet not in roomGroups:
                roomGroups.append( tempSet );
        logging.info( 'Number of room groups: %d.' % len( roomGroups ) );
        if len( roomGroups ) > 1:
            matching = [];
            for num, thisGroup in enumerate( roomGroups ):
                groupCandidates = [];
                for thisRoom in thisGroup:
                    roomCandidates = [];
                    for enum, thatGroup in enumerate( roomGroups ):
                        if thisGroup == thatGroup:
                            continue;
                        roomCandidates.append( ( self.get_nearest_room( self.rooms[thisRoom], [ self.rooms[r] for r in thatGroup ] ), enum, thisRoom ) );
                    ( candidate, dist ), group, source = min( roomCandidates, key=lambda v:v[0][1] );
                    groupCandidates.append( ( candidate, dist, group, source ) );
                result, distance, group, source = min( groupCandidates, key=lambda v:v[1] );
                logging.debug( 'connection between room %2d - group %d and %d - is room %2d with distance %d.'
                                       % ( source, num, group, result.num, distance ) );
                matching.append( ( { num, group }, { source, result.num }, distance ) );
            logging.debug( matching );
            dungeon = [];
            for groupPair, roomPair, distance in matching:
                if groupPair not in [ pair[0] for pair in dungeon ]:
                    dungeon.append( ( groupPair, roomPair, distance ) );
                else:
                    stored = next( ( tup for tup in dungeon if tup[0] == groupPair ) );
                    if distance < stored[2]:
                        dungeon[dungeon.index( stored )] = ( groupPair, roomPair, distance );
            logging.debug( 'Number of necessary connections: %d.' % len( dungeon ) );
            for room1, room2 in [ tup[1] for tup in dungeon ]:
                first = self.rooms[room1];
                second = self.rooms[room2];
                x1 = random.randint( first.x + 1, first.x + first.width - 2 );
                y1 = random.randint( first.y + 1, first.y + first.height - 2 );
                x2 = random.randint( second.x + 1, second.x + second.width - 2 );
                y2 = random.randint( second.y + 1, second.y + second.height - 2 );
                self.dig_tunnel( x1, y1, x2, y2 );
                first.connected.append( second.num );
                second.connected.append( first.num );



    def dig_tunnel( self, x1, y1, x2, y2 ):
        absx = abs( x2 - x1 );
        absy = abs( y2 - y1 );
        dx = 0 if x1 == x2 else absx / ( x2 - x1 );
        dy = 0 if y1 == y2 else absy / ( y2 - y1 );
        horizontal = random.random() > 0.5;
        distance = 0;
        broken = 100;
        while x1 != x2 or y1 != y2:
            if y1 == y2 or ( horizontal and x1 != x2 ):
                x1 += dx;
            else:
                y1 += dy;
            distance += 1;
            if self.mapArray[y1][x1]['type'] == '#':
                broken = distance;
            self.mapArray[y1][x1] = { 'type':types['tunnel'], 'visible':False, 'seen':False, 'blockMove':False, 'blockLOS':False };
            if random.random() > 0.7 and distance - broken > 1:
                horizontal = not horizontal;



    @classmethod
    def findSpot( cls ):
        while True:
            x = random.randint( 1, cls._instance.mapDim[0] - 1 );
            y = random.randint( cls._instance.mapTop + 1, cls._instance.mapDim[1] - 1 );
            if not cls._instance.mapArray[y][x]['blockMove']:
                return x, y;



    def alreadyTaken( self, x1, y1, x2, y2 ):
        for x in range( x1 - 1, x2 + 1 ):
            for y in range( y1 - 1, y2 + 1 ):
                if self.mapArray[y][x]['type'] == types['floor']:
                    return True
        return False



    def lookAround( self, origin, radius, cheat ):
        for y in range( self.mapTop, len( self.mapArray ) ):
            for x in range( len( self.mapArray[0] ) ):
                if self.mapArray[y][x]['visible'] or cheat:
                    self.mapArray[y][x]['seen'] = True;
                self.mapArray[y][x]['visible'] = False;
        for xx in range( -radius, radius + 1 ):
            for yy in range( -radius, radius + 1 ):
                if xx == 0 and yy == 0:
                    continue;
                if xx * xx + yy * yy > radius * radius or xx * xx + yy * yy < radius * radius - radius - 1:
                    continue;
                self.lineOfSight( origin[0], origin[1], origin[0] + xx, origin[1] + yy );



    def lineOfSight( self, origin_x, origin_y, target_x, target_y ):
        target_x += 0.5 if target_x < origin_x else -0.5;
        target_y += 0.5 if target_y < origin_y else -0.5;
        dx = target_x - origin_x;
        dy = target_y - origin_y;
        length = max( abs( dx ), abs( dy ) );
        dx /= length;
        dy /= length;
        xx = origin_x;
        yy = origin_y;
        while length > 0:
            ix = int( xx + 0.5 );
            iy = int( yy + 0.5 );
            self.mapArray[iy][ix]['visible'] = True;
            if self.mapArray[iy][ix]['blockLOS'] or ( ix == target_x and iy == target_y ):
                break;
            xx += dx;
            yy += dy;
            length -= 1;



    @classmethod
    def isLoSbetween( cls, source, targetDoNotModify ):
        if source is targetDoNotModify:
            return True;
        targetx, targety = targetDoNotModify;
        targetx += 0.5 if targetx < source[0] else -0.5;
        targety += 0.5 if targety < source[1] else -0.5;
        dx = targetx - source[0];
        dy = targety - source[1];
        length = max( abs( dx ), abs( dy ) );
        dx /= length;
        dy /= length;
        xx = source[0];
        yy = source[1];
        thereIs = False;
        while length > 0:
            ix = int( xx + 0.5 );
            iy = int( yy + 0.5 );
            if cls._instance.mapArray[iy][ix]['blockLOS'] or ( ix == targetx and iy == targety ):
                thereIs = False;
                break;
            thereIs = True;
            xx += dx;
            yy += dy;
            length -= 1;
        return thereIs;



    @classmethod
    def movement( cls, unit, check ):
        if cls._instance.mapArray[unit.pos[1] + check[1]][unit.pos[0] + check[0]]['blockMove']:
            if unit.control is not 'ai':
                Messenger.add( 'You can\'t move there.' );
            return False;
        mon = cls._instance.whichMonsterAt( unit.pos[0] + check[0], unit.pos[1] + check[1] );
        if mon:
            if unit.control is 'player':
                logging.debug( 'Engaged %s.' % ( mon.name ) );
                unit.attack( mon );
                return False;
            else:
                return False;
        #elif Player.get_pos() == ( unit.pos[0] + check[0], unit.pos[1] + check[1] ) and unit.control is 'ai':
        unit.pos = ( unit.pos[0] + check[0], unit.pos[1] + check[1] );
        return True;



    def whichMonsterAt( self, x, y ):
        import rogue.monster;
        for mon in rogue.monster.Menagerie.monsterList:
            if mon.pos == ( x, y ):
                return mon;
        return None;



    def drawMap( self ):
        import rogue.monster;
        for x in range( self.mapDim[0] ):
            for y in range( self.mapTop, self.mapDim[1] ):
                if self.mapArray[y][x]['visible']:
                    Curses.print_at( x, y, self.mapArray[y][x]['type'], Curses.color( 'GRAY' ) );
                elif self.mapArray[y][x]['seen']:
                    Curses.print_at( x, y, self.mapArray[y][x]['type'], Curses.color( 'DARKGRAY' ) );
                else:
                    Curses.print_at( x, y, ' ' );
        for mon in rogue.monster.Menagerie.monsterList:
            if self.mapArray[mon.pos[1]][mon.pos[0]]['visible']:
                Curses.print_at( mon.pos[0], mon.pos[1], mon.letter, mon.color );
