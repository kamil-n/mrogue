# -*- coding: utf-8 -*-

import logging
from rogue import roll


class Player(object):
    game = None
    pos = None
    tile = None
    range = 0
    hit = 0
    damage = ''
    armorClass = 0
    hitpoints = 0
    maxHealth = 0
    control = 'player'

    def __init__(self, game, rng=6):
        self.game = game
        self.pos = game.level.find_spot()
        self.tile = game.interface.tileset[107]
        self.range = rng
        self.hit = 3
        self.damage = "1d6+1"
        self.armorClass = 14
        self.hitPoints = 12
        self.maxHealth = 12
        self.game.interface.print_at(0, 0,
                                     'HP:', self.game.interface.colors['WHITE'])
        self.game.interface.print_at(12, 0,
                                     'AC:', self.game.interface.colors['WHITE'])
        self.game.interface.print_at(21, 0,
                                     'ATK:',
                                     self.game.interface.colors['WHITE'])

    def attack(self, target_monster):
        logging.info('Player attacks %s.' % target_monster.name)
        attack_roll = roll('1d20')
        logging.debug('attack roll = %d + %d' % (attack_roll, self.hit))
        critical_hit = attack_roll == 20
        critical_miss = attack_roll == 1
        if critical_hit or attack_roll + self.hit >= target_monster.armorClass:
            if critical_hit:
                logging.debug('Critical hit.')
                self.game.messenger.add(
                    'You critically hit %s.' % target_monster.name)
            else:
                logging.debug('Attack hit.')
                self.game.messenger.add('You hit %s.' % target_monster.name)
            damage_roll = roll(self.damage, critical_hit)
            logging.debug('damage roll = %d' % damage_roll)
            target_monster.take_damage(damage_roll)
        else:
            if critical_miss:
                logging.debug('Critical miss')
                self.game.messenger.add(
                    'You critically missed %s.' % target_monster.name)
            else:
                logging.debug('Attack missed')
                self.game.messenger.add('You missed %s.' % target_monster.name)

    def take_damage(self, damage):
        logging.debug('Player is taking %d damage.' % damage)
        self.hitPoints -= damage
        if self.hitPoints < 1:
            logging.info('Player dies. (%d hp)' % self.hitPoints)
            self.game.messenger.add('You die.')
        else:
            logging.debug('current hit points: %d.' % self.hitPoints)

    def draw(self):
        self.game.interface.print_at(self.pos[0], self.pos[1], self.tile)

    def show_status(self):
        self.game.interface.print_at(2, 0, '%2d/%d' % (
                                         self.hitPoints, self.maxHealth),
                                     self.game.interface.colors['WHITE'])
        self.game.interface.print_at(14, 0, '%2d' % self.armorClass,
                                     self.game.interface.colors['WHITE'])
        self.game.interface.print_at(23, 0, '%d/%s' % (self.hit, self.damage),
                                     self.game.interface.colors['WHITE'])
