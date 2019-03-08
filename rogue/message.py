import logging;
from rogue.curse import CursesHelper as Curses;

class Messenger():
    _instance = None;
    messageList = [];
    scrDim = tuple();

    def __init__( self, screenDim ):
        self. messageList = [];
        Messenger._instance = self;
        self.scrDim = screenDim;

    def show( self, messageLine ):
        #TODO: zrobic to w nowym oknie
        if len( self.messageList ) > 1:
            while len( self.messageList ) > 0:
                tempMessage = '';
                while ( self.scrDim[0] - 7 - len( tempMessage ) ) > len( self.messageList[0] ):
                    tempMessage += self.messageList.pop( 0 ) + ' ';
                    if len( self.messageList ) == 0:
                        break;
                logging.debug( 'tempMessage = %s' % ( tempMessage ) );
                messageEnd = len( tempMessage );
                Curses.print_at( 0, messageLine, tempMessage, Curses.color( 'WHITE' ) );
                tempMessage = '';
                if len( self.messageList ) > 0:
                    logging.debug( 'still messages left.' );
                    Curses.print_at( messageEnd, messageLine, '-more-', Curses.color( 'YELLOW' ) );
                    Curses.wait();
                    Curses.print_at( 0, messageLine, ( self.scrDim[0] - 1 ) * ' ' );
                Curses.refresh();
        elif len( self.messageList ) == 1:
            Curses.print_at( 0, messageLine, self.messageList[0], Curses.color( 'WHITE' ) );
            Curses.refresh();

    @classmethod
    def add( cls, message ):
        cls._instance.messageList.append( message );
    
    def clear( self, messageLine ):
        Curses.print_at( 0, messageLine, ( self.scrDim[0] - 1 ) * ' ' );
        Curses.refresh();
        del self.messageList[:];
