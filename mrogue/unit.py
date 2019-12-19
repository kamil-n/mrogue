# -*- coding: utf-8 -*-

from sys import argv
import tcod.constants
from mrogue.item import Item, Weapon, Armor, Consumable
from mrogue import Char, roll, cap, die_range


class Unit(Char):
    def __init__(self, name, game, icon, sight_range, speed, to_hit,
                 damage_dice, armor_class, current_hp):
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
        self.moved = False

    def update(self):
        pass

    def load_update(self):
        pass

    def add_item(self, item: Item):
        item.add(self.inventory)
        self.load_update()

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
        if self.player:
            item.identified()
        if not quiet:
            self.game.messenger.add(msg)

    def use(self, item: Consumable):
        effect = item.used(self)
        item.remove(self.inventory)
        self.load_update()
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
        self.load_update()
        msg = '{} dropped {}.'.format(self.name, item.name)
        if not quiet:
            self.game.messenger.add(msg)

    def pickup_item(self, itemlist: list):
        if itemlist:
            item = itemlist.pop(0)
            item.add(self.inventory)
            self.load_update()
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
        min_dmg, max_dmg = die_range(self.damage_dice)
        full_damage = max_dmg - min_dmg + 1
        critical_hit = attack_roll == 20
        if critical_hit or attack_roll + self.to_hit >= target.armor_class:
            damage_roll = roll(self.damage_dice, critical_hit)
            force = damage_roll / full_damage
            verb = 'hit{}'.format('' if self.player else 's')
            if critical_hit:
                msg += 'critically ' + verb
            elif force < 0.34:
                msg += 'barely ' + verb
            elif force < 0.67:
                msg += verb
            else:
                msg += 'accurately ' + verb
            self.game.messenger.add('{} {}.'.format(msg, attacked))
            target.take_damage(damage_roll)
        else:
            if attack_roll == 1:
                msg += 'critically miss{}'.format('' if self.player else 'es')
            else:
                msg += 'miss{}'.format('' if self.player else 'es')
            self.game.messenger.add('{} {}.'.format(msg, attacked))

    def take_damage(self, damage):
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
