# -*- coding: utf-8 -*-

import sys
import tcod.console
from tcod.path import Dijkstra
import mrogue.io
import mrogue.item
import mrogue.item_data
import mrogue.map
import mrogue.message
import mrogue.monster
import mrogue.unit
import mrogue.utils

load_statuses = {
    'light': (0.8, tcod.green),
    'normal': (1.0, tcod.white),
    'heavy': (1.2, tcod.orange),
    'immobile': (0.0, tcod.red)
}


class Player(mrogue.unit.Unit):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Player, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get(cls):
        return cls._instance

    def __init__(self):
        super().__init__('Hero', (chr(0x263A), 'lighter_red'), 10, (10, 10, 10), [], 1.0, 2, '1d2', 0, 20)
        self.player = True
        self.dijsktra_map = Dijkstra(mrogue.map.Dungeon.current_level.walkable)
        self.dijsktra_map.set_goal(*self.pos)
        self.load_status = 'light'
        self.load_thresholds = tuple(threshold + self.abilities['str'].mod for threshold in self.load_thresholds)
        self.identified_consumables = []
        self.health_regen_cooldown = 0
        self.status_bar = tcod.console.Console(mrogue.io.Screen.get().width, 1, 'F')
        self.add_item(mrogue.item.Wearable(mrogue.item_data.templates[5], None))  # mace
        self.add_item(mrogue.item.Wearable(mrogue.item_data.templates[10], None))  # tunic
        for freebie in list(self.inventory):
            self.equip(freebie, quiet=True)
        self.add(mrogue.map.Dungeon.current_level.objects_on_map, mrogue.map.Dungeon.current_level.units)

    def show_stats(self):
        self.status_bar.clear()
        self.status_bar.print(0, 0, 'HP:')
        r, g, b = tcod.color_lerp(tcod.red, tcod.green, self.current_HP / self.max_HP)
        self.status_bar.print(3, 0, f'{self.current_HP:2d}/{self.max_HP}', (r, g, b))
        self.status_bar.print(11, 0, 'AC:%2d' % self.armor_class)
        self.status_bar.print(19, 0, f'Atk:{self.to_hit:+d}/{self.damage_dice}')
        self.status_bar.print(32, 0, f'Load: {self.load_status}', load_statuses[self.load_status][1])
        self.status_bar.print(47, 0, f'Depth: {mrogue.map.Dungeon.depth()}')
        self.status_bar.print(66, 0, 'Press Q to quit, H for help.')
        self.status_bar.blit(mrogue.io.Screen.get())

    def regenerate_health(self):
        self.health_regen_cooldown -= 1
        if self.health_regen_cooldown > 0:
            return
        if self.current_HP < self.max_HP:
            self.health_regen_cooldown = 35
            self.heal(1)
            mrogue.monster.MonsterManager.create_monsters(1, mrogue.map.Dungeon.depth(), sight_range=100)

    def move(self, success=True):
        super().move(success)
        if not success:
            if self.speed == 0.0:
                mrogue.message.Messenger.add('You are overburdened!')
            else:
                mrogue.message.Messenger.add('You shuffle in place.')
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
            items = mrogue.item.ItemManager.get_item_on_map(self.pos)
            if items:
                if len(items) > 1:
                    mrogue.message.Messenger.add('{} items are lying here.'.format(len(items)))
                else:
                    safe_cap = items[0].name[0].upper() + items[0].name[1:]
                    mrogue.message.Messenger.add(f'{safe_cap} is lying here.')
            tile = mrogue.map.Dungeon.current_level.tiles[self.pos[0]][self.pos[1]]
            if tile == mrogue.map.tiles['stairs_down']:
                mrogue.message.Messenger.add('There are stairs leading down here.')
            elif tile == mrogue.map.tiles['stairs_up']:
                mrogue.message.Messenger.add('There are stairs leading up here.')

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

    def check_pulse(self, dungeon, messenger):
        if self.current_HP < 1 and 'debug' not in sys.argv:
            window = tcod.Console(20, 4, 'F')
            window.draw_frame(0, 0, 20, 4, 'Game over.', False)
            window.print(6, 2, 'YOU DIED', tcod.red)
            dungeon.draw_map()
            self.show_stats()
            messenger.show()
            window.blit(mrogue.io.Screen.get(), 10, 10)
            mrogue.io.Screen.present()
            mrogue.io.wait(tcod.event.K_ESCAPE)
            return True
        return False
