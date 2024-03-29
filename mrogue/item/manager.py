# -*- coding: utf-8 -*-
from __future__ import annotations

import string
from random import choice, choices
from typing import Any, Callable

import tcod
import tcod.constants
import tcod.event

import mrogue.utils
from mrogue import Point
from mrogue.io import Color
from mrogue.map import Dungeon
from mrogue.player import Player

from . import data, item, template


class ItemManager:
    blueprints: dict[str, template.ItemTemplate]
    item_selection: dict[int, dict[str, Any]] = {}

    def __init__(self) -> None:
        for s in filter(lambda x: x["type"] == "scroll", data.templates):
            data.scroll_names[s["name"]] = mrogue.utils.random_scroll_name()  # type: ignore[index]
        for p in filter(lambda x: x["type"] == "potion", data.templates):
            data.potion_colors[p["name"]] = choice(  # type: ignore[index]
                list(data.materials["potions"].items())
            )
        self.screen = mrogue.io.Screen.get()
        for t in data.templates:
            template.ItemTemplate(t)
        ItemManager.blueprints = template.ItemTemplate.all()
        for level in range(9):
            ItemManager.item_selection[level] = dict()
            budget_bounds = (level // 2) * 10, level * 5 + 10
            ItemManager.item_selection[level]["budget"] = list(
                range(budget_bounds[0], budget_bounds[1] + 1)
            )

    @classmethod
    def create_loot(cls, num_items: int) -> None:
        for _ in range(num_items):
            cls.random_item().dropped(Dungeon.find_spot())

    @classmethod
    def prepare_selection_for_level(cls, level: int) -> None:
        templates: list[template.ItemTemplate] = []
        for item_template in cls.blueprints.values():
            if type(item_template) in (
                template.PotionTemplate,
                template.ScrollTemplate,
            ):
                templates.append(item_template)
            else:  # if random, match all possible budget versions against the target budget
                budget_grain = {item_template.budget(i) for i in range(-2, 3)}
                if (
                    set(cls.item_selection[level]["budget"]).intersection(budget_grain)
                    != set()
                ):  # if they overlap
                    templates.append(item_template)
        cls.item_selection[level]["ungrouped"] = templates
        # group templates by type
        template_groups = {
            tpl.__class__.__name__: [
                sel
                for sel in templates
                if sel.__class__.__name__ == tpl.__class__.__name__
            ]
            for tpl in templates
        }
        cls.item_selection[level]["grouped"] = template_groups

    @classmethod
    def random_item(
        cls, keyword: str = None, groups: list[list[item.Item]] = None
    ) -> item.Item:
        level = Dungeon.depth()
        if "templates" not in cls.item_selection[level]:
            cls.prepare_selection_for_level(level)
        grouped = cls.item_selection[level]["grouped"]
        ungrouped = cls.item_selection[level]["ungrouped"]
        if keyword:
            # random choice from templates containing a specific keyword
            target = choice(
                list(filter(lambda x: keyword in getattr(x, "keywords", []), ungrouped))
            )
        else:
            item_type = choices(
                list(grouped.keys()), [5, 4, 2, 3]
            )  # weapons:armor:scrolls:potions ratio
            target = choice(grouped[item_type[0]])
        budget_min, budget_max = (
            cls.item_selection[level]["budget"][0],
            cls.item_selection[level]["budget"][-1],
        )
        random_item = target.create(True, budget_min, budget_max)
        random_item.add(groups)
        return random_item

    @staticmethod
    def get_item_on_map(coordinates: Point) -> list[item.Item]:
        return mrogue.utils.find_in(
            Dungeon.current_level.objects_on_map,
            "pos",
            coordinates,
            item.Item,
            True,
        )

    @staticmethod
    def print_list(
        inventory: list[item.Item],
        scroll: int,
        width: int,
        limit: int,
        show_details: bool = False,
    ) -> tcod.Console:
        window = tcod.Console(width, limit)
        # window.draw_frame(0, 0, window.width, window.height)
        if scroll > 0:
            window.print(0, 0, chr(0x2191), Color.black, Color.white)
        for i in range(len(inventory)):
            if i > limit - 1:
                break
            it = inventory[i + scroll]
            window.print(1, i, f"{string.ascii_letters[i+scroll]}) ")
            window.print(4, i, chr(it.icon), it.color)
            window.print(6, i, *it.interface_name)
            if show_details and type(it) == item.Wearable:
                window.print(
                    item.Item.max_name + 6,
                    i,
                    f"{it.slot:>6} {it.weight*it.amount:6.2f} {it.value*it.amount:>7.2f}",
                )
        if limit + scroll < len(inventory):
            window.print(0, limit - 1, chr(0x2193), Color.black, Color.white)
        return window

    @staticmethod
    def print_inventory_ui(
        window: tcod.Console, selected_sort: int, weight: int, value: int
    ) -> None:
        window.clear()
        window.draw_frame(0, 0, window.width, window.height, decoration="╔═╗║ ║╚═╝")
        window.print_box(0, 0, window.width, 1, " Inventory ", alignment=tcod.CENTER)
        window.print(2, 1, "Select an item or Esc to close:")
        window.print(item.Item.max_name + 11, 1, "[/] Sort", Color.yellow)
        window.print(6, 2, "Name", Color.lighter_gray)
        window.print(
            item.Item.max_name + 9, 2, "Slot     Wt     Val", Color.lighter_gray
        )
        window.print(selected_sort, 2, chr(0x2193), Color.yellow)
        window.print(
            item.Item.max_name + 7,
            window.height - 2,
            f"Total: {weight:6.2f} {value:7.2f}",
            Color.lighter_gray,
        )

    def show_inventory(self) -> bool:
        player = Player.get()
        # allow to sort the list by one of four attributes
        sorts = mrogue.utils.circular(
            [
                ("slot", item.Item.max_name + 8),
                ("weight", item.Item.max_name + 17),
                ("value", item.Item.max_name + 24),
                ("name", 5),
            ]
        )
        sort = next(sorts)
        raw_inventory = player.inventory + player.equipped
        total_items = len(raw_inventory)
        item_limit, scroll = 14, 0
        window_height, window_width = (
            5 + min(total_items, item_limit),
            item.Item.max_name + 30,
        )
        total_weight, total_value = sum([i.weight for i in raw_inventory]), sum(
            [i.value for i in raw_inventory]
        )
        inventory_window = tcod.Console(window_width, window_height, "F")
        while True:
            # present the whole inventory screen
            self.print_inventory_ui(
                inventory_window, sort[1], total_weight, total_value
            )
            inventory = sorted(
                raw_inventory, key=lambda x: (getattr(x, sort[0]), x.name)
            )
            self.print_list(
                inventory, scroll, window_width - 2, window_height - 5, True
            ).blit(inventory_window, 1, 3)
            inventory_window.blit(self.screen, 4, 4)
            self.screen.present()
            # wait for input
            key = mrogue.io.wait()
            if key[1] & mrogue.io.ignore_mods == mrogue.io.ignore_mods:
                key = (key[0], key[1] - mrogue.io.ignore_mods)
            if mrogue.io.key_is(key, tcod.event.K_ESCAPE):
                return False
            elif mrogue.io.key_is(key, tcod.event.K_DOWN):
                scroll += 1 if item_limit + scroll < total_items else 0
            elif mrogue.io.key_is(key, tcod.event.K_UP):
                scroll -= 1 if scroll > 0 else 0
            elif mrogue.io.key_is(key, tcod.event.K_SLASH):
                sort = next(sorts)
            # if an a-zA-z key was pressed and it represents an item on the list:
            elif key in data.letters and data.letters[key] in range(total_items):
                # highlight selected item and present context actions
                i = inventory[data.letters[key]]
                highlight_line = 3 + data.letters[key] - scroll
                if 3 <= highlight_line <= window_height - 3:
                    inventory_window.draw_rect(
                        1, highlight_line, window_width - 2, 1, 0, bg=Color.blue
                    )
                    inventory_window.blit(self.screen, 4, 4)
                context_actions: list[
                    tuple[str, item.Item, Callable[[None], None]]
                ] = []
                if isinstance(i, item.Consumable):
                    context_actions.append(("Use item", i, player.use))
                elif i in player.equipped:
                    context_actions.append(("Unequip item", i, player.unequip))
                elif isinstance(i, item.Wearable):
                    context_actions.append(("Equip item", i, player.equip))
                if i not in player.equipped:
                    context_actions.append(("Drop item", i, player.drop_item))
                effect = mrogue.io.select_action(context_actions)
                if effect[0]:
                    return effect[1] if effect[1] is not None else True

    def show_equipment(self) -> bool:
        player = Player.get()
        width, height = item.Item.max_name + 12, 12
        slots = ("main", "both", "off", "head", "chest", "feet", "legs", "hands")
        window = tcod.Console(width, height, "F")
        while True:
            # present the whole equipment window
            window.clear()
            window.draw_frame(0, 0, width, height, decoration="╔═╗║ ║╚═╝")
            window.print_box(0, 0, width, 1, " Equipment ", alignment=tcod.CENTER)
            window.print(2, 1, "Select a slot to manage or Esc to close:")
            for line, slot in enumerate(slots):
                window.print(2, line + 3, f"{chr(97 + line)}) {slot.capitalize():>5}:")
                it = mrogue.utils.find_in(player.equipped, "slot", slot)
                if it:
                    name, _ = it.interface_name
                    window.print(12, line + 3, chr(it.icon), it.color)
                    window.print(
                        14,
                        line + 3,
                        f"{name[4:]}",
                        data.enchantment_colors[it.enchantment_level],
                    )
            window.blit(self.screen, 4, 4)
            self.screen.present()
            # wait for input
            key = mrogue.io.wait()
            if key[1] & mrogue.io.ignore_mods == mrogue.io.ignore_mods:
                key = (key[0], key[1] - mrogue.io.ignore_mods)
            if mrogue.io.key_is(key, tcod.event.K_ESCAPE):
                return False
            # if a-z was pressed and it represents one of the slots:
            elif key[0] in range(97, 97 + len(slots)):
                it = mrogue.utils.find_in(player.equipped, "slot", slots[key[0] - 97])
                if it:
                    return player.unequip(it)
                else:
                    # if the slot is empty, highlight it and present list of available items
                    items = list(
                        filter(
                            lambda x: x.slot == slots[key[0] - 97],
                            player.inventory,
                        )
                    )
                    if not items:
                        continue
                    items.sort(key=lambda x: (getattr(x, "enchantment_level"), x.name))
                    window.draw_rect(1, 3 + key[0] - 97, width - 2, 1, 0, bg=Color.blue)
                    window.blit(self.screen, 4, 4)
                    total_items = len(items)
                    limit, scroll = 10, 0
                    selection = tcod.Console(
                        item.Item.max_name + 9, 2 + min(limit, total_items), "F"
                    )
                    selection.draw_frame(
                        0, 0, selection.width, selection.height, "Select item to equip:"
                    )
                    while True:
                        self.print_list(
                            items, scroll, selection.width - 2, selection.height - 2
                        ).blit(selection, 1, 1)
                        selection.blit(self.screen, 4 + 10, 4 + 2)
                        self.screen.present()
                        selected = mrogue.io.wait()
                        if mrogue.io.key_is(selected, tcod.event.K_ESCAPE):
                            break
                        elif mrogue.io.key_is(selected, tcod.event.K_DOWN):
                            scroll += 1 if limit + scroll < total_items else 0
                        elif mrogue.io.key_is(selected, tcod.event.K_UP):
                            scroll -= 1 if scroll > 0 else 0
                        elif selected[0] in range(97, 97 + total_items):
                            player.equip(items[selected[0] - 97])
                            return True

    def show_pickup_choice(
        self, items: list[item.Item]
    ) -> item.Item | list[item.Item] | bool:
        total = len(items)
        w, limit, scroll = item.Item.max_name + 9, 6, 0
        h = 3 + min(limit, total)
        char = string.ascii_letters[total - 1]
        window = tcod.Console(w, h, "F")
        while True:
            window.clear()
            window.draw_frame(0, 0, w, h, decoration="╔═╗║ ║╚═╝")
            window.print_box(0, 0, w, 1, " Pick up: ", alignment=tcod.CENTER)
            window.print_box(
                0,
                1,
                w,
                1,
                f"[a-{char}] single item, [,] - all:",
                Color.light_gray,
                alignment=tcod.CENTER,
            )
            self.print_list(items, scroll, w - 2, h - 3).blit(window, 1, 2)
            window.blit(
                self.screen, self.screen.width - w - 1, self.screen.height - h - 1
            )
            self.screen.present()
            key = mrogue.io.wait()
            if key[1] & mrogue.io.ignore_mods == mrogue.io.ignore_mods:
                key = (key[0], key[1] - mrogue.io.ignore_mods)
            if mrogue.io.key_is(key, tcod.event.K_ESCAPE):
                return False
            elif mrogue.io.key_is(key, tcod.event.K_COMMA):
                return items
            elif key[0] in range(97, 97 + total):
                return [items[key[0] - 97]]
            elif mrogue.io.key_is(key, tcod.event.K_DOWN):
                scroll += 1 if limit + scroll < total else 0
            elif mrogue.io.key_is(key, tcod.event.K_UP):
                scroll -= 1 if scroll > 0 else 0
