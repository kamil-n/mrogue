# -*- coding: utf-8 -*-
# Copyright (C) 2018-2021 Kamil Nienałtowski
# License: GPL-3.0-or-later
from os import path
import tcod
import tcod.event
import mrogue.item
import mrogue.map
import mrogue.message
import mrogue.monster
import mrogue.player
import mrogue.timers


class Rogue:
    """Main class representing the game.

    Attributes:
        * turn - keeps track of the passage of time
        * num_objects - how many items and how many monsters are initially spawned on each level

    Methods:
        * update_dungeon() - performs monsters' actions and updates the environment
        * draw_dungeon() - renders the dungeons and prints vital information and feedback
        * handle_input() - lists all the keys used by the game and corresponding actions
        * mainloop() - updates/draws the environment and waits for player input
    """

    turn = 0
    num_objects = 10

    def __init__(self):
        """Initialize the libTCOD terminal and some singletons and managers."""
        font = tcod.tileset.load_tilesheet(
            path.join(mrogue.work_dir, 'terminal10x16_gs_ro.png'), 16, 16, tcod.tileset.CHARMAP_CP437)
        mrogue.io.Screen(100, 40, font)
        self.dungeon = mrogue.map.Dungeon()
        self.items = mrogue.item.ItemManager()
        mrogue.monster.MonsterManager().create_monsters(self.num_objects, self.dungeon.depth())
        self.messenger = mrogue.message.Messenger()
        self.player = mrogue.player.Player()
        self.items.create_loot(self.num_objects)

    def update_dungeon(self) -> bool:
        """Perform everything that happens between player inputs (moves monsters, recalculates FoV, etc)

        :return: False if player is alive and True if they were killed during monsters' turn
        """
        self.turn += 1
        mrogue.timers.Timer.update()
        mrogue.monster.MonsterManager().handle_monsters(self.player)
        self.dungeon.look_around()
        return self.player.check_pulse(self.dungeon, self.messenger)

    def draw_dungeon(self) -> None:
        """Render the dungeon, player stats panel and message line, update the screen"""
        self.dungeon.draw_map()
        self.player.show_stats()
        self.messenger.show()
        mrogue.io.Screen.present()

    def handle_input(self, key: tuple[tcod.event.KeyDown, tcod.event.Modifier]) -> bool:
        """Determine if the game can perform a non-blocking action (that ends player's turn)

        :param key: a tuple consisting of the pressed key along with a held modifier key
        :return: False if player can still perform an action, True if control should be returned to the mainloop
        """
        # 'i'
        if mrogue.io.key_is(key, tcod.event.K_i):
            if self.items.show_inventory():
                return True
        # 'e'
        elif mrogue.io.key_is(key, tcod.event.K_e):
            if self.items.show_equipment():
                return True
        # ','
        elif mrogue.io.key_is(key, tcod.event.K_COMMA):
            if self.player.pickup_item(
                    self.items.get_item_on_map(self.player.pos)):
                return True
        # '>'
        elif mrogue.io.key_is(key, tcod.event.K_PERIOD, tcod.event.KMOD_SHIFT):
            if self.dungeon.descend(self.player.pos, self.num_objects):
                return True
        # '<'
        elif mrogue.io.key_is(key, tcod.event.K_COMMA, tcod.event.KMOD_SHIFT):
            if self.dungeon.ascend(self.player.pos):
                return True
        # Shift + [number keys|arrows|numpad keys]
        elif key[0] in mrogue.io.directions and mrogue.io.mod_is(key[1], tcod.event.KMOD_SHIFT):
            if self.dungeon.automove(self.player.pos, key[0], self.draw_dungeon, self.update_dungeon):
                return True
        # number keys|arrows|numpad keys
        elif key[0] in mrogue.io.directions:
            if self.dungeon.movement(self.player, mrogue.io.direction_from(key[0], self.player.pos)):
                return True
        # 'M'
        elif mrogue.io.key_is(key, tcod.event.K_m, tcod.event.KMOD_SHIFT):
            self.messenger.message_screen()
        # 'H'
        elif mrogue.io.key_is(key, tcod.event.K_h, tcod.event.KMOD_SHIFT):
            mrogue.io.help_screen()
        # 'Q'
        elif mrogue.io.key_is(key, tcod.event.K_q, tcod.event.KMOD_SHIFT):
            return True
        # other
        else:
            self.messenger.add(f'Unknown command.')
        return False

    def mainloop(self) -> None:
        """Update the dungeon state, render it, wait for keypress, perform related action, exit if Q was pressed"""
        key = (0, 0)
        while not mrogue.io.key_is(key, tcod.event.K_q, tcod.event.KMOD_SHIFT):
            if self.update_dungeon():
                break
            while True:
                self.draw_dungeon()
                key = mrogue.io.wait()
                self.messenger.clear()
                if self.handle_input(key):
                    break


if __name__ == '__main__':
    rogue = Rogue()
    try:
        rogue.mainloop()
    except Exception:
        raise
