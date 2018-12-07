import sys;
import os;
import logging;
import random;
import curses;
from rogue.map import RogueMap, Point;
from rogue.player import Player;
from rogue.curse import CursesHelper;
from rogue.monster import Menagerie;
from rogue.message import Messenger;



class Rogue():
    mapDim = Point( 80, 23 );
    statusLine = 0;
    messageLine = 23;
    turn = 0;
    player = None;
    level = None;
    window = None;
    monsters = None;
    messenger = None;

    def __init__( self ):
        if os.path.isfile( 'rogue.log' ):
            os.remove( 'rogue.log' );
        logging.basicConfig( filename = 'rogue.log', level = logging.DEBUG );
        logging.info( '======== Game start. ========' );
        self.window = CursesHelper();
        self.level = RogueMap( self );
        self.player = Player( self );
        self.monsters = Menagerie( self, 10 );
        self.messenger = Messenger();
        self.window.show( 0, self.statusLine, 'HP:', self.window.color['WHITE'] );
        self.window.show( 12, self.statusLine, 'AC:', self.window.color['WHITE'] );
        self.window.show( 21, self.statusLine, 'ATK:', self.window.color['WHITE'] );

    def mainloop( self ):
        key = 1;
        while key != ord( 'Q' ):
            logging.info( '== Turn %d. ==' % ( self.turn ) );
            self.level.lookAround( self.player.pos, self.player.range, sys.argv == ['rogue.py', 'seethrough'] );
            self.monsters.handleMonsters();
            self.level.drawMap();
            self.window.show( self.player.pos.x, self.player.pos.y, '@', self.player.color );
            self.messenger.show( self.messageLine, self.window );
            self.player.showStatus( self.statusLine, self.window );
            self.turn += 1;
            if self.player.hitPoints < 1:
                self.window.stdscr.refresh();
                self.window.stdscr.getch();
                self.window.close();
                break;
            key = self.window.stdscr.getch();
            self.messenger.clear( self.messageLine, self.window );
            #movement:
            check = Point( 0, 0 );
            if key in range( 49, 57 + 1 ):
                if key in ( 49, 52, 55 ):
                    check.x -= 1;
                elif key in ( 51, 54, 57 ):
                    check.x += 1;
                if key > 54:
                    check.y -= 1;
                elif key < 52:
                    check.y += 1;
            elif key in ( curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP, curses.KEY_DOWN ):
                if key == curses.KEY_LEFT:
                    check.x -= 1;
                elif key == curses.KEY_RIGHT:
                    check.x += 1;
                elif key == curses.KEY_UP:
                    check.y -= 1;
                elif key == curses.KEY_DOWN:
                    check.y += 1;
            else:
                keyChar = '';
                if key < 256:
                    keyChar = chr( key );
                logging.warn( 'Key \'%s\' (%d) not supported.' % ( keyChar, key ) );
                self.messenger.add( 'Unknown command.' );
            self.level.movement( self.player, check );
            self.window.stdscr.refresh();

    def roll( self, dieString, crit = False ):
        separatorIndex = dieString.index( 'd' );
        numDie = int( dieString[:separatorIndex] );
        typeDie = dieString[separatorIndex+1:];
        if crit:
            logging.warn( 'WE HAVE A FUCKING CRIT!!!' );
            numDie *= 2;
            dieString = str( numDie ) + dieString[separatorIndex:];
        modifier = 0;
        modifierIndex = -1;
        if '-' in typeDie:
            modifierIndex = typeDie.index( '-' );
        elif '+' in typeDie:
            modifierIndex = typeDie.index( '+' );
        if not modifierIndex == -1:
            modifier = int( typeDie[modifierIndex:] );
            typeDie = int( typeDie[:modifierIndex] );
        else:
            typeDie = int( typeDie );
        rollResult = 0;
        resultString = '';
        for i in range( numDie ):
            roll = random.randint( 1, typeDie );
            resultString += str( roll ) + '+';
            rollResult += roll;
        rollResult += modifier;
        resultString = resultString[:-1];
        if rollResult < 1:
            rollResult = 1;
        if modifier < 0:
            resultString += str(modifier);
        elif modifier > 0:
            resultString += '+' + str( modifier ); 
        logging.info( 'rolling %s: %s = %d' % ( dieString, resultString, rollResult ) );
        return rollResult;

try:
    rogue = Rogue();
    rogue.mainloop();
except:
    rogue.window.close();
    e = sys.exc_info()[1];
    print( e );
    raise;
else:
    rogue.window.close();
