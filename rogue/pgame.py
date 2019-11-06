# -*- coding: utf-8 -*-
"""
Contains various helper classes to simplify usage of pygame.

Attributes:
    tile_size (int): square size as taken from source .png for tiles
"""

import logging
import os
import sys
import pygame
import pygame.locals

tile_size = 32


class PygameHelper(object):
    """ Main bridge between the game and pygame library.

    Attributes:
        screen (pygame.display): main Surface to draw on
        font (pygame.font.Font): main font for displaying game text
        colors (dict): dictionary of color names to RGB tuples (0..255)
        dimensions (tuple): width & height of game map in cells (not pixels)
        tileset (list): list of Subsurfaces with tiles from .png image
        objects_on_map: group of Sprites having (x, y) coordinates on map
        visible_objects: group of Sprites that will be rendered
        units: list of Unit instances that have (x, y) coordinates on map
        highlight (pygame.Surface): color highlight to mark visible tiles

    """

    screen = None
    font = None
    colors = {}
    dimensions = ()
    tileset = []
    objects_on_map = pygame.sprite.LayeredUpdates()
    visible_objects = pygame.sprite.LayeredUpdates()
    units = pygame.sprite.Group()
    highlight = None

    def __init__(self):
        pygame.init()
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        self.dimensions = (48, 24)
        self.colors = {
            'BLACK': (0, 0, 0),
            'WHITE': (255, 255, 255)
        }
        self.screen = pygame.display.set_mode(
            (self.dimensions[0] * tile_size, self.dimensions[1] * tile_size))
        self.screen.fill(self.colors['BLACK'])
        basedir = os.path.dirname(os.path.abspath(__file__))
        self.load_tile_file(os.path.join(basedir, 'tiles.png'))
        ''' Since get_system_font() returns pygame's freesansbold.ttf and '''
        ''' pyinstaller can't seem to include this in the bundle, actual '''
        ''' system font needs to be called. Unfortunately system font sizes '''
        ''' are inconsistent. '''
        system_fonts = pygame.font.get_fonts()
        if 'lucida_console' in system_fonts or 'consolas' in system_fonts:
            self.font = pygame.font.SysFont('lucida_console, consolas',
                                            tile_size * 3 // 4)
        elif 'sourcecodepro' in system_fonts:
            self.font = pygame.font.SysFont('sourcecodepro', tile_size * 3 // 4)
        logging.info('Font letter size is {}.'.format(self.font.size('i')))
        self.highlight = pygame.Surface((32, 32), flags=pygame.SRCALPHA)
        self.highlight.fill((128, 128, 64, 32))

    def print_at(self,
                 x: int,
                 y: int,
                 item: str or pygame.Surface,
                 color: tuple = (255, 255, 255)):
        """ Blits item onto main screen surface.

        Args:
            x: map coord x where to put the item
            y: map coord y where to put the item
            item: text to render or existing Surface
            color: color of the text

        """
        if type(item) == str:
            item = self.font.render(item, True, color, self.colors['BLACK'])
        self.screen.blit(item, (x * tile_size, y * tile_size))

    def show_objects(self) -> None:
        """ Will blit all items from appropriate Sprite list onto the main
        surface.

        """
        container = self.visible_objects
        if 'debug' in sys.argv:
            container = self.objects_on_map
        container.draw(self.screen)

    def unit_at(self, where: tuple) -> pygame.sprite.Sprite or None:
        """ Loops through Units to find which is at supplied coordinates.
        Used for checking if space is occupied.

        Args:
            where: tuple of (x, y) with map coordinates

        Returns:
            First Unit (monster or player) at coordinates.

        """
        for unit in self.units:
            if unit.pos == where:
                return unit
        return None

    def refresh(self) -> None:
        """ Calls pygame display update and then resets visible_objects group.

        """
        pygame.display.update()
        self.visible_objects.empty()

    def close(self):
        """ Calls pygame cleanup & quit routine.

        """
        pygame.quit()

    def wait(self, character: pygame.key = None) -> pygame.key or bool:
        """ Freezes the game until a key is pressed.

        Args:
            character: (optional) wait only for this character
        Returns:
            key if no character was specified, True if expected key was pressed
        """
        pygame.event.clear()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                self.close()
            elif event.type == pygame.KEYDOWN:
                if character:
                    if event.key == character:
                        return True
                else:
                    return event.key

    def load_tile_file(self, filename):
        """
        Creates a list of Subsurfaces from single image with tiles.
        Args:
            filename: name of image with tiles
        """
        image = pygame.image.load(filename).convert_alpha()
        image_width, image_height = image.get_size()
        for tile_y in range(int(image_height / tile_size)):
            for tile_x in range(int(image_width / tile_size)):
                rect = (
                    tile_x * tile_size, tile_y * tile_size, tile_size,
                    tile_size)
                self.tileset.append(image.subsurface(rect))


class PygameWindow(pygame.Surface):
    """ Subwindow closable with 'q' key for short messages etc.

    Attributes:
        engine (PygameHelper): reference to invoking pygame helper object
        left (int): x position on main pygame screen Surface
        top (int): y position on main pygame screen Surface

    """
    engine = None
    left = 0
    top = 0

    def __init__(self, pgame, left=2, top=2, width=10, height=3,
                 title='Window title', title_color=(255, 255, 255),
                 bg_color=(0, 0, 0), border=True):
        super().__init__((width * tile_size, height * tile_size))
        self.engine = pgame
        self.left = left * tile_size
        self.top = top * tile_size
        self.fill(bg_color)
        self.print_at(1, 0, title, title_color)
        if border:
            pygame.draw.rect(self, title_color, self.get_rect(), 1)

    def loop(self, until: pygame.key = pygame.K_UNKNOWN):
        """ Will freeze game until a certain key is pressed

        Args:
            until: break only if this key is pressed

        """
        self.engine.screen.blit(self, (self.left, self.top))
        self.engine.refresh()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == until:
                    break

    def print_at(self,
                 x: int,
                 y: int,
                 item: str or pygame.Surface,
                 color: tuple = (255, 255, 255)):
        """ Blits text or image inside own coordinate space.

        Args:
            x: map coord x where to put the item
            y: map coord y where to put the item
            item: text to render or existing Surface
            color: color of the text
        """
        if type(item) == str:
            item = self.engine.font.render(item, True, color,
                                           self.engine.colors['BLACK'])
        self.blit(item, (x * tile_size, y * tile_size))

    def close(self):
        del self


class MapImage(pygame.Surface):
    """ Image for the known (discovered cells) map.

    This will grow having new cells added in the "look around" routine.

    """
    def __init__(self, w, h):
        super().__init__((w * tile_size, h * tile_size))

    def add(self, tile, coords):
        self.blit(tile, (coords[0] * tile_size, coords[1] * tile_size))

    def show(self, screen_surface):
        screen_surface.blit(self, (0, 0))
