# -*- coding: utf-8 -*-

import rogue.unit


class Player(rogue.unit.Unit):

    def __init__(self, game):
        super().__init__('Player', game, 1956, 6, 3, '1d6+1', 14, 12)
        # equipment icons
        self.image.blit(game.interface.tileset[2100], (0, 0))  # armor
        self.image.blit(game.interface.tileset[2674], (0, 0))  # pants
        self.image.blit(game.interface.tileset[2186], (0, 0))  # boots
        self.image.blit(game.interface.tileset[2304], (0, 0))  # weapon
        self.add((game.interface.objects_on_map, game.interface.units))

    def show_stats(self):
        show = self.game.interface.print_at
        show(0, 0, 'HP:', self.game.interface.colors['WHITE'])
        show(12, 0, 'AC:', self.game.interface.colors['WHITE'])
        show(21, 0, 'ATK:', self.game.interface.colors['WHITE'])
        show(2, 0, '%2d/%d' % (self.current_HP, self.max_HP), (0, 255, 0))
        show(14, 0, '%2d' % self.armor_class, (0, 0, 255))
        show(23, 0, '%d/%s' % (self.to_hit, self.damage_dice), (255, 0, 0))
