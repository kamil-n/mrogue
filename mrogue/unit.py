# -*- coding: utf-8 -*-

from sys import argv
import tcod.constants
from mrogue.item import Item, Weapon, Armor, Consumable
from mrogue import Char, roll


class Unit(Char):
    def __init__(self, name, game, icon, sight_range, speed, to_hit,
                 damage_dice, armor_class, current_hp):
        super().__init__()
        self.game = game
        self.inventory = []
        self.equipped = []
        self.name = name
        self.pos = game.dungeon.find_spot()
        self.icon = icon[0]
        self.color = vars(tcod.constants)[icon[1]]
        self.layer = 1
        self.sight_range = sight_range
        self.load_thresholds = (5.0, 30.0, 50.0)
        self.speed = speed
        self.ticks_left = int(speed * 100)
        self.base_to_hit = to_hit  # i.e. from Strength or size
        self.to_hit = self.base_to_hit
        self.default_damage_dice = damage_dice  # unarmed attacks
        self.damage_dice = self.default_damage_dice
        self.base_armor_class = armor_class  # i.e. from Dexterity or natural
        self.armor_class = self.base_armor_class
        self.current_HP = current_hp
        self.max_HP = current_hp
        self.last_pos = self.pos
        self.moved = False

    def update(self):
        self.moved = self.pos != self.last_pos
        self.last_pos = self.pos

    def add_item(self, item: Item):
        item.add(self.inventory)

    def equip(self, item: Weapon or Armor, quiet=False):
        for i in self.equipped:
            if item.slot == i.slot:
                self.unequip(i)
        item.add(self.equipped)
        if item.type == Weapon:
            self.to_hit += item.to_hit_modifier
            self.damage_dice = item.damage
        elif item.type == Armor:
            self.armor_class += item.armor_class_modifier
        msg = '{} equipped {}.'.format(self.name, item.name)
        item.remove(self.inventory)
        if self.name == 'Player':
            item.identified()
        if not quiet:
            self.game.messenger.add(msg)

    def use(self, item: Consumable):
        effect = item.used(self)
        item.remove(self.inventory)
        self.game.messenger.add(effect)

    def unequip(self, item: Weapon or Armor, quiet=False, force=False):
        if item.enchantment_level < 0 and not force:
            self.game.messenger.add('Cursed items can\'t be unequipped.')
            return False
        item.add(self.inventory)
        if item.type == Weapon:
            self.to_hit -= item.to_hit_modifier  # TODO: should recalculate
            self.damage_dice = self.default_damage_dice
        elif item.type == Armor:
            self.armor_class -= item.armor_class_modifier  # TODO: ditto
        msg = '{} unequipped {}.'.format(self.name, item.name)
        item.remove(self.equipped)
        if not quiet:
            self.game.messenger.add(msg)
        return True

    def drop_item(self, item: Item, quiet=False):
        item.remove(self.inventory, self.equipped)
        item.dropped(self.pos)
        msg = '{} dropped {}.'.format(self.name, item.name)
        if not quiet:
            self.game.messenger.add(msg)

    def pickup_item(self, itemlist: list):
        if itemlist:
            item = itemlist.pop(0)
            item.add(self.inventory)
            item.picked()
            msg = '{} picked up {}.'.format(self.name, item.name)
            self.game.messenger.add(msg)
            return True
        else:
            msg = 'There are no items here.'
            self.game.messenger.add(msg)
            return False

    def attack(self, target):
        uname = str.upper(self.name[0]) + self.name[1:]
        attack_roll = roll('1d20')
        critical_hit = attack_roll == 20
        critical_miss = attack_roll == 1
        if critical_hit or attack_roll + self.to_hit >= target.armor_class:
            if critical_hit:
                self.game.messenger.add('{} critically hits {}.'.format(
                    uname, target.name))
            else:
                self.game.messenger.add('{} hits {}.'.format(
                    uname, target.name))
            damage_roll = roll(self.damage_dice, critical_hit)
            target.take_damage(damage_roll)
        else:
            if critical_miss:
                self.game.messenger.add('{} critically misses {}.'.format(
                    uname, target.name))
            else:
                self.game.messenger.add('{} misses {}.'.format(
                    uname, target.name))

    def take_damage(self, damage):
        self.current_HP -= damage
        if self.current_HP < 1:
            self.die()

    def die(self):
        self.game.messenger.add('{} dies.'.format(
            str.upper(self.name[0]) + self.name[1:]))
        if not (self.name == 'Player' and 'debug' in argv):
            self.kill()  # TODO: bugged!
            if not self.name == 'Player':
                for item in self.equipped:
                    self.unequip(item, quiet=True, force=True)
                for item in self.inventory:
                    self.drop_item(item, quiet=True)
            self.remove(self.game.level.units, self.game.level.objects_on_map)
