# -*- coding: utf-8 -*-

from os import path
import tcod
import tcod.event
import mrogue.item
import mrogue.map
import mrogue.message
import mrogue.monster
import mrogue.player
import mrogue.timers


class Rogue(object):
    turn = 0
    num_objects = 10

    def __init__(self):
        font = tcod.tileset.load_tilesheet(
            path.join(mrogue.work_dir, 'terminal10x16_gs_ro.png'), 16, 16, tcod.tileset.CHARMAP_CP437)
        self.screen = mrogue.io.Screen(100, 40, font)
        self.dungeon = mrogue.map.Dungeon()
        self.items = mrogue.item.ItemManager()
        mrogue.monster.MonsterManager().create_monsters(self.num_objects, self.dungeon.depth())
        self.messenger = mrogue.message.Messenger()
        self.player = mrogue.player.Player()
        self.items.create_loot(self.num_objects)

    def update_dungeon(self):
        self.turn += 1
        mrogue.timers.Timer.update()
        while True:
            if mrogue.monster.MonsterManager().handle_monsters(self.player):
                break
        self.dungeon.look_around()
        return self.player.check_pulse(self.dungeon, self.messenger)

    def draw_dungeon(self):
        self.dungeon.draw_map()
        self.player.show_stats()
        self.messenger.show()
        self.screen.present()

    def handle_input(self, key):
        if mrogue.io.key_is(key, tcod.event.K_i):
            if self.items.show_inventory():
                return True
        elif mrogue.io.key_is(key, tcod.event.K_e):
            if self.items.show_equipment():
                return True
        elif mrogue.io.key_is(key, tcod.event.K_COMMA):
            if self.player.pickup_item(
                    self.items.get_item_on_map(self.player.pos)):
                return True
        elif mrogue.io.key_is(key, tcod.event.K_PERIOD, tcod.event.KMOD_SHIFT):
            if self.dungeon.descend(self.player.pos, self.num_objects):
                return True
        elif mrogue.io.key_is(key, tcod.event.K_COMMA, tcod.event.KMOD_SHIFT):
            if self.dungeon.ascend(self.player.pos):
                return True
        # elif key[0] in mrogue.io.directions and mrogue.io.mod_is(key[1], tcod.event.KMOD_SHIFT):
        #     if self.dungeon.automove(self.player.pos, key[0]):
        #         return True
        elif key[0] in mrogue.io.directions:
            if self.dungeon.movement(self.player, mrogue.io.direction_from(key[0], *self.player.pos)):
                return True
        elif mrogue.io.key_is(key, tcod.event.K_m, tcod.event.KMOD_SHIFT):
            self.messenger.message_screen()
        elif mrogue.io.key_is(key, tcod.event.K_h, tcod.event.KMOD_SHIFT):
            mrogue.io.help_screen()
        elif mrogue.io.key_is(key, tcod.event.K_q, tcod.event.KMOD_SHIFT):
            return True
        else:
            self.messenger.add(f"Unknown command: {'mod+' if key[1] else ''}{chr(key[0]) if key[0] < 256 else '<?>'}")
        return False

    def mainloop(self):
        key = (0, 0)
        while not mrogue.io.key_is(key, tcod.event.K_q, tcod.event.KMOD_SHIFT):
            if self.update_dungeon():
                break
            while True:
                self.draw_dungeon()
                key = mrogue.io.wait()
                self.messenger.clear()
                self.player.moved = False
                if self.handle_input(key):
                    break


if __name__ == '__main__':
    rogue = Rogue()
    try:
        rogue.mainloop()
    except Exception:
        raise
