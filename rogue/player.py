# -*- coding: utf-8 -*-

import rogue.unit


class Player(rogue.unit.Unit):

    def __init__(self, game):
        super().__init__('Player', game, 1956, 6, 1, '1d2+1', 11, 12)

        # self.image.blit(game.interface.tileset[2674], (0, 0))  # pants
        # self.image.blit(game.interface.tileset[2186], (0, 0))  # boots
        # TODO: should starting equipment be added in constructor?
        self.add((game.interface.objects_on_map, game.interface.units))

    def show_stats(self):
        show = self.game.interface.print_at
        show(0, 0, 'HP', self.game.interface.colors['WHITE'])
        show(5, 0, 'AC', self.game.interface.colors['WHITE'])
        show(9, 0, 'Atk', self.game.interface.colors['WHITE'])
        show(1, 0, '%2d/%d' % (self.current_HP, self.max_HP), (0, 255, 0))
        show(6, 0, '%2d' % self.armor_class, (0, 0, 255))
        show(11, 0, '{:+d}/{}'.format(self.to_hit, self.damage_dice), (255, 0, 0))
        show(15, 0, 'Equipment(e): {}'.format(len(self.equipped)))
        show(25, 0, 'Inventory(u): {}'.format(len(self.inventory)))
