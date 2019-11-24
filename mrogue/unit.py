# -*- coding: utf-8 -*-

import logging
from sys import argv
import tcod.constants
from mrogue.console import Char
from mrogue.item import Item, Weapon, Armor
from mrogue import roll


class Unit(Char):
    def __init__(self, name, game, icon, sight_range, to_hit, damage_dice,
                 armor_class, current_hp):
        super().__init__()
        self.game = game
        self.log = logging.getLogger(__name__)
        self.inventory = []
        self.equipped = []
        self.name = name
        self.pos = game.level.find_spot()
        self.icon = icon[0]
        self.color = vars(tcod.constants)[icon[1]]
        self.layer = 1
        self.sight_range = sight_range
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
        self.log.debug('{} received {}.'.format(self.name,
                                                item.identified_name))

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
        self.log.debug(msg)

    def unequip(self, item: Weapon or Armor, quiet=False):
        if item.enchantment_level < 0:
            self.log.warning('{} tried to unequip cursed item! {}'.format(
                self.name, item.identified_name))
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
        self.log.debug(msg)

    def drop_item(self, item: Item, quiet=False):
        item.remove(self.inventory, self.equipped)
        item.dropped(self.pos)
        msg = '{} dropped {}.'.format(self.name, item.name)
        if not quiet:
            self.game.messenger.add(msg)
        self.log.debug(msg)

    def pickup_item(self, itemlist: list):
        if itemlist:
            item = itemlist.pop(0)
            item.add(self.inventory)
            item.picked()
            msg = '{} picked up {}.'.format(self.name, item.name)
            self.game.messenger.add(msg)
            self.log.debug(msg)
            return True
        else:
            msg = 'There are no items here.'
            self.game.messenger.add(msg)
            return False

    def attack(self, target):
        uname = str.upper(self.name[0]) + self.name[1:]
        self.log.info('{} attacks {}.'.format(uname, target.name))
        attack_roll = roll('1d20')
        self.log.debug('attack roll = %d + %d' % (attack_roll, self.to_hit))
        critical_hit = attack_roll == 20
        critical_miss = attack_roll == 1
        if critical_hit or attack_roll + self.to_hit >= target.armor_class:
            if critical_hit:
                self.log.debug('Critical hit.')
                self.game.messenger.add('{} critically hits {}.'.format(
                    uname, target.name))
            else:
                self.log.debug('Attack hit.')
                self.game.messenger.add('{} hits {}.'.format(
                    uname, target.name))
            damage_roll = roll(self.damage_dice, critical_hit)
            self.log.debug('damage roll = %d' % damage_roll)
            target.take_damage(damage_roll)
        else:
            if critical_miss:
                self.log.debug('Critical miss')
                self.game.messenger.add('{} critically misses {}.'.format(
                    uname, target.name))
            else:
                self.log.debug('Attack missed')
                self.game.messenger.add('{} misses {}.'.format(
                    uname, target.name))

    def take_damage(self, damage):
        self.log.debug('{} is taking {} damage.'.format(
            str.upper(self.name[0]) + self.name[1:], damage))
        self.current_HP -= damage
        if self.current_HP < 1:
            self.die()
        else:
            self.log.debug('current hit points: %d.' % self.current_HP)

    def die(self):
        self.log.info('{} dies. ({} hp)'.format(self.name, self.current_HP))
        self.game.messenger.add('{} dies.'.format(
            str.upper(self.name[0]) + self.name[1:]))
        if not (self.name == 'Player' and 'debug' in argv):
            self.kill()  # TODO: bugged!
            if not self.name == 'Player':
                for item in self.equipped:
                    self.unequip(item, quiet=True)
                for item in self.inventory:
                    self.drop_item(item, quiet=True)
            self.remove(self.game.level.units, self.game.level.objects_on_map,
                        self.game.monsters.monsterList)
