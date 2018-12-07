import logging;

class Player:
    gameObject = None;
    pos = None;
    color = None;
    range = 0;
    hit = 0;
    damage = '';
    armorClass = 0;
    hitpoints = 0;
    maxHealth = 0;
    control = 'player';

    def __init__( self, game, range = 6 ):
        self.gameObject = game;
        self.pos = self.gameObject.level.findSpot();
        self.color = self.gameObject.window.color['YELLOW'];
        self.range = range;
        self.hit = 3;
        self.damage = "1d6+1";
        self.armorClass = 14;
        self.hitPoints = 12;
        self.maxHealth = 12;

    def attack( self, targetMonster ):
        logging.info( 'Player attacks %s.' % ( targetMonster.name ) );
        attackRoll = self.gameObject.roll( '1d20' );
        logging.debug( 'attack roll = %d + %d' % ( attackRoll, self.hit ) );
        criticalHit = attackRoll == 20;
        criticalMiss = attackRoll == 1;
        if criticalHit or attackRoll + self.hit >= targetMonster.armorClass:
            if criticalHit:
                logging.debug( 'Critical hit.' );
                self.gameObject.messenger.add( 'You critically hit %s.' % ( targetMonster.name ) );
            else:
                logging.debug( 'Attack hit.' );
                self.gameObject.messenger.add( 'You hit %s.' % ( targetMonster.name ) );
            damageRoll = self.gameObject.roll( self.damage, criticalHit );
            logging.debug( 'damage roll = %d' % ( damageRoll ) );
            targetMonster.takeDamage( damageRoll );
        else:
            if criticalMiss:
                logging.debug( 'Critical miss' );
                self.gameObject.messenger.add( 'You critically missed %s.' % ( targetMonster.name ) );
            else:
                logging.debug( 'Attack missed' );
                self.gameObject.messenger.add( 'You missed %s.' % ( targetMonster.name ) );

    def takeDamage( self, damage ):
        logging.debug( 'Player is taking %d damage.' % ( damage ) );
        self.hitPoints -= damage;
        if self.hitPoints < 1:
            logging.info( 'Player dies. (%d hp)' % ( self.hitPoints ) );
            self.gameObject.messenger.add( 'You die.' );
        else:
            logging.debug( 'current hit points: %d.' % ( self.hitPoints ) );

    def showStatus( self, statusLine, cursesObject ):
        cursesObject.show( 4, statusLine, '%2d/%d' % ( self.hitPoints, self.maxHealth ), cursesObject.color['GREEN'] );
        cursesObject.show( 16, statusLine, '%2d' % ( self.armorClass ), cursesObject.color['LIGHTBLUE'] );
        cursesObject.show( 26, statusLine, '%d/%s' % ( self.hit, self.damage ), cursesObject.color['RED'] );
