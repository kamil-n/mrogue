# -*- coding: utf-8 -*-
# Copyright (C) 2018-2021 Kamil Nienałtowski
# License: GPL-3.0-or-later
from os import path

import tcod
import tcod.event

import mrogue.item.manager
import mrogue.map
import mrogue.message
import mrogue.monster
import mrogue.player
import mrogue.timers
import mrogue.utils


class Rogue:
    turn = 0
    num_objects = 10

    def __init__(self) -> None:
        self.fonts = mrogue.utils.circular(
            [
                ("terminal10x16_gs_ro.png", (10, 16)),
                ("Bedstead-20-df.png", (12, 20)),
                ("Cooz_curses_14x16.png", (14, 16)),
                ("Bmac_smooth_16x24.png", (16, 24)),
                ("Cheepicus_12x12.png", (12, 12)),
                ("16x16_sb_ascii.png", (16, 16)),
                ("Haowan_Curses_1440x450.png", (18, 18)),
                ("Nagidal24x24shade.png", (24, 24)),
                ("Curses_square_24.png", (24, 24)),
            ]
        )
        font = tcod.tileset.load_tilesheet(
            path.join(mrogue.work_dir, "data", next(self.fonts)[0]),
            16,
            16,
            tcod.tileset.CHARMAP_CP437,
        )
        mrogue.io.Screen(100, 40, font)
        self.dungeon = mrogue.map.Dungeon()
        self.items = mrogue.item.manager.ItemManager()
        mrogue.monster.MonsterManager().create_monsters(
            self.num_objects, self.dungeon.depth()
        )
        self.messenger = mrogue.message.Messenger()
        self.player = mrogue.player.Player()
        self.items.create_loot(self.num_objects)

    def update_dungeon(self) -> bool:
        self.turn += 1
        mrogue.timers.Timer.update()
        if self.turn > 1:  # so that the player has first move
            mrogue.monster.MonsterManager().handle_monsters(self.player)
        self.dungeon.look_around()
        return self.player.check_pulse(self.dungeon, self.messenger)

    def draw_dungeon(self) -> None:
        self.dungeon.draw_map()
        self.player.show_stats()
        self.messenger.show()
        mrogue.io.Screen.present()

    def handle_input(self, key: tuple[int, int]) -> bool:
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
            if self.player.pickup(self.items):
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
        elif key[0] in mrogue.io.directions and mrogue.io.mod_is(
            key[1], tcod.event.KMOD_SHIFT
        ):
            if self.dungeon.automove(
                self.player.pos, key[0], self.draw_dungeon, self.update_dungeon
            ):
                return True
        # number keys|arrows|numpad keys
        elif key[0] in mrogue.io.directions:
            if self.dungeon.movement(
                self.player, mrogue.io.direction_from(key[0], self.player.pos)
            ):
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
        # Ctrl + R
        elif mrogue.io.key_is(key, tcod.event.K_r, tcod.event.KMOD_CTRL):
            mrogue.io.Screen.change_font(new_font := next(self.fonts))
            self.messenger.add(f"Changed font to {new_font[0]}.")
        # other
        else:
            self.messenger.add("Unknown command.")
        return False

    def mainloop(self) -> None:
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


if __name__ == "__main__":
    rogue = Rogue()
    try:
        rogue.mainloop()
    except Exception:
        raise
