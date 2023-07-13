# -*- coding: utf-8 -*-
from __future__ import annotations

from random import choice, choices
from typing import Any

import tcod.constants

from . import data, item


class ItemTemplate:
    _subclass_registry: dict[str, Any] = {}
    _templates: dict[str, ItemTemplate] = {}

    def __init_subclass__(cls, type: str, *args, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        cls._subclass_registry[type] = cls

    def __new__(cls, template: dict[str, Any]) -> ItemTemplate:
        subclass = cls._subclass_registry[template["type"]]
        obj = object.__new__(subclass)
        obj._template = template
        return obj

    def __init__(self, *args):
        self.name = self._template["name"]
        self.weight = self._template["base_weight"]
        self.value = self._template["base_value"]
        self.icon = self._template["icon"]

    def __str__(self) -> str:
        return f"{self._template['name']} {self.__class__.__name__}"

    def budget(self, quality: int) -> int:
        return 25

    @staticmethod
    def randomize() -> tuple[int, int]:
        enchantment = choices(list(data.enchantment_levels.keys()), [1, 2, 10, 2, 1])
        quality = choices(list(data.quality_levels.keys()), [1, 3, 10, 3, 1])
        return quality[0], enchantment[0]

    @classmethod
    def all(cls) -> dict[str, ItemTemplate]:
        return cls._templates


class WeaponTemplate(ItemTemplate, type="weapon"):
    def __init__(self, *args):
        super().__init__()
        self.material = data.materials["weapons"][self._template["material"]]
        self.slot = self._template["slot"]
        self.keywords = self._template["keywords"]  # i.e. ['light']
        self.speed = self._template["speed_modifier"]
        self.to_hit = self._template["to_hit_modifier"]
        self.damage = self._template["damage_range"]
        super()._templates[self.name] = self

    def budget(self, quality: int) -> int:
        budget = self.damage[0] * 9 + self.damage[1] + self.to_hit * 10
        budget += int(budget * quality * 0.45)
        return budget

    def __repr__(self) -> str:
        return (
            f"{self._template['name']} [{self.damage[0]}-{self.damage[1]}/{self.to_hit}] "
            f"{self.__class__.__name__}"
        )

    def create(
        self, random: bool = False, min_budget: int = 0, max_budget: int = 10
    ) -> item.Wearable:
        if random:
            mat_name, mat_mods = choice(list(data.materials["weapons"].items()))
            name = f"{mat_name} {self.name}"
            material = mat_mods
            quality, enchantment = 0, 0
            while not (min_budget <= self.budget(quality) <= max_budget):
                quality, enchantment = ItemTemplate.randomize()
            props = item.Wearable.Weapon(
                quality, enchantment, self.speed, self.to_hit, self.damage
            )
            return item.Wearable(
                name,
                self.weight,
                self.value,
                self.icon,
                material,
                quality,
                enchantment,
                self.slot,
                "weapon",
                props,
            )
        name = f"{self._template['material']} {self.name}"
        props = item.Wearable.Weapon(0, 0, self.speed, self.to_hit, self.damage)
        return item.Wearable(
            name,
            self.weight,
            self.value,
            self.icon,
            self.material,
            0,
            0,
            self.slot,
            "weapon",
            props,
        )


class ArmorTemplate(ItemTemplate, type="armor"):
    def __init__(self, *args):
        super().__init__()
        self.slot = self._template["slot"]
        self.keywords = self._template["keywords"]
        if len(self.keywords):
            self.material = data.materials["armor"][self.keywords[0]][
                self._template["material"]
            ]
        else:
            self.all_materials = data.materials["armor"]["organic"]
            self.all_materials.update(data.materials["armor"]["metal"])
            self.material = self.all_materials[self._template["material"]]
        self.ac = self._template["armor_class_modifier"]
        super()._templates[self.name] = self

    def budget(self, quality: int) -> int:
        budget = self.ac * 10
        budget += int(budget * quality * 0.45)
        return budget

    def __repr__(self) -> str:
        return f"{self._template['name']} [{self.ac}] {self.__class__.__name__}"

    def create(
        self, random: bool = False, min_budget: int = 0, max_budget: int = 10
    ) -> item.Wearable:
        if random:
            if len(self.keywords):
                materials = data.materials["armor"][self.keywords[0]]
            else:
                materials = self.all_materials
            mat_name, mat_mods = choice(list(materials.items()))
            name = f"{mat_name} {self.name}"
            material = mat_mods
            quality, enchantment = 0, 0
            while not (min_budget <= self.budget(quality) <= max_budget):
                quality, enchantment = ItemTemplate.randomize()
            props = item.Wearable.Armor(quality, enchantment, self.ac)
            return item.Wearable(
                name,
                self.weight,
                self.value,
                self.icon,
                material,
                quality,
                enchantment,
                self.slot,
                "armor",
                props,
            )
        self.name = f"{self._template['material']} {self.name}"
        props = item.Wearable.Armor(0, 0, self.ac)
        return item.Wearable(
            self.name,
            self.weight,
            self.value,
            self.icon,
            self.material,
            0,
            0,
            self.slot,
            "armor",
            props,
        )


class ScrollTemplate(ItemTemplate, type="scroll"):
    def __init__(self, *args):
        super().__init__()
        self.color = self._template["color"]
        self.effect = self._template["effect"]
        self.uses = self._template["number_of_uses"]
        super()._templates[self.name] = self

    def create(self, *args) -> item.Consumable:
        color = vars(tcod.constants)[self.color]
        name = f"scroll titled {data.scroll_names[self.name]}"
        id_name = f"scroll of {self.name}"
        return item.Consumable(
            name,
            self.weight,
            self.value,
            self.icon,
            1,
            color,
            self.effect,
            id_name,
            "scroll",
        )


class PotionTemplate(ItemTemplate, type="potion"):
    def __init__(self, *args):
        super().__init__()
        self.effect = self._template["effect"]
        self.uses = self._template["number_of_uses"]
        super()._templates[self.name] = self

    def create(self, *args) -> item.Consumable:
        color = data.potion_colors[self.name][1]
        name = f"{data.potion_colors[self.name][0]} potion"
        id_name = f"potion of {self.name}"
        return item.Consumable(
            name,
            self.weight,
            self.value,
            self.icon,
            1,
            color,
            self.effect,
            id_name,
            "potion",
        )
