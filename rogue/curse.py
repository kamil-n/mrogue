import curses;

class CursesHelper:
    stdscr = None;
    color = None;

    def __init__( self ):
        self.stdscr = curses.initscr();
        curses.curs_set( False );
        curses.noecho();
        self.stdscr.keypad( 1 );
        curses.start_color();
        curses.use_default_colors();
        curses.init_pair( 1, curses.COLOR_RED, curses.COLOR_BLACK );
        curses.init_pair( 2, curses.COLOR_GREEN, curses.COLOR_BLACK );
        curses.init_pair( 3, curses.COLOR_BLUE, curses.COLOR_BLACK );
        curses.init_pair( 4, curses.COLOR_CYAN, curses.COLOR_BLACK );
        curses.init_pair( 5, curses.COLOR_MAGENTA, curses.COLOR_BLACK );
        curses.init_pair( 6, curses.COLOR_YELLOW, curses.COLOR_BLACK );
        curses.init_pair( 7, curses.COLOR_BLACK, curses.COLOR_BLACK );
        self.color = {\
            'WHITE':    curses.color_pair( 0 ) | curses.A_BOLD,\
            'GRAY':     curses.color_pair( 0 ),\
            'RED':      curses.color_pair( 1 ) | curses.A_BOLD,\
            'DARKRED':  curses.color_pair( 1 ),\
            'GREEN':    curses.color_pair( 2 ) | curses.A_BOLD,\
            'DARKGREEN':curses.color_pair( 2 ),\
            'BLUE':     curses.color_pair( 3 ) | curses.A_BOLD,\
            'DARKBLUE': curses.color_pair( 3 ),\
            'LIGHTBLUE':curses.color_pair( 4 ) | curses.A_BOLD,\
            'AQUAMARINE':curses.color_pair( 4 ),\
            'PURPLE':   curses.color_pair( 5 ) | curses.A_BOLD,\
            'DARKPURPLE':curses.color_pair( 5 ),\
            'YELLOW':   curses.color_pair( 6 ) | curses.A_BOLD,\
            'BROWN':    curses.color_pair( 6 ),\
            'DARKGRAY': curses.color_pair( 7 ) | curses.A_BOLD\
        };

    def show( self, x, y, string, decoration = None ):
        if decoration == None:
            decoration = self.color['DARKGRAY'];
        self.stdscr.addstr( y, x, string, decoration );

    def close( self ):
        curses.curs_set( True );
        curses.echo();
        self.stdscr.keypad( 0 );
        curses.endwin();
