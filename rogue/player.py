# -*- coding: utf-8 -*-

import rogue.unit
from rogue.pgame import PygameWindow


class Player(rogue.unit.Unit):

    def __init__(self, game):
        super().__init__('Player', game, 1956, 6, 1, '1d2+1', 11, 12)
        self.window = PygameWindow(game.interface, 0, 0, game.interface.dimensions[0], 1)
        self.add_item(game.items.item_templates['weapons']['maces'][0])
        self.add_item(game.items.item_templates['armor']['chest'][0])
        self.add_item(game.items.item_templates['armor']['feet'][0])
        self.add((game.interface.objects_on_map, game.interface.units))

    def show_stats(self):
        self.window.clear()
        self.window.print_at(0, 0, 'HP', self.game.interface.colors['WHITE'])
        self.window.print_at(5, 0, 'AC', self.game.interface.colors['WHITE'])
        self.window.print_at(9, 0, 'Atk', self.game.interface.colors['WHITE'])
        self.window.print_at(1, 0, '%2d/%d' % (self.current_HP, self.max_HP), (0, 255, 0))
        self.window.print_at(6, 0, '%2d' % self.armor_class, (0, 0, 255))
        self.window.print_at(11, 0, '{:+d}/{}'.format(self.to_hit, self.damage_dice), (255, 0, 0))
        self.window.print_at(15, 0, 'Equipment(e): {}'.format(len(self.equipped)))
        self.window.print_at(25, 0, 'Inventory(u): {}'.format(len(self.inventory)))
        self.window.update()
