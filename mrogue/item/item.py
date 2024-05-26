# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
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
from mrogue.io import Color


class Item(ABC, mrogue.Entity):
    max_name = 39

    @abstractmethod
    def __init__(self, name: str, base_weight: float, base_value: float, icon: int):
        super().__init__()
        self.pos: Point | None
        self.base_weight = base_weight
        self.base_value = base_value
        self.identified_value = base_value
        self.value = base_value
        self.icon = icon
        self.background = (0, 0, 76)
        # self.layer = 2
        self.status_identified = False
        self.name = name
        self.amount = 1
        self.identified_name = name  # TEMP

    def __repr__(self) -> str:
        return f"Item('{self.name}', {self.__class__}, 0x{self.icon:x})"  # ", {self.color})"

    def __str__(self) -> str:
        return f"{chr(self.icon)} '{self.name}' ({self.amount})"  # " [{self.color}]"

    def dropped(self, coordinates: Point) -> None:
        self.add(mrogue.map.Dungeon.current_level.objects_on_map)
        self.pos = coordinates

    def picked(self) -> None:
        self.remove(mrogue.map.Dungeon.current_level.objects_on_map)
        self.pos = None

    def identified(self) -> None:
        self.status_identified = True
        self.name = self.identified_name
        self.value = self.identified_value

    @property
    def interface_name(self) -> tuple[str, tuple[int, int, int]]:
        color = Color.white
        prefix = ""
        suffix = ""
        if isinstance(self, Wearable) and self.status_identified:
            if hasattr(self, "enchantment_level"):
                color = mrogue.item.data.enchantment_colors[self.enchantment_level]
            if isinstance(self.props, Wearable.Weapon):
                suffix = (
                    f" ({self.props.damage[0]}-{self.props.damage[1]}/"
                    f"{self.props.to_hit_modifier:+d})"
                )
            else:
                suffix = f" ({self.props.armor_class_modifier:+d})"
        if self.amount > 1:
            prefix = f"{self.amount} "
        elif self in mrogue.player.Player.get().equipped:
            prefix = "(E) "
            color = Color.light_gray
        elif not self.status_identified:
            prefix = "(?) "
        name = self.name
        if len(prefix + name + suffix) > Item.max_name:
            name = name[: Item.max_name - len(prefix) - len(suffix) - 1] + "+"
        return prefix + name + suffix, color


class Wearable(Item):
    class Weapon:
        def __init__(
            self,
            quality: int,
            enchantment_level: int,
            speed_modifier: float,
            base_to_hit: int,
            damage_range: tuple[int, int],
        ):
            self.speed_modifier = speed_modifier
            self.base_to_hit = base_to_hit
            self.to_hit_modifier = self.base_to_hit + quality + enchantment_level
            self.base_damage = damage_range
            self.damage = (
                max(damage_range[0] + enchantment_level, 1),
                max(damage_range[1] + enchantment_level, 1),
            )

    class Armor:
        def __init__(self, quality: int, enchantment_level: int, ac_mod: int):
            self.base_armor_class = ac_mod
            self.armor_class_modifier = ac_mod + quality + enchantment_level * 2

    def __init__(
        self,
        name: str,
        base_weight: float,
        base_value: float,
        icon: int,
        material: tuple[str, str, str],
        quality: int,
        enchantment: int,
        slot: str,
        subtype: str,
        props: Weapon | Armor,
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
        quality_word = mrogue.item.data.quality_levels[self.quality]
        if type(quality_word) == tuple:
            quality_word = choice(quality_word)
        enchantment_word = mrogue.item.data.enchantment_levels[self.enchantment_level]
        self.identified_name = f"{quality_word} {enchantment_word} {self.name}".strip()
        self.identified_name = " ".join(self.identified_name.split())
        self.props = props

    def __repr__(self) -> str:
        return f"Wearable('{self.name}', {type(self.props)}, 0x{self.icon:x})"  # ", {self.color})"

    def upgrade_enchantment(self, amount: int) -> None:
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
        if isinstance(self.props, Wearable.Weapon):
            speed = self.props.speed_modifier
            to_hit = self.props.base_to_hit
            damage = self.props.base_damage
            self.props = Wearable.Weapon(
                self.quality, self.enchantment_level, speed, to_hit, damage
            )
        else:
            ac_mod = self.props.base_armor_class
            self.props = Wearable.Armor(self.quality, self.enchantment_level, ac_mod)

    def upgrade_armor(self, amount: int) -> None:
        if type(self.props) != Wearable.Armor:
            raise ValueError("Can't upgrade armor on non-armor items.")
        self.props.armor_class_modifier += amount
        self.identified_name = "fortified " + self.identified_name
        self.name = self.identified_name


class Stackable(Item):
    @abstractmethod
    def __init__(
        self, name: str, base_weight: float, base_value: float, icon: int, amount: int
    ):
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


class Consumable(Stackable):
    def __init__(
        self,
        name: str,
        base_weight: float,
        base_value: float,
        icon: int,
        amount: int,
        color: tuple[int, int, int],
        effect: str,
        id_name: str,
        subtype: str,
    ):
        super().__init__(name, base_weight, base_value, icon, amount)
        self.identified_name = id_name
        self.slot = ""
        self.color = color
        self.effect = effect
        # self.uses = template['number_of_uses']
        if self.name in mrogue.player.Player.get().identified_consumables:
            self.identified()
        self.subtype = subtype

    def __repr__(self) -> str:
        return f"Consumable('{self.name}', {self.subtype}, 0x{self.icon:x})"  # ", {self.color})"

    def used(self, target: mrogue.unit.Unit) -> str:
        self.identified()
        mrogue.message.Messenger.add("This is {}.".format(self.name))
        self.amount -= 1
        if self.amount == 0:
            self.kill()

        from mrogue.effects import Effect

        effect = Effect(self, target)
        return effect.apply()

    def identified(self) -> None:
        mrogue.player.Player.get().identified_consumables.append(self.name)
        super().identified()
        self.identify_all()

    def identify_all(self) -> None:
        for i in mrogue.map.Dungeon.current_level.objects_on_map:
            if (
                isinstance(i, Consumable)
                and not i.status_identified
                and i.effect == self.effect
            ):
                i.identified()
        for i in mrogue.player.Player.get().inventory:
            if (
                isinstance(i, Consumable)
                and not i.status_identified
                and i.effect == self.effect
            ):
                i.identified()
