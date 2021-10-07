# -*- coding: utf-8 -*-
"""Tools that extend Unit with custom features related to health regen, information bar on the screen, etc

Globals:
    * load_statuses - speed modifiers and colors related to encumbrance
Classes:
    * Player - customized Unit just for the player character
"""
from __future__ import annotations
from copy import copy
import sys
from typing import TYPE_CHECKING
import tcod.console
from tcod.path import Dijkstra
import mrogue.item_data
import mrogue.monster
import mrogue.unit
import mrogue.utils
if TYPE_CHECKING:
    from mrogue.item import Wearable, ItemManager
    from mrogue.map import Dungeon, Level
    from mrogue.message import Messenger

load_statuses = {
    'light': (0.8, tcod.green),
    'normal': (1.0, tcod.white),
    'heavy': (1.2, tcod.orange),
    'immobile': (0.0, tcod.red)
}


class Player(mrogue.unit.Unit):
    """Class description.

    Extends:
        * Player
    Class attributes:
        * _instance - Singleton instance
    Object attributes:
        * dijsktra_map - tcod.path.Dijsktra instance that follows Player
        * load_status - current load level (encumbrance)
        * identified_consumables - list of remember Consumables to be always identified
        * health_regen_cooldown - how many turns must pass before 1 HP is gained
        * crit_immunity - critical hit immunity based on amount of blessed items equipped
        * status_bar - tcod.console.Console for displaying Player stats on the screen
    Methods:
        * show_stats() - prints information on the status bar
        * regenerate_health() - slow health regeneration for a price
        * move() - recalculates pathfinding map
        * change_level() - things to do when ascending or descending a Level
        * update() - ambient information on each turn
        * burden_update() - applies encumbrance effects
        * in_slot() - what Item is held in a specific slot
        * check_pulse() - ends the game if Player's health points go below 0
        * pickup_item() - if there are multiple items, present the Item selection menu
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Player, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get(cls):
        return cls._instance

    def __init__(self):
        """Equip the player with a weapon and a piece of armor."""
        super().__init__('you', (0x263A, 'lighter_red'), 10, (10, 10, 10), [], 1.0, 2, (1, 2), 0, 20)
        self.background = tcod.green * 0.3
        self.player = True
        self.dijkstra_map = Dijkstra(mrogue.map.Dungeon.current_level.tiles['walkable'])
        self.dijkstra_map.set_goal(*self.pos)
        self.load_status = 'light'
        self.load_thresholds = tuple(threshold + self.abilities['str'].mod for threshold in self.load_thresholds)
        self.identified_consumables = []
        self.health_regen_cooldown = 0
        self.crit_immunity = 0.0
        self.status_bar = tcod.console.Console(mrogue.io.Screen.get().width, 1, 'F')
        self.add_item(mrogue.item.Item(mrogue.item_data.templates[4], 1, None))  # stick
        self.add_item(mrogue.item.Item(mrogue.item_data.templates[10], 1, None))  # tunic
        for freebie in list(self.inventory):
            self.equip(freebie, quiet=True)
        self.add(mrogue.map.Dungeon.current_level.objects_on_map, mrogue.map.Dungeon.current_level.units)

    def show_stats(self) -> None:
        """Puts basic information in the top line on the screen"""
        self.status_bar.clear()
        self.status_bar.print(0, 0, 'HP:')
        r, g, b = tcod.color_lerp(tcod.red, tcod.green, self.current_HP / self.max_HP)
        self.status_bar.print(3, 0, f'{self.current_HP:2d}/{self.max_HP}', (r, g, b))
        self.status_bar.print(11, 0, 'AC:%2d' % self.armor_class)
        self.status_bar.print(19, 0, f'Atk: {self.damage_dice[0]}-{self.damage_dice[1]}/{self.to_hit:+d}')
        self.status_bar.print(32, 0, f'Load: {self.load_status}', load_statuses[self.load_status][1])
        self.status_bar.print(47, 0, f'Depth: {mrogue.map.Dungeon.depth()}')
        self.status_bar.print(66, 0, 'Press Q to quit, H for help.')
        self.status_bar.blit(mrogue.io.Screen.get())

    def regenerate_health(self) -> None:
        """Add 1 HP every 35 turns and spawn a random Monster that will hunt the player"""
        self.health_regen_cooldown -= 1
        if self.health_regen_cooldown > 0:
            return
        if self.current_HP < self.max_HP:
            self.health_regen_cooldown = 35
            self.heal(1)
            mrogue.message.Messenger.add('You regenerate some health.')
            mrogue.monster.MonsterManager.spawn_monster(mrogue.map.Dungeon.depth(), sight_range=100)

    def move(self, success: bool = True) -> None:
        """Recalculate pathfinding map on each successful step"""
        super().move(success)
        if not success:
            if self.speed == 0.0:
                mrogue.message.Messenger.add('You are overburdened!')
            else:
                mrogue.message.Messenger.add('You shuffle in place.')
        else:
            self.dijkstra_map.set_goal(*self.pos)

    def change_level(self, level: Level) -> None:
        """Reset the pathfinding map when changing Levels

        :param level: the new Level of the Dungeon map
        """
        self.pos = level.pos
        self.dijkstra_map = Dijkstra(level.tiles['walkable'])
        self.dijkstra_map.set_goal(*self.pos)
        if self not in level.units:
            self.add(level.objects_on_map, level.units)

    def update(self) -> None:
        """Add ambient information after movement"""
        self.regenerate_health()
        if self.moved:
            items = mrogue.item.ItemManager.get_item_on_map(self.pos)
            if items:
                if len(items) > 1:
                    mrogue.message.Messenger.add('{} items are lying here.'.format(len(items)))
                else:
                    safe_cap = items[0].name[0].upper() + items[0].name[1:]
                    mrogue.message.Messenger.add(f'{safe_cap} is lying here.')
            tile = mrogue.map.Dungeon.current_level.tiles[self.pos]
            if tile == mrogue.map.compare['stairs_down']:
                mrogue.message.Messenger.add('There are stairs leading down here.')
            elif tile == mrogue.map.compare['stairs_up']:
                mrogue.message.Messenger.add('There are stairs leading up here.')
        super().update()

    def burden_update(self) -> None:
        """Adjust speed and display load information based on total weight of possessions"""
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

    def in_slot(self, slot: str):
        return mrogue.utils.find_in(self.equipped, 'slot', slot)

    def check_pulse(self, dungeon: Dungeon, messenger: Messenger) -> bool:
        """Show the game over screen if hit points go below

        :param dungeon: for refreshing the map view one last time
        :param messenger: for showing last messages outside of main game loop
        :return: True if player character died, False otherwise
        """
        if self.current_HP < 1 and 'debug' not in sys.argv:
            window = tcod.Console(20, 4, 'F')
            window.draw_frame(0, 0, 20, 4, 'Game over.', False)
            window.print_box(0, 2, 20, 1, 'YOU DIED', tcod.red, alignment=tcod.CENTER)
            dungeon.draw_map()
            self.show_stats()
            messenger.show()
            window.blit(mrogue.io.Screen.get(), 10, 10)
            mrogue.io.Screen.present()
            mrogue.io.wait(tcod.event.K_ESCAPE)
            return True
        return False

    def equip(self, item: Wearable, **kwargs) -> None:
        """Check if Item being equipped is blessed to increase critical hit immunity by 25%

        :param item: Item to be worn
        """
        super().equip(item, **kwargs)
        if item.enchantment_level > 0:
            self.crit_immunity += 0.25

    def unequip(self, item: Wearable, **kwargs) -> bool:
        """Check if Item being removed is blessed to decrease critical hit immunity by 25%

        :param item: Item to be removed
        """
        if super().unequip(item, **kwargs):
            if item.enchantment_level > 0:
                self.crit_immunity -= 0.25
            return True
        return False

    def pickup_item(self, item_manager: ItemManager) -> bool:
        """Pick an Item up if it's a single item, present pick-up choice list otherwise

        :param item_manager: ItemManager object for access to instance methods
        :return: True if Item(s) were picked up, False if there were no Items
        """
        item_list = item_manager.get_item_on_map(self.pos)
        if not item_list:
            msg = 'There are no items here.'
            mrogue.message.Messenger.add(msg)
            return False
        if len(item_list) > 1:
            chosen = item_manager.show_pickup_choice(item_list)
            if not chosen:
                return False
            if len(chosen) > 1:
                for item in chosen:
                    if issubclass(type(item), mrogue.item.Stackable):
                        existing_item = mrogue.utils.find_in(self.inventory, 'name', item.name)
                        if existing_item:
                            existing_item.amount += 1
                        else:
                            new_item = copy(item)
                            new_item.amount = 1
                            new_item.add(self.inventory)
                        if item.amount > 1:
                            item.amount -= 1
                        else:
                            item.picked()
                    else:
                        item.add(self.inventory)
                        item.picked()
                    msg = f'{self.name.capitalize()} picked up {item.name}.'
                    mrogue.message.Messenger.add(msg)
                self.burden_update()
                return True
            else:
                return super().pickup_item(chosen)
        else:
            return super().pickup_item(item_list)
