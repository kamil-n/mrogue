# -*- coding: utf-8 -*-

import json
import logging
import random
from pygame import sprite
from rogue import roll
import rogue.unit


class Menagerie(object):
    game = None
    monsterList = sprite.Group()

    def __init__(self, game, num):
        self.game = game
        with open('rogue/monster_templates.json') as f:
            monster_templates = json.loads(f.read())
        for i in range(num):
            Monster(self.game, random.choice(monster_templates),
                    (self.monsterList, game.interface.objects_on_map))

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

    def __init__(self, game, template, groups):
        super().__init__(template['name'], game, template['tile'], 5,
                         template['to_hit'], template['dmg_die'],
                         template['ac'], roll(template['hit_die']))
        if 'wields' in template:
            self.image.blit(game.interface.tileset[template['wields']], (-2, 6))
        self.add(groups)
        logging.debug('Created monster {} at {},{}'.format(
            self.name, self.pos[0], self.pos[1]))

    def is_in_range(self, target_position):
        return abs(self.pos[0] - target_position[0]) <= self.sight_range and \
               abs(self.pos[1] - target_position[1]) <= self.sight_range

    def approach(self, goal):
        difx = goal[0] - self.pos[0]
        dify = goal[1] - self.pos[1]
        vertical = abs(dify) > abs(difx)
        if vertical:
            if difx == 0:
                success = self.game.level.movement(self, (0, int(dify / abs(dify))))
                if not success:
                    success = self.game.level.movement(self, (-1, int(dify / abs(dify))))
                    if not success:
                        self.game.level.movement(self, (1, int(dify / abs(dify))))
            else:
                success = self.game.level.movement(self, (int(difx / abs(difx)), int(dify / abs(dify))))
                if not success:
                    success = self.game.level.movement(self, (0, int(dify / abs(dify))))
                    if not success:
                        self.game.level.movement(self, (-1 * int(difx / abs(difx)), int(dify / abs(dify))))
        else:
            if dify == 0:
                success = self.game.level.movement(self, (int(difx / abs(difx)), 0))
                if not success:
                    success = self.game.level.movement(self, (int(difx / abs(difx)), -1))
                    if not success:
                        self.game.level.movement(self, (int(difx / abs(difx)), 1))
            else:
                success = self.game.level.movement(self, (int(difx / abs(difx)), int(dify / abs(dify))))
                if not success:
                    success = self.game.level.movement(self, (int(difx / abs(difx)), 0))
                    if not success:
                        self.game.level.movement(self, (int(difx / abs(difx)), -1 * int(dify / abs(dify))))
