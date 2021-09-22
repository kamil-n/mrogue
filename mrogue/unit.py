# -*- coding: utf-8 -*-
"""Represents a mobile Entity

Classes:
    * AbilityScore - Ability score as defined by Dungeon & Dragons rules
    * Unit - A mobile Entity
"""
from copy import copy
from sys import argv
import tcod.constants
import mrogue.item
import mrogue.map
import mrogue.message
import mrogue.utils


class AbilityScore:
    """Quantifier of a basic character attribute.

    Object attributes:
        * name - name of this ability (Str., Dex., Con., Wis., Int., Cha.)
        * score - a number between 1 and 20
        * _original_score - in case it would need to be reset
    Methods:
        * mod() - modifier added to a skill check based on this ability
    """

    def __init__(self, name, score):
        self.name = name
        self._original_score = self.score = score

    @property
    def mod(self):
        return (self.score - 10) // 2


class Unit(mrogue.Entity):
    """A mobile entity that can carry and use items, attack other Entities, etc

    Extends:
        * Entity
    Object attributes:
        * player - whether Entity is a Player or a Monster
        * inventory - a list for holding all carried items
        * equipped - a list for grouping all worn/held items
        * name - race/type in case of Monsters
        * pos - position on current Level
        * layer - used for determining which Glyph should be printed on top of a cell
        * sight_range - how far an Entity can detect Entities and terrain
        * abilities - currently 3 abilities used in combat/exploration
        * load_thresholds - breakpoints for calculating encumbrance from Items
        * speed - a modifier to amount of ticks between turns
        * ticks_left - how soon an Entity can take it's turn
        * keywords - helper attributes for determining additional mechanics
        * proficiency - global bonus to ability checks
        * ability_bonus - either Strength or Dexterity bonus to be added to attack rolls
        * to_hit - total bonus to attack rolls (the higher the better)
        * default_damage_dice - default for calculating damage rolls when unarmed
        * damage_dice - used in combat, either default (unarmed) or calculated from a Weapon used
        * base_armor_class - inherent armor class (when just dodging)
        * ac_bonus - a bonus from natural armor
        * armor_class - total armor value including worn Armor
        * damage_reduction - flat damage reduction for balancing combat
        * current_HP - current level of health
        * max_HP - maximum level of health
        * moved - if Unit performed movement action on last turn
    Methods:
        * update() - placeholder for actions to be considered every turn
        * burden_update() - placeholder for encumbrance calculation (only Player)
        * add_item() - puts a new Item in the inventory
        * equip() - calculates Unit stats in case of Wearables; identifies equipped item
        * use() - basic actions when an item is used (watching encumbrance, etc)
        * unequip() - recalculates Unit stats after Wearable is removed, checks for curse status
        * drop_item() - changes item placement in various groups, handles additional logic in case of Stackables
        * pickup_item() - changes item placement in various groups, handles additional logic in case of Stackables
        * move() - to be redefined in extending classes
        * attack() - makes the attack roll and calculates success
        * take_damage() - subtract health points and take action after going below 1
        * heal() - add hit points
        * die() - remove self from all groups and drop worn and held items
    """

    def __init__(self, name, icon, sight_range, abi_scores, keywords, speed, proficiency,
                 damage_dice, ac_bonus, base_hp_from_dice):
        super().__init__()
        self.player = False
        self.inventory = []
        self.equipped = []
        self.name = name
        self.pos = mrogue.map.Dungeon.find_spot()
        self.icon = icon[0]
        self.color = vars(tcod.constants)[icon[1]]
        self.layer = 1
        self.sight_range = sight_range
        self.abilities = {
            'str': AbilityScore('Strength', abi_scores[0]),
            'dex': AbilityScore('Dexterity', abi_scores[1]),
            'con': AbilityScore('Constitution', abi_scores[2])
        }
        self.load_thresholds = (5.0, 30.0, 50.0)
        self.speed = speed
        self.ticks_left = int(speed * 100)
        self.keywords = keywords
        self.proficiency = proficiency
        self.ability_bonus = self.abilities['dex'].mod if 'finesse' in keywords else self.abilities['str'].mod
        self.to_hit = self.proficiency + self.ability_bonus
        num, sides, mod = mrogue.utils.decompile_dmg_dice(damage_dice)
        self.default_damage_dice = mrogue.utils.compile_dmg_dice(num, sides, mod + self.ability_bonus)
        self.damage_dice = self.default_damage_dice
        self.base_armor_class = 10 + self.abilities['dex'].mod
        self.ac_bonus = ac_bonus
        self.armor_class = self.base_armor_class + self.ac_bonus
        self.damage_reduction = self.armor_class / 100
        self.current_HP = base_hp_from_dice + self.abilities['con'].mod
        self.max_HP = base_hp_from_dice
        self.moved = False

    def __repr__(self):
        return f"Unit('{self.name}','{self.icon}')"  # ", {self.color})"

    def __str__(self):
        return f"{self.icon} '{self.name}'"  # " [{self.color}]"

    def update(self) -> None:
        pass

    def burden_update(self) -> None:
        pass

    def add_item(self, item) -> None:
        """Add an item to Unit's inventory and recalculate encumbrance

        :param item: Item to be added
        """
        item.add(self.inventory)
        self.burden_update()

    def equip(self, item, quiet: bool = False) -> None:
        """Switch groups and apply bonuses from wearing the Item

        :param item: Item to be worn
        :param quiet: should feedback messages be suppressed?
        """
        for i in self.equipped:
            if item.slot == i.slot:
                self.unequip(i)
        item.add(self.equipped)
        item.remove(self.inventory)
        if item.type == mrogue.item.Wearable and item.subtype == 'weapon':
            self.to_hit = self.proficiency + self.ability_bonus + item.props.to_hit_modifier
            num, sides, mod = mrogue.utils.decompile_dmg_dice(item.props.damage)
            self.damage_dice = mrogue.utils.compile_dmg_dice(num, sides, mod + self.ability_bonus)
        elif item.type == mrogue.item.Wearable and item.subtype == 'armor':
            bonus_ac_equipped = sum([i.props.armor_class_modifier for i in self.equipped if i.subtype == 'armor'])
            self.armor_class = 10 + self.abilities['dex'].mod + self.ac_bonus + bonus_ac_equipped
            self.damage_reduction = self.armor_class / 100
        msg = f'{self.name} equipped {item.name}.'
        if self.player:
            item.identified()
        if not quiet:
            mrogue.message.Messenger.add(msg)

    def use(self, item) -> None:
        """Apply Item effects and display message to player

        :param item: Item to be used
        """
        effect = item.used(self)
        self.burden_update()
        mrogue.message.Messenger.add(effect)

    def unequip(self, item, quiet: bool = False, force: bool = False) -> bool:
        """Switch the Item between lists and recalculate related stats

        :param item: Item to be removed
        :param quiet: if feedback should be shown to player
        :param force: if curse check should be ignored
        :return: False if Item can't be removed, True after successful removal
        """
        if item.enchantment_level < 0 and not force:
            mrogue.message.Messenger.add('Cursed items can\'t be unequipped.')
            return False
        item.add(self.inventory)
        item.remove(self.equipped)
        if item.type == mrogue.item.Wearable and item.subtype == 'weapon':
            self.to_hit = self.proficiency + self.ability_bonus
            self.damage_dice = self.default_damage_dice
        elif item.type == mrogue.item.Wearable and item.subtype == 'armor':
            bonus_ac_equipped = sum([i.props.armor_class_modifier for i in self.equipped if i.subtype == 'armor'])
            self.armor_class = 10 + self.abilities['dex'].mod + self.ac_bonus + bonus_ac_equipped
            self.damage_reduction = self.armor_class / 100
        msg = f'{self.name} unequipped {item.name}.'
        if not quiet:
            mrogue.message.Messenger.add(msg)
        return True

    def drop_item(self, item, quiet: bool = False) -> None:
        """Switch an Item between groups and recalculate encumbrance,

        :param item: Item to be removed from inventory
        :param quiet: if feedback to player should be suppressed
        """
        if item.amount > 1:
            item.amount -= 1
            new_item = copy(item)
            new_item.amount = 1
            new_item.dropped(self.pos)
        else:
            item.remove(self.inventory, self.equipped)
            item.dropped(self.pos)
        self.burden_update()
        msg = f'{self.name} dropped {item.name}.'
        if not quiet:
            mrogue.message.Messenger.add(msg)

    def pickup_item(self, item_list: list) -> bool:
        """Transfer the top item from the heap to Unit's inventory

        :param item_list: all Items laying at the spot
        :return: True if an Item was picked up, False if there were no Items
        """
        if item_list:
            item = item_list.pop(0)
            if issubclass(type(item),  mrogue.item.Stackable):
                # in case of Stackables, pick just a singular amount
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
            self.burden_update()
            msg = f'{self.name} picked up {item.name}.'
            mrogue.message.Messenger.add(msg)
            return True
        else:
            msg = 'There are no items here.'
            mrogue.message.Messenger.add(msg)
            return False

    def move(self, success: bool = True) -> None:
        self.moved = success

    def attack(self, target) -> None:
        """Attempt an attack against another Unit

        :param target: the other Unit
        """
        attacker = 'You' if self.player else self.name.capitalize()
        attacked = 'you' if target.player else target.name
        msg = attacker + ' '
        attack_roll = mrogue.utils.roll('1d20')
        critical_hit = attack_roll == 20
        if critical_hit or attack_roll + self.to_hit >= target.armor_class:
            damage_roll = mrogue.utils.roll(self.damage_dice, critical_hit)
            msg += f"{'critically ' if critical_hit else ''}hit{'' if self.player else 's'}"
            mrogue.message.Messenger.add('{} {}.'.format(msg, attacked))
            target.take_damage(damage_roll)
        else:
            if attack_roll == 1:
                msg += f"critically miss{'' if self.player else 'es'}"
            else:
                msg += f"miss{'' if self.player else 'es'}"
            mrogue.message.Messenger.add('{} {}.'.format(msg, attacked))

    def take_damage(self, damage: int) -> None:
        """Remove hit points and check if they go below minimum

        :param damage: The amount of hit points to subtract
        """
        absorption = int(self.damage_reduction * damage)
        damage -= absorption
        self.current_HP -= damage
        if self.current_HP < 1:
            self.die()

    def heal(self, amount: int) -> None:
        """Increase hit points and check if they go over maximum

        :param amount: The amount of hit points to add
        """
        self.current_HP += amount
        if self.current_HP > self.max_HP:
            self.current_HP = self.max_HP

    def die(self) -> None:
        """Remove self from all lists and drop all items on the ground"""
        mrogue.message.Messenger.add(f'{self.name.capitalize()} dies.')
        if not (self.player and 'debug' in argv):
            self.kill()
            if not self.player:
                for item in self.equipped:
                    self.unequip(item, quiet=True, force=True)
                for item in self.inventory:
                    self.drop_item(item, quiet=True)
            self.remove(mrogue.map.Dungeon.current_level.units, mrogue.map.Dungeon.current_level.objects_on_map)
