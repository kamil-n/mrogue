# -*- coding: utf-8 -*-
"""Item management - item functions, printing various inventory screens, etc

Classes:
    * ItemManager - helper class to create random items, show and manage held and used items
    * Item - base class for a single type of an item
    * Wearable - a subclass of Item that can be equipped and modifies player's statistics and abilities
    * Stackable - a subclass of Item that can has the amount property
    * Consumable - a subclass of Item that produces an Effect on single use
"""
import random
from random import choice

import tcod
import tcod.constants
import tcod.event

import mrogue.item.data
import mrogue.map
import mrogue.message
import mrogue.player
import mrogue.utils
from mrogue import Point


class Item(mrogue.Entity):
    """Base class for an item. Should not be used directly

    Extends:
        * Entity
    Object attributes:
        * type - class name from the extending class
        * pos - position on the game map
        * base_weight - base weight for this type of item (default material)
        * base_value - base value shown for unidentified items
        * identified_value - value shown after the item is identified
        * value - value when material and quality is taken is into account
        * icon - variable inherited from Entity
        * layer - for the order of rendering if several Entities overlap
        * status_identified - whether the item is identified (all details revealed)
        * name - name for the unidentified version
        * amount - default = 1 for unstackable items
        * identified_name - full name including quality and enchantment
    Methods:
        * dropped() - state change when item is dropped on the ground
        * picked() - state change when item is put into some kind of inventory
        * identified() - state change when this Item instance is identified
    """

    max_name = 39

    def __init__(self, name, base_weight, base_value, icon):
        super().__init__()
        self.pos = None
        self.base_weight = base_weight
        self.base_value = base_value
        self.identified_value = base_value
        self.value = base_value
        self.icon = icon
        self.background = tcod.blue * 0.3
        # self.layer = 2
        self.status_identified = False
        self.name = name
        self.amount = 1
        self.identified_name = name  # TEMP

    def __repr__(self):
        return f"Item('{self.name}', {self.__class__}, 0x{self.icon:x})"  # ", {self.color})"

    def __str__(self):
        return f"{chr(self.icon)} '{self.name}' ({self.amount})"  # " [{self.color}]"

    def dropped(self, coordinates: Point) -> None:
        """Assign a position on the map and add this item to current level's objects group

        :param coordinates: a pair of (x, y) coordinates
        """
        self.add(mrogue.map.Dungeon.current_level.objects_on_map)
        self.pos = coordinates

    def picked(self) -> None:
        """Remove placement data and remove the item from current level's objects group"""
        self.remove(mrogue.map.Dungeon.current_level.objects_on_map)
        self.pos = None

    def identified(self) -> None:
        """Change the name and show real value of the item"""
        self.status_identified = True
        self.name = self.identified_name
        self.value = self.identified_value

    @property
    def interface_name(self):
        color = tcod.white
        prefix = ""
        suffix = ""
        if self.status_identified:
            if hasattr(self, "enchantment_level"):
                color = mrogue.item.data.enchantment_colors[self.enchantment_level]
            if self.subtype == "weapon":
                suffix = f" ({self.props.damage[0]}-{self.props.damage[1]}/{self.props.to_hit_modifier:+d})"
            elif self.subtype == "armor":
                suffix = f" ({self.props.armor_class_modifier:+d})"
        if self.amount > 1:
            prefix = f"{self.amount} "
        elif self in mrogue.player.Player.get().equipped:
            prefix = "(E) "
            color = tcod.light_grey
        elif not self.status_identified:
            prefix = "(?) "
        name = self.name
        if len(prefix + name + suffix) > Item.max_name:
            name = name[: Item.max_name - len(prefix) - len(suffix) - 1] + "+"
        return prefix + name + suffix, color


class Wearable(Item):
    """An item that can be held or worn. Encapsulates two types of functional types: weapons and armor.

    Extends:
        * Item
    Object attributes:
        * material - affects weight, value and Glyph color
        * quality - affects Item stats slightly
        * enchantment_level - affects Item stats severely
        * weight - self explanatory
        * slot - which equipment slot the Item takes
        * subtype - currently either Weapon or Armor
    """

    class Weapon:
        """Holds all the stats related to damage and accuracy.

        Object attributes:
            * speed_modifier - affects global player speed
            * base_to_hit - baseline accuracy bonus
            * to_hit_modifier - accuracy bonus after adding quality and enchantment modifiers
            * base_damage - baseline damage dice (range for the random number generator)
            * damage - damage dice after adding enchantment modifiers
        """

        def __init__(
            self, quality, enchantment_level, speed_modifier, base_to_hit, damage_range
        ):
            self.speed_modifier = speed_modifier
            self.base_to_hit = base_to_hit
            self.to_hit_modifier = self.base_to_hit + quality + enchantment_level
            self.base_damage = damage_range
            self.damage = (
                damage_range[0] + enchantment_level,
                damage_range[1] + enchantment_level,
            )

    class Armor:
        """Hold all the stats related to armor class.

        Object attributes:
            * base_armor_class - baseline armor class modifier
            * armor_class_modifier - armor class modifier after adding quality and enchantment bonuses
        """

        def __init__(self, quality, enchantment_level, ac_mod):
            self.base_armor_class = ac_mod
            self.armor_class_modifier = ac_mod + quality + enchantment_level * 2

    def __init__(
        self,
        name,
        base_weight,
        base_value,
        icon,
        material,
        quality,
        enchantment,
        slot,
        subtype,
        props,
    ):
        super().__init__(name, base_weight, base_value, icon)
        self.material = material
        self.quality = quality
        self.enchantment_level = enchantment
        self.weight = self.base_weight * float(self.material[0])
        self.identified_value = (
            self.base_value
            * (1 + 0.4 * self.quality)
            * (1 + 0.8 * self.enchantment_level)
        )
        self.color = vars(tcod.constants)[self.material[2]]
        self.slot = slot
        quality = mrogue.item.data.quality_levels[self.quality]
        if type(quality) == tuple:
            quality = choice(quality)
        enchantment = mrogue.item.data.enchantment_levels[self.enchantment_level]
        self.identified_name = f"{quality} {enchantment} {self.name}".strip()
        self.identified_name = " ".join(self.identified_name.split())
        self.subtype = subtype
        self.props = props

    def __repr__(self):
        return f"Wearable('{self.name}', {self.subtype}, 0x{self.icon:x})"  # ", {self.color})"

    def upgrade_enchantment(self, amount):
        if self.enchantment_level > 1:
            raise ValueError("Item already at max ench. level.")
        self.enchantment_level += amount
        self.identified_value = (
            self.base_value
            * (1 + 0.4 * self.quality)
            * (1 + 0.8 * self.enchantment_level)
        )
        quality = mrogue.item.data.quality_levels[self.quality]
        if type(quality) == tuple:
            quality = choice(quality)
        enchantment = mrogue.item.data.enchantment_levels[self.enchantment_level]
        self.identified_name = f"{quality} {enchantment} {self.name}".strip()
        self.identified_name = " ".join(self.identified_name.split())
        self.name = self.identified_name
        if self.subtype == "weapon":
            speed = self.props.speed_modifier
            to_hit = self.props.base_to_hit
            damage = self.props.base_damage
            self.props = Wearable.Weapon(
                self.quality, self.enchantment_level, speed, to_hit, damage
            )
        elif self.subtype == "armor":
            ac_mod = self.props.base_armor_class
            self.props = Wearable.Armor(self.quality, self.enchantment_level, ac_mod)

    def upgrade_armor(self, amount):
        if self.subtype != "armor":
            raise ValueError("Can't upgrade armor on non-armor items.")
        self.props.armor_class_modifier += amount
        self.identified_name = "fortified " + self.identified_name
        self.name = self.identified_name


class Stackable(Item):
    """Adds count on top of the Item class

    Extends:
        * Item
    Object attributes:
        * amount - object should remove itself when amount reaches 0
    Methods:
        * used() - reduces the amount when used (as Consumable)
    """

    def __init__(self, name, base_weight, base_value, icon, amount):
        super().__init__(name, base_weight, base_value, icon)
        self.amount = amount
        self.weight = self.base_weight * self.amount
        self.value = self.base_value * self.amount

    # @property
    # def s_name(self):
    #     prefix = 'a' if self.amount == 1 else self.amount
    #     suffix = 's' if self.amount > 1 else ''
    #     return f"{prefix} {self.name}{suffix}"
    #
    # @property
    # def identified_s_name(self):
    #     prefix = 'a' if self.amount == 1 else self.amount
    #     suffix = 's' if self.amount > 1 else ''
    #     return f"{prefix} {self.name}{suffix}"

    def used(self, *args) -> None:
        """Remove self from any list when amount reaches 0"""
        self.amount -= 1
        if self.amount == 0:
            self.kill()


class Consumable(Stackable):
    """Class description.

    Extends:
        * Stackable
    Object attributes:
        * subtype - currently either scroll or potion
        * effect - a string representing the action to perform on use
        * uses - how many times Consumable can be used before reducing the amount
    Methods:
        * used() - apply the effect on use
        * identified() - identifies each copy of this item
        * identify_all() - loops through dungeon and inventory item groups to identify all copies
    """

    def __init__(
        self,
        name,
        base_weight,
        base_value,
        icon,
        amount,
        color,
        effect,
        id_name,
        subtype,
    ):
        """Sets appropriate color and name based on subtype (scroll or potion)"""
        super().__init__(name, base_weight, base_value, icon, amount)
        self.identified_name = id_name
        self.slot = ""
        self.color = color
        self.effect = effect
        # self.uses = template['number_of_uses']
        if self.name in mrogue.player.Player.get().identified_consumables:
            self.identified()
        self.subtype = subtype

    def __repr__(self):
        return f"Consumable('{self.name}', {self.subtype}, 0x{self.icon:x})"  # ", {self.color})"

    def used(self, target) -> str:
        """Apply the related effect and fetch it's feedback message

        :param target: a unit to apply the effect to
        :return: the description of the effect to show the player
        """
        self.identified()
        mrogue.message.Messenger.add("This is {}.".format(self.name))
        super().used(None)
        from mrogue.effects import Effect

        effect = Effect(self, target)
        return effect.apply()

    def identified(self) -> None:
        """Add this item to the list of consumables known to player"""
        mrogue.player.Player.get().identified_consumables.append(self.name)
        super().identified()
        self.identify_all()

    def identify_all(self) -> None:
        """Identify each item of this type in map and player inventory"""
        for i in mrogue.map.Dungeon.current_level.objects_on_map:
            if (
                isinstance(i, Consumable)
                and not i.status_identified
                and i.effect == self.effect
            ):
                i.identified()
        for i in mrogue.player.Player.get().inventory:
            if (
                i.subtype in ("scroll", "potion")
                and not i.status_identified
                and i.effect == self.effect
            ):
                i.identified()
