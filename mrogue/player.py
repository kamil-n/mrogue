# -*- coding: utf-8 -*-

import tcod.console
from tcod.path import Dijkstra
import mrogue.item
import mrogue.item_data
import mrogue.map
import mrogue.unit
import mrogue.utils

load_statuses = {
    'light': (0.8, tcod.green),
    'normal': (1.0, tcod.white),
    'heavy': (1.2, tcod.orange),
    'immobile': (0.0, tcod.red)
}


class Player(mrogue.unit.Unit):
    def __init__(self, game):
        super().__init__('Hero', game, (chr(0x263A), 'lighter_red'), 10, (10, 10, 10), [], 1.0, 2, '1d2', 0, 20)
        self.player = True
        self.dijsktra_map = Dijkstra(game.dungeon.level.walkable)
        self.dijsktra_map.set_goal(*self.pos)
        self.load_status = 'light'
        self.load_thresholds = tuple(threshold + self.abilities['str'].mod for threshold in self.load_thresholds)
        self.identified_consumables = []
        self.health_regen_cooldown = 0
        self.status_bar = tcod.console.Console(game.screen.width, 1, 'F')
        self.add_item(mrogue.item.Weapon(game.items, mrogue.item_data.templates[5], None))  # mace
        self.add_item(mrogue.item.Armor(game.items, mrogue.item_data.templates[10], None))  # tunic
        for freebie in list(self.inventory):
            self.equip(freebie, quiet=True)
        self.add(game.dungeon.level.objects_on_map, game.dungeon.level.units)

    def show_stats(self):
        self.status_bar.clear()
        self.status_bar.print(0, 0, 'HP:')
        r, g, b = tcod.color_lerp(tcod.red, tcod.green, self.current_HP / self.max_HP)
        self.status_bar.print(3, 0, f'{self.current_HP:2d}/{self.max_HP}', (r, g, b))
        self.status_bar.print(11, 0, 'AC:%2d' % self.armor_class)
        self.status_bar.print(19, 0, f'Atk:{self.to_hit:+d}/{self.damage_dice}')
        self.status_bar.print(32, 0, f'Load: {self.load_status}', load_statuses[self.load_status][1])
        self.status_bar.print(47, 0, f'Depth: {self.game.dungeon.depth}')
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
        self.regenerate_health()
        if self.moved:
            items = self.game.items.get_item_on_map(self.pos)
            if items:
                if len(items) > 1:
                    self.game.messenger.add('{} items are lying here.'.format(
                        len(items)))
                else:
                    self.game.messenger.add(f'{mrogue.cap(items[0].name)} is lying here.')
            tile = self.game.dungeon.level.tiles[self.pos[0]][self.pos[1]]
            if tile == mrogue.map.tiles['stairs_down']:
                self.game.messenger.add('There are stairs leading down here.')
            elif tile == mrogue.map.tiles['stairs_up']:
                self.game.messenger.add('There are stairs leading up here.')

    def burden_update(self):
        super().burden_update()
        total_load = sum([i.weight for i in self.inventory + self.equipped])
        if total_load < self.load_thresholds[0]:
            self.load_status = 'light'
        elif total_load < self.load_thresholds[1]:
            self.load_status = 'normal'
        elif total_load < self.load_thresholds[2]:
            self.load_status = 'heavy'
        else:
            self.load_status = 'immobile'
        self.speed = load_statuses[self.load_status][0] - self.abilities['dex'].mod / 100

    def in_slot(self, slot):
        mrogue.utils.find_in(self.equipped, 'slot', slot)
