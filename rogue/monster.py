# -*- coding: utf-8 -*-

import logging
import random
from rogue import roll
import rogue.unit


class Menagerie(object):
    game = None
    monsterList = []

    def __init__(self, game, num):
        self.game = game
        monster_templates = [
            {
                'name': 'rat',
                'tile': 255,
                'hit_die': '1d4-1',
                'dmg_die': '1d4-1',
                'to_hit': 2,
                'ac': 12
            },
            {
                'name': 'kobold',
                'tile': 467,
                'wields': 491,
                'hit_die': '1d6-1',
                'dmg_die': '1d6-1',
                'to_hit': 1,
                'ac': 13
            },
            {
                'name': 'goblin',
                'tile': 119,
                'wields': 491,
                'hit_die': '1d6-1',
                'dmg_die': '1d8-1',
                'to_hit': 2,
                'ac': 13
            },
            {
                'name': 'orc',
                'tile': 179,
                'wields': 484,
                'hit_die': '1d8',
                'dmg_die': '1d8',
                'to_hit': 3,
                'ac': 14
            },
            {
                'name': 'skeleton',
                'tile': 521,
                'wields': 488,
                'hit_die': '1d8',
                'dmg_die': '1d4+1',
                'to_hit': 3,
                'ac': 11
            }
        ]
        for i in range(num):
            temp_monster = Monster(self.game, random.choice(monster_templates))
            self.monsterList.append(temp_monster)
            logging.debug('Created monster {} at {},{}'.format(
                temp_monster.name, temp_monster.pos[0], temp_monster.pos[1]))

    def handle_monsters(self):
        for monster in self.monsterList:
            if monster.is_in_range(self.game.player.pos):
                if self.game.level.is_los_between(monster.pos,
                                                  self.game.player.pos):
                    if abs(monster.pos[0] - self.game.player.pos[0]) <= 1 and \
                            abs(monster.pos[1] - self.game.player.pos[1]) <= 1:
                        logging.debug('%s is in melee range - attacking' %
                                      monster.name)
                        monster.attack(self.game.player)
                    else:
                        monster.approach(self.game.player.pos)


class Monster(rogue.unit.Unit):

    def __init__(self, game, template):
        super().__init__(template['name'], game, template['tile'], 5,
                         template['to_hit'], template['dmg_die'],
                         template['ac'], roll(template['hit_die']))
        if 'wields' in template:
            self.tile.blit(game.interface.tileset[template['wields']], (-2, 6))

    def is_in_range(self, target_position):
        return abs(self.pos[0] - target_position[0]) <= self.sight_range and \
               abs(self.pos[1] - target_position[1]) <= self.sight_range

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
