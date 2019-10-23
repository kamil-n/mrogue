# -*- coding: utf-8 -*-

import logging
import random
from rogue import roll


class Menagerie(object):
    game = None
    monsterList = []

    def __init__(self, game, num):
        self.game = game
        monster_templates = [MonsterTemplate('rat', 'r',
                                             game.interface.colors[
                                                 'DARKGRAY'],
                                             '1d4-1', '1d4-1', 2, 12),
                             MonsterTemplate('kobold', 'k',
                                             game.interface.colors['RED'],
                                             '1d6-1', '1d6-1', 1, 13),
                             MonsterTemplate('goblin', 'g',
                                             game.interface.colors['GREEN'],
                                             '1d6-1', '1d8-1', 2, 13),
                             MonsterTemplate('orc', 'o',
                                             game.interface.colors[
                                                 'DARKGREEN'],
                                             '1d8', '1d8', 3, 14),
                             MonsterTemplate('skeleton', 's',
                                             game.interface.colors['WHITE'],
                                             '1d8', '1d4+1', 3, 11)]
        for i in range(num):
            start_position = game.level.find_spot()
            temp_monster = Monster(self.game, start_position,
                                   random.choice(monster_templates))
            self.monsterList.append(temp_monster)
            logging.debug('Created monster %s at %d,%d' % (temp_monster.name,
                                                           temp_monster.pos[0],
                                                           temp_monster.pos[1]))

    def handle_monsters(self):
        for monster in self.monsterList:
            if monster.is_in_range(self.game.player.pos, 5):
                if self.game.level.is_los_between(monster.pos,
                                                  self.game.player.pos):
                    if monster.is_in_range(self.game.player.pos, 1):
                        logging.debug('%s is in melee range - attacking' %
                                      monster.name)
                        monster.attack(self.game.player.armorClass)
                    else:
                        monster.approach(self.game.player.pos)
        return len(self.monsterList) > 0


class MonsterTemplate(object):
    def __init__(self, name, letter, color, hit_die, dmg_die, to_hit, ac):
        self.name = name
        self.letter = letter
        self.color = color
        self.hitDie = hit_die
        self.dmgDie = dmg_die
        self.toHit = to_hit
        self.armorClass = ac


class Monster(object):
    game = None
    name = ''
    letter = 0
    color = None
    pos = None
    hit = 0
    damage = ''
    armorClass = 0
    hitPoints = 0
    control = 'ai'

    def __init__(self, game, pos, template):
        self.game = game
        self.name = template.name
        self.letter = template.letter
        self.color = template.color
        self.pos = pos
        self.hit = template.toHit
        self.damage = template.dmgDie
        self.armorClass = template.armorClass
        self.hitPoints = roll(template.hitDie)

    def take_damage(self, damage):
        logging.debug('%s is taking %d damage.' % (self.name, damage))
        self.hitPoints -= damage
        if self.hitPoints < 1:
            self.die()
        else:
            logging.debug('current hit points: %d.' % self.hitPoints)

    def die(self):
        logging.info('%s dies. (%d hp)' % (self.name, self.hitPoints))
        self.game.messenger.add(
            '%s dies.' % (str.upper(self.name[0]) + self.name[1:]))
        Menagerie.monsterList.remove(self)

    def attack(self, target_ac):
        logging.info('%s attacks player.' % self.name)
        attack_roll = roll('1d20')
        logging.debug('attack roll = %d + %d' % (attack_roll, self.hit))
        critical_hit = attack_roll == 20
        critical_miss = attack_roll == 1
        if critical_hit or attack_roll + self.hit >= target_ac:
            if critical_hit:
                logging.debug('Critical hit.')
                self.game.messenger.add('%s critically hits you.' % (
                        str.upper(self.name[0]) + self.name[1:]))
            else:
                logging.debug('Attack hit.')
                self.game.messenger.add('%s hits you.' % (
                        str.upper(self.name[0]) + self.name[1:]))
            damage_roll = roll(self.damage, critical_hit)
            logging.debug('damage roll = %d' % damage_roll)
            self.game.player.take_damage(damage_roll)
        else:
            if critical_miss:
                logging.debug('Critical miss')
                self.game.messenger.add('%s critically misses you.' % (
                        str.upper(self.name[0]) + self.name[1:]))
            else:
                logging.debug('Attack missed')
                self.game.messenger.add('%s misses you.' % (
                        str.upper(self.name[0]) + self.name[1:]))

    def is_in_range(self, target_position, radius):
        return abs(self.pos[0] - target_position[0]) <= radius and \
               abs(self.pos[1] - target_position[1]) <= radius

    def approach(self, goal):
        difx = goal[0] - self.pos[0]
        dify = goal[1] - self.pos[1]
        vertical = abs(dify) > abs(difx)
        if vertical:
            if difx == 0:
                success = self.game.level.movement(self,
                                                   (0,
                                                    int(dify / abs(dify))))
                if not success:
                    success = self.game.level.movement(self,
                                                       (-1,
                                                        int(dify / abs(
                                                            dify))))
                    if not success:
                        self.game.level.movement(self,
                                                 (1,
                                                  int(dify / abs(dify))))
            else:
                success = self.game.level.movement(self,
                                                   (int(difx / abs(difx)),
                                                    int(dify / abs(dify))))
                if not success:
                    success = self.game.level.movement(self,
                                                       (0,
                                                        int(dify / abs(
                                                            dify))))
                    if not success:
                        self.game.level.movement(self,
                                                 (-1 * int(difx / abs(difx)),
                                                  int(dify / abs(dify))))
        else:
            if dify == 0:
                success = self.game.level.movement(self,
                                                   (int(difx / abs(difx)),
                                                    0))
                if not success:
                    success = self.game.level.movement(self,
                                                       (
                                                           int(difx / abs(
                                                               difx)),
                                                           -1))
                    if not success:
                        self.game.level.movement(self,
                                                 (int(difx / abs(difx)),
                                                  1))
            else:
                success = self.game.level.movement(self,
                                                   (int(difx / abs(difx)),
                                                    int(dify / abs(dify))))
                if not success:
                    success = self.game.level.movement(self,
                                                       (
                                                           int(difx / abs(
                                                               difx)),
                                                           0))
                    if not success:
                        self.game.level.movement(self,
                                                 (int(difx / abs(difx)),
                                                  -1 * int(
                                                      dify / abs(dify))))
