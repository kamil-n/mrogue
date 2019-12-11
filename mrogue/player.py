# -*- coding: utf-8 -*-

import tcod.console
from tcod.path import Dijkstra
import mrogue.unit
from mrogue.item import Weapon, Armor
from mrogue.map import tileset

load_statuses = {
    'light': (0.8, tcod.green),
    'normal': (1.0, tcod.white),
    'heavy': (1.2, tcod.orange),
    'immobile': (0.0, tcod.red)
}


class Player(mrogue.unit.Unit):
    def __init__(self, game):
        super().__init__('Player', game, ('@', 'lighter_red'),
                         6, 1.0, 1, '1d2+1', 11, 20)
        self.dijsktra_map = Dijkstra(game.dungeon.level.walkable)
        self.dijsktra_map.set_goal(*self.pos)
        self.load_status = 'light'
        self.identified_consumables = []
        self.status_bar = tcod.console.Console(game.screen.width, 1, 'F')
        self.add_item(Weapon(game.items,
                             game.items.templates_file['weapons']['maces'][0],
                             None))
        self.add_item(Armor(game.items,
                            game.items.templates_file['armor']['chest'][0],
                            None))
        for item in list(self.inventory):
            self.equip(item, quiet=True)
        self.add(game.dungeon.level.objects_on_map, game.dungeon.level.units)

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
        self.status_bar.print(32, 0, 'Load: {}'.format(
            self.load_status), load_statuses[self.load_status][1])
        self.status_bar.print(47, 0, 'Depth: {}'.format(
            self.game.dungeon.depth))
        self.status_bar.print(66, 0, 'Press Q to quit, H for help.')
        self.status_bar.blit(self.game.screen)

    def regenerate_health(self):
        self.health_regen_cooldown -= 1
        if self.health_regen_cooldown > 0:
            return
        if self.current_HP < self.max_HP:
            self.health_regen_cooldown = 35
            self.heal(1)
            self.game.monsters.create_monsters(1, sight_range=100)

    def move(self, success=True):
        super().move(success)
        if not success:
            if self.speed == 0.0:
                self.game.messenger.add('You are overburdened!')
            else:
                self.game.messenger.add('You shuffle in place.')
        else:
            self.dijsktra_map.set_goal(*self.pos)

    def change_level(self, level):
        self.pos = level.pos
        self.dijsktra_map = Dijkstra(level.walkable)
        self.dijsktra_map.set_goal(*self.pos)
        if self not in level.units:
            self.add(level.objects_on_map, level.units)

    def update(self):
        super().update()
        items = self.game.items.get_item_on_map(self.pos)
        if items and self.moved:
            if len(items) > 1:
                self.game.messenger.add('{} items are lying here.'.format(
                    len(items)))
            else:
                self.game.messenger.add('{} is lying here.'.format(
                    items[0].name[0].upper() + items[0].name[1:]))
        if self.game.level.tiles[self.pos[0]][self.pos[1]] == tileset['stairs_down'] and self.moved:
            self.game.messenger.add('There are stairs leading down here.')
        elif self.game.level.tiles[self.pos[0]][self.pos[1]] == tileset['stairs_up'] and self.moved:
            self.game.messenger.add('There are stairs leading up here.')
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
