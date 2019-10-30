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
        self.dimensions = (48, 24)
        self.colors = {
            'BLACK': (0, 0, 0),
            'WHITE': (255, 255, 255)
        }
        self.screen = pygame.display.set_mode(
            (self.dimensions[0] * tile_size, self.dimensions[1] * tile_size))
        self.screen.fill(self.colors['BLACK'])
        self.load_tile_file('tiles.png')
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), tile_size)

    def print_at(self, x, y, item, color=(255, 255, 255), window=None):
        if not window:
            window = self.screen
        if type(item) == str:
            item = self.font.render(item, True, color, self.colors['BLACK'])   # item, alias, fg_color, bg_color
        window.blit(item, (x * tile_size, y * tile_size))

    def refresh(self):
        pygame.display.flip()

    def close(self):
        pygame.quit()

    def wait(self, character=pygame.K_UNKNOWN):
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    break

    def load_tile_file(self, filename):
        image = pygame.image.load(filename).convert()
        image_width, image_height = image.get_size()
        tile_size = 32
        for tile_y in range(int(image_height / tile_size)):
            for tile_x in range(int(image_width / tile_size)):
                rect = (
                    tile_x * tile_size, tile_y * tile_size, tile_size,
                    tile_size)
                self.tileset.append(image.subsurface(rect))


class PygameWindow(object):
    window = None

    def __init__(self, pgame,
                 left=1 * tile_size,
                 top=1 * tile_size,
                 width=20 * tile_size,
                 height=4 * tile_size,
                 title='Window title',
                 title_color=(0, 0, 0),
                 bg_color=(255, 255, 255)):
        self.window = pygame.Surface((left + width, top + height))
        pgame.print_at(1, 2, title, pgame.colors['WHITE'], self.window)
        pgame.screen.blit(self.window, (left, top))

    def loop(self, until=pygame.K_UNKNOWN):
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key == until:
                    break

    def close(self):
        del self.window
