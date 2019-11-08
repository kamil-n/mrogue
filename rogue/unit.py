# -*- coding: utf-8 -*-

import logging
from sys import argv
from pygame import sprite
from rogue.item import Item, Weapon, Armor
from rogue import roll


class Unit(sprite.Sprite):
    def __init__(self, name, game, tile_id, sight_range, to_hit, damage_dice,
                 armor_class, current_hp):
        super().__init__()
        self.game = game
        self.log = logging.getLogger(__name__)
        self.inventory = sprite.Group()
        self.equipped = sprite.Group()
        self.name = name
        self.pos = game.level.find_spot()
        self.image_no_equip = game.interface.tileset[tile_id].copy()
        self.image = self.image_no_equip.copy()
        self.rect = self.image.get_rect()
        self.sight_range = sight_range
        self.base_to_hit = to_hit  # i.e. from Strength or size
        self.to_hit = self.base_to_hit
        self.default_damage_dice = damage_dice  # inherent (unarmed / natural attacks)
        self.damage_dice = self.default_damage_dice
        self.base_armor_class = armor_class  # i.e. from Dexterity or natural
        self.armor_class = self.base_armor_class
        self.current_HP = current_hp
        self.max_HP = current_hp

    def update(self):
        self.rect.topleft = (self.pos[0] * 32, self.pos[1] * 32)

    def add_item(self, item: Item):
        item.add(self.inventory)
        self.log.debug('{} received {}.'.format(self.name, item.full_name))

    def equip(self, item: Weapon or Armor, quiet=False):
        item.add(self.equipped)
        if item.type == Weapon:
            self.to_hit += item.to_hit_modifier
            self.damage_dice = item.damage_string
        elif item.type == Armor:
            self.armor_class += item.armor_class_modifier
        for icon in item.icon['equip']:
            self.image.blit(icon, (0, 0))
        msg = '{} equipped {}.'.format(self.name, item.full_name)
        item.remove(self.inventory)
        if not quiet:
            self.game.messenger.add(msg)
        self.log.debug(msg)

    def unequip(self, item: Weapon or Armor, quiet=False):
        item.add(self.inventory)
        if item.type == Weapon:
            self.to_hit -= item.to_hit_modifier  # TODO: should recalculate
            self.damage_dice = self.default_damage_dice
        elif item.type == Armor:
            self.armor_class -= item.armor_class_modifier  # TODO: ditto
        self.image = self.image_no_equip.copy()
        msg = '{} unequipped {}.'.format(self.name, item.full_name)
        item.remove(self.equipped)
        for item in self.equipped:
            for icon in item.icon['equip']:
                self.image.blit(icon, (0, 0))
        if not quiet:
            self.game.messenger.add(msg)
        self.log.debug(msg)

    def drop_item(self, item: Item):
        item.remove((self.inventory, self.equipped))
        self.log.debug('{} dropped {}.'.format(self.name, item.full_name))

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
                self.game.messenger.add('{} critically hits {}.'.format(uname, target.name))
            else:
                self.log.debug('Attack hit.')
                self.game.messenger.add('{} hits {}.'.format(uname, target.name))
            damage_roll = roll(self.damage_dice, critical_hit)
            self.log.debug('damage roll = %d' % damage_roll)
            target.take_damage(damage_roll)
        else:
            if critical_miss:
                self.log.debug('Critical miss')
                self.game.messenger.add('{} critically misses {}.'.format(uname, target.name))
            else:
                self.log.debug('Attack missed')
                self.game.messenger.add('{} misses {}.'.format(uname, target.name))

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
        self.game.messenger.add('{} dies.'.format(str.upper(self.name[0]) + self.name[1:]))
        if not (self.name == 'Player' and 'god' in argv):
            self.kill()
