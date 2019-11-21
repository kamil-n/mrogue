# -*- coding: utf-8 -*-

import tcod.console
import mrogue.unit


class Player(mrogue.unit.Unit):
    def __init__(self, game):
        super().__init__('Player', game, ('@', 'lighter_red'), 6, 1, '1d2+1', 11, 20)
        self.status_bar = tcod.console.Console(game.screen.width, 1, 'F')
        self.add_item(game.items.item_templates['weapons']['maces'][0])
        self.add_item(game.items.item_templates['armor']['chest'][0])
        self.add_item(game.items.item_templates['armor']['feet'][0])
        for item in list(self.inventory):
            self.equip(item, quiet=True)
        self.add(game.level.objects_on_map, game.level.units)

    def show_stats(self):
        self.status_bar.clear()
        self.status_bar.print(0, 0, 'HP:')
        self.status_bar.print(3, 0, '%2d/%d' % (self.current_HP, self.max_HP),
                              tcod.color_lerp(
                                  tcod.red, tcod.green,
                                  self.current_HP / self.max_HP))
        self.status_bar.print(11, 0, 'AC:%2d' % self.armor_class)
        self.status_bar.print(19, 0, 'Atk:{:+d}/{}'.format(
            self.to_hit, self.damage_dice))
        self.status_bar.print(34, 0, 'Equipment: {}/4'.format(
            len(self.equipped)))
        self.status_bar.print(51, 0, 'Inventory: {}'.format(
            len(self.inventory)))
        self.status_bar.print(66, 0, 'Press q to quit, h for help.')
        self.status_bar.blit(self.game.screen, 0, 0)
        #? tcod.console_flush()

    def check_if_items_on_ground(self):
        items = self.game.items.get_item_on_map(self.pos)
        if items and self.moved:
            if len(items) > 1:
                self.game.messenger.add('{} items are lying here.'.format(
                    len(items)))
            else:
                self.game.messenger.add('{} is lying here.'.format(
                    items[0].full_name[0].upper() + items[0].full_name[1:]))
