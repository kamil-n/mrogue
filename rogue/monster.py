# -*- coding: utf-8 -*-

import logging, random;
from rogue.curse import CursesHelper as Curses;
from rogue.map import RogueMap;
from rogue import roll;
from rogue.player import Player;
from rogue.message import Messenger;

class Menagerie:
    #_instance = None;
    monsterList = [];

    def __init__( self, num ):
        monsterTemplates = [ MonsterTemplate( 'rat', 'r', Curses.color( 'DARKGRAY' ), '1d4-1', '1d4-1', 2, 12 ),
                             MonsterTemplate( 'kobold', 'k', Curses.color( 'RED' ), '1d6-1', '1d6-1', 1, 13 ),
                             MonsterTemplate( 'goblin', 'g', Curses.color( 'GREEN' ), '1d6-1', '1d8-1', 2, 13 ),
                             MonsterTemplate( 'orc', 'o', Curses.color( 'DARKGREEN' ), '1d8', '1d8', 3, 14 ),
                             MonsterTemplate( 'skeleton', 's', Curses.color( 'WHITE' ), '1d8', '1d4+1', 3, 11 ) ];
        for i in range( num ):
            startPosition = RogueMap.find_spot();
            tempMonster = Monster( startPosition, random.choice( monsterTemplates ) );
            self.monsterList.append( tempMonster );
            logging.debug( 'Created monster %s at %d,%d' % ( tempMonster.name, tempMonster.pos[0], tempMonster.pos[1] ) );
        #Menagerie._instance = self;

    def handle_monsters( self ):
        for monster in self.monsterList:
            if monster.is_in_range( Player.get_pos(), 5 ):
                if RogueMap.is_los_between( monster.pos, Player.get_pos() ):
                    if monster.is_in_range( Player.get_pos(), 1 ):
                        logging.debug( '%s is in melee range - attacking' % monster.name );
                        monster.attack( Player.get_ac() );
                    else:
                        monster.approach( Player.get_pos() );
        if not len( self.monsterList ):
            return False;
        return True;



class MonsterTemplate:
    def __init__( self, name, letter, color, hitDie, dmgDie, toHit, AC ):
        self.name = name;
        self.letter = letter;
        self.color = color;
        self.hitDie = hitDie;
        self.dmgDie = dmgDie;
        self.toHit = toHit;
        self.armorClass = AC;



class Monster:
    name = '';
    letter = 0;
    color = None;
    pos = None;
    hit = 0;
    damage = '';
    armorClass = 0; 
    hitPoints = 0;
    control = 'ai';

    def __init__( self, pos, template ):
        self.name = template.name;
        self.letter = template.letter;
        self.color = template.color;
        self.pos = pos;
        self.hit = template.toHit;
        self.damage = template.dmgDie;
        self.armorClass = template.armorClass;
        self.hitPoints = roll( template.hitDie );

    def take_damage( self, damage ):
        logging.debug( '%s is taking %d damage.' % ( self.name, damage ) );
        self.hitPoints -= damage;
        if self.hitPoints < 1:
            self.die();
        else:
            logging.debug( 'current hit points: %d.' % self.hitPoints );

    def die( self ):
        logging.info( '%s dies. (%d hp)' % ( self.name, self.hitPoints ) );
        Messenger.add( '%s dies.' % ( str.upper( self.name[0] ) + self.name[1:] ) );
        Menagerie.monsterList.remove( self );

    def attack( self, targetAC ):
        logging.info( '%s attacks player.' % self.name );
        attackRoll = roll( '1d20' );
        logging.debug( 'attack roll = %d + %d' % ( attackRoll, self.hit ) );
        criticalHit = attackRoll == 20;
        criticalMiss = attackRoll == 1;
        if criticalHit or attackRoll + self.hit >= targetAC:
            if criticalHit:
                logging.debug( 'Critical hit.' );
                Messenger.add( '%s critically hits you.' % ( str.upper( self.name[0] ) + self.name[1:] ) );
            else:
                logging.debug( 'Attack hit.' );
                Messenger.add( '%s hits you.' % ( str.upper( self.name[0] ) + self.name[1:] ) );
            damageRoll = roll( self.damage, criticalHit );
            logging.debug( 'damage roll = %d' % damageRoll );
            Player.take_damage( damageRoll );
        else:
            if criticalMiss:
                logging.debug( 'Critical miss' );
                Messenger.add( '%s critically misses you.' % ( str.upper( self.name[0] ) + self.name[1:] ) );
            else:
                logging.debug( 'Attack missed' );
                Messenger.add( '%s misses you.' % ( str.upper( self.name[0] ) + self.name[1:] ) );

    def is_in_range( self, targetPosition, radius ):
        return abs( self.pos[0] - targetPosition[0] ) <= radius and abs( self.pos[1] - targetPosition[1] ) <= radius;

    def approach( self, goal ):
        difx = goal[0] - self.pos[0];
        dify = goal[1] - self.pos[1];
        vertical = abs( dify ) > abs( difx );
        if vertical:
            if difx == 0:
                success = RogueMap.movement( self, ( 0, dify / abs( dify ) ) );
                if not success:
                    success = RogueMap.movement( self, ( -1, dify / abs( dify ) ) );
                    if not success:
                        RogueMap.movement( self, ( 1, dify / abs( dify ) ) );
            else:
                success = RogueMap.movement( self, ( difx / abs( difx ), dify / abs( dify ) ) );
                if not success:
                    success = RogueMap.movement( self, ( 0, dify / abs( dify ) ) );
                    if not success:
                        RogueMap.movement( self, ( -1 * difx / abs( difx ), dify / abs( dify ) ) );
        else:
            if dify == 0:
                success = RogueMap.movement( self, ( difx / abs( difx ), 0 ) );
                if not success:
                    success = RogueMap.movement( self, ( difx / abs( difx ), -1 ) );
                    if not success:
                        RogueMap.movement( self, ( difx / abs( difx ), 1 ) );
            else:
                success = RogueMap.movement( self, ( difx / abs( difx ), dify / abs( dify ) ) );
                if not success:
                    success = RogueMap.movement( self, ( difx / abs( difx ), 0 ) );
                    if not success:
                        RogueMap.movement( self, ( difx / abs( difx ), -1 * dify / abs( dify ) ) );
            
