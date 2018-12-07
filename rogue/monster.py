import random;
import logging;
from map import Point;

class Menagerie():
    gameObject = None;
    monsterList = [];

    def __init__( self, game, num ):
        self.gameObject = game;
        monsterTemplates = [];
        monsterTemplates.append( MonsterTemplate( 'rat', 'r', self.gameObject.window.color['DARKGRAY'], '1d4-1', '1d4-1', 2, 12 ) );
        monsterTemplates.append( MonsterTemplate( 'kobold', 'k', self.gameObject.window.color['RED'], '1d6-1', '1d6-1', 1, 13 ) );
        monsterTemplates.append( MonsterTemplate( 'goblin', 'g', self.gameObject.window.color['GREEN'], '1d6-1', '1d8-1', 2, 13 ) );
        monsterTemplates.append( MonsterTemplate( 'orc', 'o', self.gameObject.window.color['DARKGREEN'], '1d8', '1d8', 3, 14 ) );
        monsterTemplates.append( MonsterTemplate( 'skeleton', 's', self.gameObject.window.color['WHITE'], '1d8', '1d4+1', 3, 11 ) );
        for i in range( num ):
            startPosition = self.gameObject.level.findSpot();
            tempMonster = Monster( self.gameObject, startPosition, random.choice( monsterTemplates ) );
            self.monsterList.append( tempMonster );
            logging.debug( 'Created monster %s at %d,%d' % ( tempMonster.name, tempMonster.pos.x, tempMonster.pos.y ) );

    def handleMonsters( self ):
        for monster in self.monsterList:
            if monster.isInRange( self.gameObject.player.pos, 5 ):
                if self.gameObject.level.isLoSbetween( monster.pos, self.gameObject.player.pos ):
                    if monster.isInRange( self.gameObject.player.pos, 1 ):
                        logging.debug( '%s is in melee range - attacking' % ( monster.name ) );
                        monster.attack( self.gameObject.player );
                    else:
                        monster.approach( self.gameObject.player.pos );



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
    gameObject = None;
    name = '';
    letter = 0;
    color = None;
    pos = None;
    hit = 0;
    damage = '';
    armorClass = 0; 
    hitPoints = 0;
    control = 'ai';

    def __init__( self, game, pos, template ):
        self.gameObject = game;
        self.name = template.name;
        self.letter = template.letter;
        self.color = template.color;
        self.pos = pos;
        self.hit = template.toHit;
        self.damage = template.dmgDie;
        self.armorClass = template.armorClass;
        self.hitPoints = self.gameObject.roll( template.hitDie );

    def takeDamage( self, damage ):
        logging.debug( '%s is taking %d damage.' % ( self.name, damage ) );
        self.hitPoints -= damage;
        if self.hitPoints < 1:
            self.die();
        else:
            logging.debug( 'current hit points: %d.' % ( self.hitPoints ) );

    def die( self ):
        logging.info( '%s dies. (%d hp)' % ( self.name, self.hitPoints ) );
        self.gameObject.messenger.add( '%s dies.' % ( str.upper( self.name[0] ) + self.name[1:] ) );
        self.gameObject.monsters.monsterList.remove( self );

    def attack( self, playerObject ):
        logging.info( '%s attacks player.' % ( self.name ) );
        attackRoll = self.gameObject.roll( '1d20' );
        logging.debug( 'attack roll = %d + %d' % ( attackRoll, self.hit ) );
        criticalHit = attackRoll == 20;
        criticalMiss = attackRoll == 1;
        if criticalHit or attackRoll + self.hit >= playerObject.armorClass:
            if criticalHit:
                logging.debug( 'Critical hit.' );
                self.gameObject.messenger.add( '%s critically hits you.' % ( str.upper( self.name[0] ) + self.name[1:] ) );
            else:
                logging.debug( 'Attack hit.' );
                self.gameObject.messenger.add( '%s hits you.' % ( str.upper( self.name[0] ) + self.name[1:] ) );
            damageRoll = self.gameObject.roll( self.damage, criticalHit );
            logging.debug( 'damage roll = %d' % ( damageRoll ) );
            playerObject.takeDamage( damageRoll );
        else:
            if criticalMiss:
                logging.debug( 'Critical miss' );
                self.gameObject.messenger.add( '%s critically misses you.' % ( str.upper( self.name[0] ) + self.name[1:] ) );
            else:
                logging.debug( 'Attack missed' );
                self.gameObject.messenger.add( '%s misses you.' % ( str.upper( self.name[0] ) + self.name[1:] ) );

    def isInRange( self, targetPosition, radius ):
        return abs( self.pos.x - targetPosition.x ) <= radius and abs( self.pos.y - targetPosition.y ) <= radius;

    def approach( self, goal ):
        difx = goal.x - self.pos.x;
        dify = goal.y - self.pos.y;
        vertical = abs( dify ) > abs( difx );
        if vertical:
            if difx == 0:
                success = self.gameObject.level.movement( self, Point( 0, dify / abs( dify ) ) );
                if not success:
                    success = self.gameObject.level.movement( self, Point( -1, dify / abs( dify ) ) );
                    if not success:
                        self.gameObject.level.movement( self, Point( 1, dify / abs( dify ) ) );
            else:
                success = self.gameObject.level.movement( self, Point( difx / abs( difx ), dify / abs( dify ) ) );
                if not success:
                    success = self.gameObject.level.movement( self, Point( 0, dify / abs( dify ) ) );
                    if not success:
                        self.gameObject.level.movement( self, Point( -1 * difx / abs( difx ), dify / abs( dify ) ) );
        else:
            if dify == 0:
                success = self.gameObject.level.movement( self, Point( difx / abs( difx ), 0 ) );
                if not success:
                    success = self.gameObject.level.movement( self, Point( difx / abs( difx ), -1 ) );
                    if not success:
                        self.gameObject.level.movement( self, Point( difx / abs( difx ), 1 ) );
            else:
                success = self.gameObject.level.movement( self, Point( difx / abs( difx ), dify / abs( dify ) ) );
                if not success:
                    success = self.gameObject.level.movement( self, Point( difx / abs( difx ), 0 ) );
                    if not success:
                        success = self.gameObject.level.movement( self, Point( difx / abs( difx ), -1 * dify / abs( dify ) ) );
            
