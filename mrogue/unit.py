# -*- coding: utf-8 -*-
from __future__ import annotations

import random
from copy import copy
from sys import argv
from typing import TYPE_CHECKING

import tcod.constants

import mrogue.map
import mrogue.message
import mrogue.utils

if TYPE_CHECKING:
    import mrogue.item


class AbilityScore:
    def __init__(self, name, score):
        self.name = name
        self._original_score = self.score = score

    @property
    def mod(self):
        return (self.score - 10) // 2


class Unit(mrogue.Entity):
    def __init__(
        self,
        name,
        icon,
        sight_range,
        abi_scores,
        keywords,
        speed,
        proficiency,
        damage_range,
        ac_bonus,
        base_hp_from_dice,
    ):
        super().__init__()
        self.player = False
        self.inventory = []
        self.equipped = []
        self.name = name
        self.pos = mrogue.map.Dungeon.find_spot()
        self.icon = icon[0]
        self.color = vars(tcod.constants)[icon[1]]
        # self.layer = 1
        self.sight_range = sight_range
        self.abilities = {
            "str": AbilityScore("Strength", abi_scores[0]),
            "dex": AbilityScore("Dexterity", abi_scores[1]),
            "con": AbilityScore("Constitution", abi_scores[2]),
        }
        self.load_thresholds = (5.0, 30.0, 50.0)
        self.speed_bonus = 1.0
        self.speed = speed
        self.initiative = int(speed * 100)
        self.keywords = keywords
        self.proficiency = proficiency
        self.ability_bonus = (
            self.abilities["dex"].mod
            if "finesse" in keywords
            else self.abilities["str"].mod
        )
        self.to_hit = self.proficiency + self.ability_bonus
        self.default_damage_dice = damage_range
        self.damage_dice = self.default_damage_dice
        self.base_armor_class = 10 + self.abilities["dex"].mod
        self.ac_bonus = ac_bonus
        self.armor_class = self.base_armor_class + self.ac_bonus
        self.damage_reduction = self.armor_class / 100
        self.current_HP = base_hp_from_dice + self.abilities["con"].mod
        self.max_HP = base_hp_from_dice
        self.moved = False

    def __repr__(self):
        return f"Unit('{self.name}', 0x{self.icon:x})"  # ", {self.color})"

    def __str__(self):
        return f"{chr(self.icon)} '{self.name}'"  # " [{self.color}]"

    def update(self) -> None:
        self.moved = False
        self.initiative = int(self.speed * 100) if self.speed != 0.0 else 100

    def burden_update(self) -> None:
        pass

    def add_item(self, item: mrogue.item.item.Item) -> None:
        item.add(self.inventory)
        self.burden_update()

    def use(self, item: mrogue.item.item.Consumable) -> None:
        effect = item.used(self)
        self.burden_update()
        mrogue.message.Messenger.add(effect)

    def recalculate_stats_from_items(self):
        # weapon
        self.to_hit = self.proficiency + self.ability_bonus
        self.damage_dice = self.default_damage_dice
        item = mrogue.utils.find_in(self.equipped, "subtype", "weapon")
        if item:
            self.to_hit += item.props.to_hit_modifier
            self.damage_dice = (
                item.props.damage[0] + self.abilities["str"].mod,
                item.props.damage[1] + self.abilities["str"].mod,
            )
        # armor
        bonus_ac_equipped = sum(
            [
                i.props.armor_class_modifier
                for i in self.equipped
                if i.subtype == "armor"
            ]
        )
        self.armor_class = (
            10 + self.abilities["dex"].mod + self.ac_bonus + bonus_ac_equipped
        )
        self.damage_reduction = self.armor_class / 100

    def equip(self, item: mrogue.item.item.Wearable, quiet: bool = False) -> bool:
        slot = [item.slot]
        if item.slot == "both":
            slot = ["main", "both", "off"]
        elif item.slot == "main":
            slot = ["main", "both"]
        elif item.slot == "off":
            slot = ["both", "off"]
        for i in self.equipped.copy():
            if i.slot in slot:
                if i.enchantment_level < -1:
                    mrogue.message.Messenger.add("You can't replace cursed items.")
                    return False
                self.unequip(i)
        item.add(self.equipped)
        item.remove(self.inventory)
        self.recalculate_stats_from_items()
        msg = f"{self.name.capitalize()} equipped {item.name}."
        if self.player:
            item.identified()
        if not quiet:
            mrogue.message.Messenger.add(msg)
        return True

    def unequip(
        self, item: mrogue.item.item.Wearable, quiet: bool = False, force: bool = False
    ) -> bool:
        if item.enchantment_level < -1 and not force:
            mrogue.message.Messenger.add("Cursed items can't be unequipped.")
            return False
        item.add(self.inventory)
        item.remove(self.equipped)
        self.recalculate_stats_from_items()
        msg = f"{self.name.capitalize()} unequipped {item.name}."
        if not quiet:
            mrogue.message.Messenger.add(msg)
        return True

    def drop_item(self, item: mrogue.item.item.Item, quiet: bool = False) -> None:
        if item.amount > 1:
            item.amount -= 1
            new_item = copy(item)
            new_item.amount = 1
            new_item.dropped(self.pos)
        else:
            item.remove(self.inventory, self.equipped)
            item.dropped(self.pos)
        self.burden_update()
        msg = f"{self.name.capitalize()} dropped {item.name}."
        if not quiet:
            mrogue.message.Messenger.add(msg)

    def pickup_item(self, item_list: list[mrogue.item.item.Item]) -> bool:
        if item_list:
            item = item_list.pop(0)
            if issubclass(type(item), mrogue.item.item.Stackable):
                # in case of Stackables, pick just a singular amount
                existing_item = mrogue.utils.find_in(self.inventory, "name", item.name)
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
            self.burden_update()
            msg = f"{self.name.capitalize()} picked up {item.name}."
            mrogue.message.Messenger.add(msg)
            return True
        else:
            msg = "There are no items here."
            mrogue.message.Messenger.add(msg)
            return False

    def move(self, success: bool = True) -> None:
        self.moved = success

    def attack(self, target: mrogue.unit.Unit) -> None:
        msg = self.name.capitalize() + " "
        attack_roll = mrogue.utils.roll(1, 20)
        critical_hit = attack_roll == 20
        if target.player and critical_hit:
            critical_hit = random.random() > target.crit_immunity
        if critical_hit or attack_roll + self.to_hit >= target.armor_class:
            damage_roll = mrogue.utils.roll(*self.damage_dice, critical_hit)
            msg += f"{'critically ' if critical_hit else ''}hit{'' if self.player else 's'}"
            mrogue.message.Messenger.add("{} {}.".format(msg, target.name))
            target.take_damage(damage_roll)
        else:
            if attack_roll == 1:
                msg += f"critically miss{'' if self.player else 'es'}"
            else:
                msg += f"miss{'' if self.player else 'es'}"
            mrogue.message.Messenger.add("{} {}.".format(msg, target.name))

    def take_damage(self, damage: int) -> None:
        absorption = int(self.damage_reduction * damage)
        damage -= absorption
        self.current_HP -= damage
        if self.current_HP < 1:
            self.die()

    def heal(self, amount: int) -> None:
        self.current_HP += amount
        if self.current_HP > self.max_HP:
            self.current_HP = self.max_HP

    def die(self) -> None:
        mrogue.message.Messenger.add(f"{self.name.capitalize()} died.")
        if not (self.player and "debug" in argv):
            self.kill()
            if not self.player:
                for item in self.equipped:
                    self.unequip(item, quiet=True, force=True)
                for item in self.inventory:
                    self.drop_item(item, quiet=True)
            self.remove(
                mrogue.map.Dungeon.current_level.units,
                mrogue.map.Dungeon.current_level.objects_on_map,
            )
