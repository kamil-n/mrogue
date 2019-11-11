# -*- coding: utf-8 -*-
import logging
import os
import sys
import pygame
import pygame.locals
from rogue import __version__

tile_size = 32


class PygameHelper(object):
    objects_on_map = pygame.sprite.LayeredUpdates(default_layer=3)
    visible_objects = pygame.sprite.LayeredUpdates(default_layer=3)
    units = pygame.sprite.Group()

    def __init__(self):
        self.log = logging.getLogger(__name__)
        pygame.init()
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        self.dimensions = (48, 24)
        self.colors = {
            'BLACK': (0, 0, 0),
            'WHITE': (255, 255, 255)
        }
        self.tileset = []
        self.screen = pygame.display.set_mode((self.dimensions[0] * tile_size, self.dimensions[1] * tile_size))
        pygame.display.set_caption('Rogue ' + __version__)
        self.screen.fill(self.colors['BLACK'])
        basedir = os.path.dirname(os.path.abspath(__file__))
        self.load_tile_file(os.path.join(basedir, 'tiles.png'))
        ''' Since get_system_font() returns pygame's freesansbold.ttf and '''
        ''' pyinstaller can't seem to include this in the bundle, actual '''
        ''' system font needs to be called. Unfortunately system font sizes '''
        ''' are inconsistent. '''
        self.font = None
        system_fonts = pygame.font.get_fonts()
        if 'lucida_console' in system_fonts or 'consolas' in system_fonts:
            self.font = pygame.font.SysFont('lucida_console, consolas', tile_size * 3 // 4)
        elif 'sourcecodepro' in system_fonts:
            self.font = pygame.font.SysFont('sourcecodepro', tile_size * 3 // 4)
        self.log.debug('Font letter size is {}.'.format(self.font.size('i')))
        self.highlight = pygame.Surface((32, 32), flags=pygame.SRCALPHA)
        self.highlight.fill((128, 128, 64, 32))

    def print_at(self, x: int, y: int, item: str or pygame.Surface, color: tuple = (255, 255, 255)):
        if type(item) == str:
            item = self.font.render(item, True, color, self.colors['BLACK'])
        self.screen.blit(item, (x * tile_size, y * tile_size))

    def show_objects(self) -> None:
        container = self.visible_objects
        if 'debug' in sys.argv:
            container = self.objects_on_map
        container.draw(self.screen)

    def update_objects(self):
        self.objects_on_map.update()

    def unit_at(self, where: tuple) -> pygame.sprite.Sprite or None:
        for unit in self.units:
            if unit.pos == where:
                return unit
        return None

    def refresh(self) -> None:
        pygame.display.update()
        self.visible_objects.empty()

    def close(self):
        pygame.quit()

    def wait(self, character: pygame.key = None) -> pygame.key or bool:
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


class PygameWindow(pygame.Surface):
    engine = None

    def __init__(self, pgame, left=2, top=2, width=10, height=3, title=None, title_color=(255, 255, 255),
                 bg_color=(0, 0, 0), border=True):
        super().__init__((width * tile_size, height * tile_size))
        self.engine = pgame
        self.left = left * tile_size
        self.top = top * tile_size
        self.bg_color = bg_color
        self.title_color = title_color
        self.fill(self.bg_color)
        if title:
            self.print_at(1, 0, title, title_color)
        self.border = border
        if border:
            pygame.draw.rect(self, title_color, self.get_rect(), 1)

    def update(self):
        self.engine.screen.blit(self, (self.left, self.top))
        # self.engine.refresh()
        pygame.display.update()

    def loop(self, until: pygame.key = pygame.K_UNKNOWN):
        self.engine.screen.blit(self, (self.left, self.top))
        # self.engine.refresh()
        pygame.display.update()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == until:
                    break

    def print_at(self,  x: int, y: int, item: str or pygame.Surface, color: tuple = (255, 255, 255)):
        if type(item) == str:
            item = self.engine.font.render(item, True, color, self.engine.colors['BLACK'])
        self.blit(item, (x * tile_size, y * tile_size))

    def clear(self):
        self.fill(self.bg_color)
        if self.border:
            pygame.draw.rect(self, self.title_color, self.get_rect(), 1)

    def close(self):
        del self


class PygameDialog(pygame.Surface):
    def __init__(self, engine, prompt, options):
        self.engine = engine
        super().__init__((16 * tile_size, (1 + len(options)) * tile_size))
        self.fill((0, 0, 0))
        text = engine.font.render('{} (Esc to cancel)'.format(prompt), True, engine.colors['WHITE'])
        self.blit(text, (0, 0))
        pygame.draw.rect(self, (255, 255, 255), self.get_rect(), 1)
        i = 0
        for key, description in options:
            text = engine.font.render('{}) {}'.format(chr(key), description), True, engine.colors['WHITE'])
            self.blit(text, (1 * tile_size, (1 + i) * tile_size))
            i += 1
        engine.screen.blit(self, (14 * tile_size, 12 * tile_size))
        pygame.display.update()
        self.keys = [option[0] for option in options]

    def loop(self):
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == 27:
                    return False
                if event.key in self.keys:
                    return event.key


class MapImage(pygame.Surface):
    def __init__(self, w, h):
        super().__init__((w * tile_size, h * tile_size))

    def add(self, tile, coords):
        self.blit(tile, (coords[0] * tile_size, coords[1] * tile_size))

    def show(self, screen_surface):
        screen_surface.blit(self, (0, 0))
