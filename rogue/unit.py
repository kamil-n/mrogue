# -*- coding: utf-8 -*-

import logging
from rogue import roll


class Unit(object):
    game = None
    name = ''
    tile = None
    pos = None
    to_hit = 0
    sight_range = 0
    damage_dice = ''
    armor_class = 0
    current_HP = 0
    max_HP = 0

    def __init__(self, name, game, tile_id, sight_range, to_hit, damage_dice, armor_class, current_hp, container=None):
        self.game = game
        self.name = name
        self.pos = game.level.find_spot()
        self.tile = game.interface.tileset[tile_id].copy()
        self.sight_range = sight_range
        self.to_hit = to_hit
        self.damage_dice = damage_dice
        self.armor_class = armor_class
        self.current_HP = current_hp
        self.max_HP = current_hp
        if container:
            self.container = container

    def attack(self, target):
        uname = str.upper(self.name[0]) + self.name[1:]
        logging.info('{} attacks {}.'.format(uname, target.name))
        attack_roll = roll('1d20')
        logging.debug('attack roll = %d + %d' % (attack_roll, self.to_hit))
        critical_hit = attack_roll == 20
        critical_miss = attack_roll == 1
        if critical_hit or attack_roll + self.to_hit >= target.armor_class:
            if critical_hit:
                logging.debug('Critical hit.')
                self.game.messenger.add('{} critically hits {}.'.format(
                    uname, target.name))
            else:
                logging.debug('Attack hit.')
                self.game.messenger.add('{} hits {}.'.format(
                    uname, target.name))
            damage_roll = roll(self.damage_dice, critical_hit)
            logging.debug('damage roll = %d' % damage_roll)
            target.take_damage(damage_roll)
        else:
            if critical_miss:
                logging.debug('Critical miss')
                self.game.messenger.add('{} critically misses {}.'.format(
                    uname, target.name))
            else:
                logging.debug('Attack missed')
                self.game.messenger.add('{} misses {}.'.format(
                    uname, target.name))

    def take_damage(self, damage):
        logging.debug('{} is taking {} damage.'.format(
            str.upper(self.name[0]) + self.name[1:], damage))
        self.current_HP -= damage
        if self.current_HP < 1:
            self.die()
        else:
            logging.debug('current hit points: %d.' % self.current_HP)

    def die(self):
        logging.info('{} dies. ({} hp)'.format(self.name, self.current_HP))
        self.game.messenger.add('{} dies.'.format(str.upper(self.name[0]) + self.name[1:]))
        if self.name != 'Player':
            from rogue.monster import Menagerie
            Menagerie.monsterList.remove(self)
