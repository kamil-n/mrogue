# -*- coding: utf-8 -*-
""""Module providing on-use effect implementation for consumables, spells, etc.

Classes:
    * Effect - an action or change of state to be triggered
"""
import string

import tcod

import mrogue.item
import mrogue.message
import mrogue.timers
import mrogue.unit
import mrogue.utils


def select_item_from_list(
    items: list[mrogue.item.item.Wearable], action: str
) -> mrogue.item.item.Wearable or False:
    screen = mrogue.io.Screen.get()
    total = len(items)
    w, limit, scroll = mrogue.item.item.Item.max_name + 9, 6, 0
    h = 2 + min(limit, total)
    window = tcod.Console(w, h, "F")
    window.draw_frame(0, 0, window.width, window.height)
    while True:
        window.clear()
        window.draw_frame(0, 0, w, h, decoration="╔═╗║ ║╚═╝")
        window.print_box(
            0, 0, w, 1, f" Select an item to {action}: ", alignment=tcod.CENTER
        )
        if scroll > 0:
            window.print(1, 1, chr(0x2191), tcod.black, tcod.white)
        for i in range(len(items)):
            if i > limit - 1:
                break
            it = items[i + scroll]
            window.print(2, i + 1, f"{string.ascii_letters[i + scroll]}) ")
            window.print(5, i + 1, chr(it.icon), it.color)
            window.print(7, i + 1, *it.interface_name)
        if limit + scroll < len(items):
            window.print(1, limit, chr(0x2193), tcod.black, tcod.white)
        window.blit(screen, 16, 6)
        screen.present()
        key = mrogue.io.wait()
        if key[1] & mrogue.io.ignore_mods == mrogue.io.ignore_mods:
            key = (key[0], key[1] - mrogue.io.ignore_mods)
        if mrogue.io.key_is(key, tcod.event.K_ESCAPE):
            return False
        elif key[0] in range(97, 97 + total):
            return items[key[0] - 97]
        elif mrogue.io.key_is(key, tcod.event.K_DOWN):
            scroll += 1 if limit + scroll < total else 0
        elif mrogue.io.key_is(key, tcod.event.K_UP):
            scroll -= 1 if scroll > 0 else 0


class Effect:
    """Describes what will change at a specified moment.

    Currently defines feedback message and optionally a following effect
    (after a delay handled using Timer class).

    Methods:
        * apply() - make some changes and inform the player
    """

    def __init__(
        self, from_item: mrogue.item.item.Consumable, for_unit: mrogue.unit.Unit
    ):
        """Define the source of the Effect (it must provide instructions) and a target - usually an Unit."""
        self.source = from_item
        self.target = for_unit

    def apply(self) -> str:
        """Perform the action described by the first word of the attribute 'effect', then gives feedback.

        Supported keywords:
            * 'identify'
            * 'decurse'
            * 'enchant x'
            * 'fortify_armor x'
            * 'heal x'
            * 'ac_bonus x(hp) y(turns)'
            * 'speed_bonus x y'

        :return: a feedback message to be displayed to the player
        """
        feedback = ""
        keyword, *args = self.source.effect.split()

        # identify all items in the inventory
        if keyword == "identify":
            for i in self.target.inventory:
                if not i.status_identified:
                    i.identified()
            feedback = "Unknown items have been identified."

        # remove all equipped cursed items
        elif keyword == "decurse":
            for i in range(len(self.target.equipped) - 1, -1, -1):
                if self.target.equipped[i].enchantment_level < -1:
                    self.target.unequip(self.target.equipped[i], force=True)

        # enchant an item
        elif keyword == "enchant":
            # select a Wearable
            items = self.target.inventory + self.target.equipped
            items = list(
                filter(lambda x: isinstance(x, mrogue.item.item.Wearable), items)
            )
            item = select_item_from_list(items, "enchant")
            if not item:
                return "You have wasted an enchantment spell."
            if item.enchantment_level < 2:
                name = item.name
                item.upgrade_enchantment(int(args[0]))
                item.identified()
                self.target.recalculate_stats_from_items()
                feedback = f"Your {name} has been enchanted!"
            else:
                item.identified()
                feedback = f"Your {item.name} is already enchanted."

        # fortify an armor piece
        elif keyword == "fortify_armor":
            # select Armor
            items = self.target.inventory + self.target.equipped
            items = list(
                filter(
                    lambda x: isinstance(x, mrogue.item.item.Wearable)
                    and x.subtype == "armor",
                    items,
                )
            )
            item = select_item_from_list(items, "fortify")
            if not item:
                return "You have wasted a fortify spell."
            name = item.name
            item.upgrade_armor(int(args[0]))
            item.identified()
            self.target.recalculate_stats_from_items()
            feedback = f"Your {name} has been fortified."

        # heal a random amount of health points
        elif keyword == "heal":
            self.target.heal(mrogue.utils.roll(int(args[0]), int(args[1])))
            feedback = "Some of your wounds are healed."

        # grant additional speed for a duration
        elif keyword == "speed_bonus":

            def lower_speed():
                self.target.speed_bonus *= 1 / float(args[0])
                self.target.burden_update()
                mrogue.message.Messenger.add("Your speed turns back to normal.")

            mrogue.timers.Timer(int(args[1]), lower_speed)
            self.target.speed_bonus *= float(args[0])
            self.target.burden_update()
            feedback = "You feel much quicker."

        # grant additional armor for a duration
        elif keyword == "ac_bonus":

            def lower_ac():
                self.target.ac_bonus -= int(args[0])
                self.target.recalculate_stats_from_items()
                mrogue.message.Messenger.add("Your skin turns back to normal.")

            mrogue.timers.Timer(int(args[1]), lower_ac)
            self.target.ac_bonus += int(args[0])
            self.target.recalculate_stats_from_items()
            feedback = "Your skin turns into " + (
                "scales." if "scaleskin" in self.source.name else "bark."
            )

        return feedback
