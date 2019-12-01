# -*- coding: utf-8 -*-

import tcod.console
import mrogue.unit

load_statuses = {
    'light': (1.2, tcod.green),
    'normal': (1.0, tcod.white),
    'heavy': (0.8, tcod.orange),
    'immobile': (0.0, tcod.red)
}

class Player(mrogue.unit.Unit):
    def __init__(self, game):
        super().__init__('Player', game, ('@', 'lighter_red'), 6, 1, '1d2+1', 11, 20)
        self.load_status = 'light'
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
        self.status_bar.print(32, 0, 'Load: {}'.format(self.load_status),
                              load_statuses[self.load_status][1])
        self.status_bar.print(66, 0, 'Press Q to quit, H for help.')
        self.status_bar.blit(self.game.screen, 0, 0)

    def heartbeat(self):
        items = self.game.items.get_item_on_map(self.pos)
        if items and self.moved:
            if len(items) > 1:
                self.game.messenger.add('{} items are lying here.'.format(
                    len(items)))
            else:
                self.game.messenger.add('{} is lying here.'.format(
                    items[0].name[0].upper() + items[0].name[1:]))
        total_load = sum([i.weight for i in self.inventory + self.equipped])
        if total_load < self.load_thresholds[0]:
            self.load_status = 'light'
        elif total_load < self.load_thresholds[1]:
            self.load_status = 'normal'
        elif total_load < self.load_thresholds[2]:
            self.load_status = 'heavy'
        else:
            self.load_status = 'immobile'
        self.speed = 1.0 * load_statuses[self.load_status][0]

    def in_slot(self, slot):
        for i in self.equipped:
            if i.slot == slot:
                return i
