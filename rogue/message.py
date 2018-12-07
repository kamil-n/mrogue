import logging;

class Messenger():
    messageList = [];

    def show( self, messageLine, windowObject ):
        #TODO: zrobic to w nowym oknie
        if len( self.messageList ) > 1:
            while len( self.messageList ) > 0:
                tempMessage = '';
                while ( 73 - len( tempMessage ) ) > len( self.messageList[0] ):
                    tempMessage += self.messageList.pop( 0 ) + ' ';
                    if len( self.messageList ) == 0:
                        break;
                logging.debug( 'tempMessage = %s' % ( tempMessage ) );
                messageEnd = len( tempMessage );
                windowObject.show( 0, messageLine, tempMessage, windowObject.color['WHITE'] );
                tempMessage = '';
                if len( self.messageList ) > 0:
                    logging.debug( 'still messages left.' );
                    windowObject.show( messageEnd, 23, '-more-', windowObject.color['YELLOW'] );
                    windowObject.stdscr.getch();
                    windowObject.show( 0, messageLine, 79*' ' );
                windowObject.stdscr.refresh();
        elif len( self.messageList ) == 1:
            windowObject.show( 0, messageLine, self.messageList[0], windowObject.color['WHITE'] );
            windowObject.stdscr.refresh();

    def add( self, message ):
        self.messageList.append( message );
    
    def clear( self, messageLine, windowObject ):
        windowObject.show( 0, messageLine, 79*' ' );
        windowObject.stdscr.refresh();
        del self.messageList[:];
