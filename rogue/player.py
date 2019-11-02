# -*- coding: utf-8 -*-

import rogue.unit


class Player(rogue.unit.Unit):

    def __init__(self, game, ):
        super().__init__('Player', game, 1956, sight_range=6, to_hit=3, damage_dice='1d6+1', armor_class=14, current_hp=12)
        # equipment icons
        self.tile.blit(game.interface.tileset[2100], (0, 0))  # armor
        self.tile.blit(game.interface.tileset[2674], (0, 0))  # pants
        self.tile.blit(game.interface.tileset[2186], (0, 0))  # boots
        self.tile.blit(game.interface.tileset[2304], (0, 0))  # weapon

    def show(self):
        show = self.game.interface.print_at
        show(self.pos[0], self.pos[1], self.tile)
        self.game.interface.print_at(0, 0, 'HP:', self.game.interface.colors['WHITE'])
        self.game.interface.print_at(12, 0, 'AC:', self.game.interface.colors['WHITE'])
        self.game.interface.print_at(21, 0, 'ATK:', self.game.interface.colors['WHITE'])
        self.game.interface.print_at(2, 0, '%2d/%d' % (self.current_HP, self.max_HP), (0, 255, 0))
        self.game.interface.print_at(14, 0, '%2d' % self.armor_class, (0, 0, 255))
        self.game.interface.print_at(23, 0, '%d/%s' % (self.to_hit, self.damage_dice), (255, 0, 0))
