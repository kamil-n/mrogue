# -*- coding: utf-8 -*-

import logging
from rogue import roll
from rogue.map import RogueMap
from rogue.curse import CursesHelper as Curses
from rogue.message import Messenger


class Player:
    _instance = None
    pos = None
    color = None
    range = 0
    hit = 0
    damage = ''
    armorClass = 0
    hitpoints = 0
    maxHealth = 0
    control = 'player'

    def __init__(self, rng=6):
        self.pos = RogueMap.find_spot()
        self.color = Curses.color('YELLOW')
        self.range = rng
        self.hit = 3
        self.damage = "1d6+1"
        self.armorClass = 14
        self.hitPoints = 12
        self.maxHealth = 12
        Player._instance = self

    @classmethod
    def get_pos(cls):
        return cls._instance.pos

    @classmethod
    def get_ac(cls):
        return cls._instance.armorClass

    def attack(self, target_monster):
        logging.info('Player attacks %s.' % target_monster.name)
        attack_roll = roll('1d20')
        logging.debug('attack roll = %d + %d' % (attack_roll, self.hit))
        critical_hit = attack_roll == 20
        critical_miss = attack_roll == 1
        if critical_hit or attack_roll + self.hit >= target_monster.armorClass:
            if critical_hit:
                logging.debug('Critical hit.')
                Messenger.add('You critically hit %s.' % target_monster.name)
            else:
                logging.debug('Attack hit.')
                Messenger.add('You hit %s.' % target_monster.name)
            damage_roll = roll(self.damage, critical_hit)
            logging.debug('damage roll = %d' % damage_roll)
            target_monster.take_damage(damage_roll)
        else:
            if critical_miss:
                logging.debug('Critical miss')
                Messenger.add('You critically missed %s.' % target_monster.name)
            else:
                logging.debug('Attack missed')
                Messenger.add('You missed %s.' % target_monster.name)

    @classmethod
    def take_damage(cls, damage):
        logging.debug('Player is taking %d damage.' % damage)
        cls._instance.hitPoints -= damage
        if cls._instance.hitPoints < 1:
            logging.info('Player dies. (%d hp)' % cls._instance.hitPoints)
            Messenger.add('You die.')
        else:
            logging.debug('current hit points: %d.' % cls._instance.hitPoints)

    def show_status(self, status_line):
        Curses.print_at(4, status_line, '%2d/%d' %
                        (self.hitPoints, self.maxHealth), Curses.color('GREEN'))
        Curses.print_at(16, status_line, '%2d' %
                        self.armorClass, Curses.color('LIGHTBLUE'))
        Curses.print_at(26, status_line, '%d/%s' %
                        (self.hit, self.damage), Curses.color('RED'))
