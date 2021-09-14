# -*- coding: utf-8 -*-

from sys import argv
import tcod.constants
from mrogue.item import Item, Weapon, Armor, Consumable
from mrogue.utils import *


class AbilityScore:
    def __init__(self, name, score):
        self.name = name
        self._original_score = self.score = score

    @property
    def mod(self):
        return (self.score - 10) // 2


class Unit(Instance):
    def __init__(self, name, game, icon, sight_range, abi_scores, keywords, speed, proficiency,
                 damage_dice, ac_bonus, base_hp_from_dice):
        super().__init__()
        self.player = False
        self.game = game
        self.inventory = []
        self.equipped = []
        self.name = name
        self.pos = game.dungeon.find_spot()
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
        num, sides, mod = decompile_dmg_die(damage_dice)
        self.default_damage_dice = compile_dmg_die(num, sides, mod + self.ability_bonus)  # unarmed attacks
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

    def add_item(self, item: Item):
        item.add(self.inventory)
        self.burden_update()

    def equip(self, item: Weapon or Armor, quiet=False):
        for i in self.equipped:
            if item.slot == i.slot:
                self.unequip(i)
        item.add(self.equipped)
        item.remove(self.inventory)
        if item.type == Weapon:
            self.to_hit = self.proficiency + self.ability_bonus + item.to_hit_modifier
            num, sides, mod = decompile_dmg_die(item.damage)
            self.damage_dice = compile_dmg_die(num, sides, mod + self.ability_bonus)
        elif item.type == Armor:  # TODO: possibly bugged, either here or in unequip()
            bonus_armor_from_equipped = sum([i.armor_class_modifier for i in self.equipped if i.type == Armor])
            self.armor_class = 10 + self.abilities['dex'].mod + self.ac_bonus + bonus_armor_from_equipped
            self.damage_reduction = self.armor_class / 100
        msg = '{} equipped {}.'.format(self.name, item.name)
        if self.player:
            item.identified()
        if not quiet:
            self.game.messenger.add(msg)

    def use(self, item: Consumable):
        effect = item.used(self)
        item.remove(self.inventory)
        self.burden_update()
        self.game.messenger.add(effect)

    def unequip(self, item: Weapon or Armor, quiet=False, force=False):
        if item.enchantment_level < 0 and not force:
            self.game.messenger.add('Cursed items can\'t be unequipped.')
            return False
        item.add(self.inventory)
        item.remove(self.equipped)
        if item.type == Weapon:
            self.to_hit = self.proficiency + self.ability_bonus
            self.damage_dice = self.default_damage_dice
        elif item.type == Armor:
            bonus_armor_from_equipped = sum([i.armor_class_modifier for i in self.equipped if i.type == Armor])
            self.armor_class = 10 + self.abilities['dex'].mod + self.ac_bonus + bonus_armor_from_equipped
            self.damage_reduction = self.armor_class / 100
        msg = '{} unequipped {}.'.format(self.name, item.name)
        if not quiet:
            self.game.messenger.add(msg)
        return True

    def drop_item(self, item: Item, quiet=False):
        item.remove(self.inventory, self.equipped)
        item.dropped(self.pos)
        self.burden_update()
        msg = '{} dropped {}.'.format(self.name, item.name)
        if not quiet:
            self.game.messenger.add(msg)

    def pickup_item(self, itemlist: list):
        if itemlist:
            item = itemlist.pop(0)
            item.add(self.inventory)
            self.burden_update()
            item.picked()
            msg = '{} picked up {}.'.format(self.name, item.name)
            self.game.messenger.add(msg)
            return True
        else:
            msg = 'There are no items here.'
            self.game.messenger.add(msg)
            return False

    def move(self, success=True):
        self.moved = success

    def attack(self, target):
        attacker = 'You' if self.player else cap(self.name)
        attacked = 'you' if target.player else target.name
        msg = attacker + ' '
        attack_roll = roll('1d20')
        critical_hit = attack_roll == 20
        if critical_hit or attack_roll + self.to_hit >= target.armor_class:
            damage_roll = roll(self.damage_dice, critical_hit)
            msg += ('critically ' if critical_hit else '') + 'hit{}'.format('' if self.player else 's')
            self.game.messenger.add('{} {}.'.format(msg, attacked))
            target.take_damage(damage_roll)
        else:
            if attack_roll == 1:
                msg += 'critically miss{}'.format('' if self.player else 'es')
            else:
                msg += 'miss{}'.format('' if self.player else 'es')
            self.game.messenger.add('{} {}.'.format(msg, attacked))

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
        self.game.messenger.add('{} dies.'.format(cap(self.name)))
        if not (self.player and 'debug' in argv):
            self.kill()  # TODO: bugged!
            if not self.player:
                for item in self.equipped:
                    self.unequip(item, quiet=True, force=True)
                for item in self.inventory:
                    self.drop_item(item, quiet=True)
            self.remove(self.game.dungeon.level.units,
                        self.game.dungeon.level.objects_on_map)
