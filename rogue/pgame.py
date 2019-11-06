# -*- coding: utf-8 -*-

import os
import sys
import pygame
import pygame.locals

tile_size = 32


class PygameHelper(object):
    screen = None
    font = None
    colors = {}
    dimensions = ()
    resolution = ()
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

    def print_at(self, x, y, item, color=(255, 255, 255)):
        if type(item) == str:
            item = self.font.render(item, True, color, self.colors['BLACK'])
        self.screen.blit(item, (x * tile_size, y * tile_size))

    def show_objects(self):
        container = self.visible_objects
        if 'debug' in sys.argv:
            container = self.objects_on_map
        container.draw(self.screen)

    def unit_at(self, where):
        for unit in self.units:
            if unit.pos == where:
                return unit
        return None

    def refresh(self):
        pygame.display.update()
        self.visible_objects.empty()

    def close(self):
        pygame.quit()

    def wait(self, character=None):
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
        image = pygame.image.load(filename).convert_alpha()
        image_width, image_height = image.get_size()
        for tile_y in range(int(image_height / tile_size)):
            for tile_x in range(int(image_width / tile_size)):
                rect = (
                    tile_x * tile_size, tile_y * tile_size, tile_size,
                    tile_size)
                self.tileset.append(image.subsurface(rect))


class PygameWindow(object):
    window = None
    engine = None
    left = 0
    top = 0
    width = 0
    height = 0

    def __init__(self, pgame, left=2, top=2, width=10, height=3,
                 title='Window title', title_color=(255, 255, 255),
                 bg_color=(0, 0, 0), border=True):
        self.engine = pgame
        self.left = left * tile_size
        self.top = top * tile_size
        self.width = width * tile_size
        self.height = height * tile_size
        self.window = pygame.Surface((self.width, self.height))
        self.window.fill(bg_color)
        self.print_at(1, 0, title, title_color)
        if border:
            pygame.draw.rect(self.window, title_color, self.window.get_rect(), 1)

    def loop(self, until=pygame.K_UNKNOWN):
        self.engine.screen.blit(self.window, (self.left, self.top))
        self.engine.refresh()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == until:
                    break

    def print_at(self, x, y, item, color=(255, 255, 255)):
        if type(item) == str:
            item = self.engine.font.render(item, True, color,
                                           self.engine.colors['BLACK'])
        self.window.blit(item, (x * tile_size, y * tile_size))

    def close(self):
        del self.window


class MapImage(object):
    surf = None

    def __init__(self, w, h):
        self.surf = pygame.Surface((w * tile_size, h * tile_size))

    def add(self, tile, coords):
        self.surf.blit(tile, (coords[0] * tile_size, coords[1] * tile_size))

    def show(self, screen_surface):
        screen_surface.blit(self.surf, (0, 0))
