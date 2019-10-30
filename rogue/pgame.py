# -*- coding: utf-8 -*-

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
        self.load_tile_file('tiles.png')
        self.font = pygame.font.SysFont(pygame.font.get_default_font(),
                                        tile_size)

    def print_at(self, x, y, item, color=(255, 255, 255)):
        if type(item) == str:
            item = self.font.render(item, True, color, self.colors['BLACK'])
        self.screen.blit(item, (x * tile_size, y * tile_size))

    def refresh(self):
        pygame.display.flip()

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
    under = None

    def __init__(self, pgame,
                 left=2 * tile_size,
                 top=2 * tile_size,
                 width=10 * tile_size,
                 height=3 * tile_size,
                 title='Window title',
                 title_color=(255, 255, 255),
                 bg_color=(0, 0, 0)):
        self.engine = pgame
        self.left = left
        self.top = top
        self.window = pygame.Surface((left + width, top + height))
        self.under = self.engine.screen.copy().subsurface(
            (left, top), (left+width, top+height))
        self.window.fill(bg_color)
        self.print_at(1, 1, title, title_color)

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
        self.engine.screen.blit(self.under, (self.left, self.top))