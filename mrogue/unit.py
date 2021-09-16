# -*- coding: utf-8 -*-

from copy import copy
from sys import argv
import tcod.constants
import mrogue.item
import mrogue.map
import mrogue.message
import mrogue.utils


class AbilityScore:
    def __init__(self, name, score):
        self.name = name
        self._original_score = self.score = score

    @property
    def mod(self):
        return (self.score - 10) // 2


class Unit(mrogue.Entity):
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
        num, sides, mod = mrogue.utils.decompile_dmg_die(damage_dice)
        self.default_damage_dice = mrogue.utils.compile_dmg_die(num, sides, mod + self.ability_bonus)  # unarmed attacks
        self.damage_dice = self.default_damage_dice
        self.base_armor_class = 10 + self.abilities['dex'].mod
        self.ac_bonus = ac_bonus
        self.armor_class = self.base_armor_class + self.ac_bonus
        self.damage_reduction = self.armor_class / 100
        self.current_HP = base_hp_from_dice + self.abilities['con'].mod
        self.max_HP = base_hp_from_dice
        self.moved = False

    def update(self):
        pass

    def burden_update(self):
        pass

    def add_item(self, item):
        item.add(self.inventory)
        self.burden_update()

    def equip(self, item, quiet=False):
        for i in self.equipped:
            if item.slot == i.slot:
                self.unequip(i)
        item.add(self.equipped)
        item.remove(self.inventory)
        if item.type == mrogue.item.Wearable and item.subtype == 'weapon':
            self.to_hit = self.proficiency + self.ability_bonus + item.props.to_hit_modifier
            num, sides, mod = mrogue.utils.decompile_dmg_die(item.props.damage)
            self.damage_dice = mrogue.utils.compile_dmg_die(num, sides, mod + self.ability_bonus)
        elif item.type == mrogue.item.Wearable and item.subtype == 'armor':
            bonus_ac_equipped = sum([i.props.armor_class_modifier for i in self.equipped if i.subtype == 'armor'])
            self.armor_class = 10 + self.abilities['dex'].mod + self.ac_bonus + bonus_ac_equipped
            self.damage_reduction = self.armor_class / 100
        msg = f'{self.name} equipped {item.name}.'
        if self.player:
            item.identified()
        if not quiet:
            mrogue.message.Messenger.add(msg)

    def use(self, item):
        effect = item.used(self)
        self.burden_update()
        mrogue.message.Messenger.add(effect)

    def unequip(self, item, quiet=False, force=False):
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

    def drop_item(self, item, quiet=False):
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

    def pickup_item(self, item_list: list):
        if item_list:
            item = item_list.pop(0)
            if issubclass(type(item),  mrogue.item.Stackable):
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

    def move(self, success=True):
        self.moved = success

    def attack(self, target):
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

    def take_damage(self, damage):
        absorption = int(self.damage_reduction * damage)
        damage -= absorption
        self.current_HP -= damage
        if self.current_HP < 1:
            self.die()

    def heal(self, amount):
        self.current_HP += amount
        if self.current_HP > self.max_HP:
            self.current_HP = self.max_HP

    def die(self):
        mrogue.message.Messenger.add(f'{self.name.capitalize()} dies.')
        if not (self.player and 'debug' in argv):
            self.kill()
            if not self.player:
                for item in self.equipped:
                    self.unequip(item, quiet=True, force=True)
                for item in self.inventory:
                    self.drop_item(item, quiet=True)
            self.remove(mrogue.map.Dungeon.current_level.units, mrogue.map.Dungeon.current_level.objects_on_map)
