import logging;
from rogue import roll;
from rogue.map import RogueMap;
from rogue.curse import CursesHelper as Curses;
from rogue.message import Messenger;

class Player:
    _instance = None;
    pos = None;
    color = None;
    range = 0;
    hit = 0;
    damage = '';
    armorClass = 0;
    hitpoints = 0;
    maxHealth = 0;
    control = 'player';

    def __init__( self, range = 6 ):
        self.pos = RogueMap.findSpot();
        self.color = Curses.color( 'YELLOW' );
        self.range = range;
        self.hit = 3;
        self.damage = "1d6+1";
        self.armorClass = 14;
        self.hitPoints = 12;
        self.maxHealth = 12;
        Player._instance = self;

    @classmethod
    def get_pos( cls ):
        return cls._instance.pos;

    @classmethod
    def get_AC( cls ):
        return cls._instance.armorClass;

    def attack( self, targetMonster ):
        logging.info( 'Player attacks %s.' % ( targetMonster.name ) );
        attackRoll = roll( '1d20' );
        logging.debug( 'attack roll = %d + %d' % ( attackRoll, self.hit ) );
        criticalHit = attackRoll == 20;
        criticalMiss = attackRoll == 1;
        if criticalHit or attackRoll + self.hit >= targetMonster.armorClass:
            if criticalHit:
                logging.debug( 'Critical hit.' );
                Messenger.add( 'You critically hit %s.' % ( targetMonster.name ) );
            else:
                logging.debug( 'Attack hit.' );
                Messenger.add( 'You hit %s.' % ( targetMonster.name ) );
            damageRoll = roll( self.damage, criticalHit );
            logging.debug( 'damage roll = %d' % ( damageRoll ) );
            targetMonster.takeDamage( damageRoll );
        else:
            if criticalMiss:
                logging.debug( 'Critical miss' );
                Messenger.add( 'You critically missed %s.' % ( targetMonster.name ) );
            else:
                logging.debug( 'Attack missed' );
                Messenger.add( 'You missed %s.' % ( targetMonster.name ) );

    @classmethod
    def takeDamage( cls, damage ):
        logging.debug( 'Player is taking %d damage.' % ( damage ) );
        cls._instance.hitPoints -= damage;
        if cls._instance.hitPoints < 1:
            logging.info( 'Player dies. (%d hp)' % ( cls._instance.hitPoints ) );
            Messenger.add( 'You die.' );
        else:
            logging.debug( 'current hit points: %d.' % ( cls._instance.hitPoints ) );

    def showStatus( self, statusLine ):
        Curses.print_at( 4, statusLine, '%2d/%d' % ( self.hitPoints, self.maxHealth ), Curses.color( 'GREEN' ) );
        Curses.print_at( 16, statusLine, '%2d' % ( self.armorClass ), Curses.color( 'LIGHTBLUE' ) );
        Curses.print_at( 26, statusLine, '%d/%s' % ( self.hit, self.damage ), Curses.color( 'RED' ) );
