# -*- coding: utf-8 -*-
"""
Module to support items (equipment) implementation.
Attributes:
    slots (dict): list of (body) slots where an item can be equipped

"""

import logging
from json import loads
from os import path
import pygame
import random
from rogue import decompile_dmg_die, compile_dmg_die
from rogue.pgame import PygameWindow

slots = {
    # 'head': 1,
    # 'neck': 1,
    'torso': 1,
    # 'waist': 1,
    # 'wrist': 2,
    'hand': 2,
    # 'finger': 10,
    # 'legs': 1,
    # 'foot': 2
}

quality_levels = {
    -2: 'broken',
    -1: 'flimsy',
    0: '',
    1: 'masterwork',
    2: 'extraordinary'
}

enchantment_levels = {
    -1: 'cursed',
    0: '',
    1: 'blessed'
}


class ItemManager(object):
    game = None
    loot = pygame.sprite.Group()
    templates = pygame.sprite.Group()
    item_templates = {}

    def __init__(self, game, num):
        self.game = game
        basedir = path.dirname(path.abspath(__file__))
        with open(path.join(basedir, 'item_templates.json')) as f:
            templates_file = loads(f.read())
        for category, category_dict in templates_file.items():
            self.item_templates[category] = {}
            for type, type_list in category_dict.items():
                self.item_templates[category][type] = []
                for item in type_list:
                    new_item = None
                    if category == 'weapons':
                        new_item = Weapon(self.game, item, self.templates)
                    elif category == 'armor':
                        new_item = Armor(self.game, item, self.templates)
                    self.item_templates[category][type].append(new_item)

    def show_inventory(self):
        window = PygameWindow(self.game.interface, 4, 4, 20, 3 + len(self.game.player.inventory), 'Inventory')
        window.print_at(2, 1, 'Press a letter or Esc to close:')
        for i, item in enumerate(self.game.player.inventory):
            window.print_at(1, 3 + i, item.icon['inv'])
            summary = '{}) {} ('.format(chr(i+97), item.full_name)
            if item.type == Weapon:
                summary += '{:+d}/{})'.format(item.to_hit_modifier, item.damage_string)
            elif item.type == Armor:
                summary += '{:+d})'.format(item.armor_class_modifier)
            window.print_at(2, 3 + i, summary)
        self.game.interface.screen.blit(window, (window.left, window.top))
        self.game.interface.refresh()
        pygame.event.clear()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                self.game.interface.close()
            elif event.type == pygame.KEYDOWN:
                last_letter = 96 + len(self.game.player.inventory)
                if event.key == 27:
                    break
                elif event.key in range(97, last_letter + 1):
                    logging.debug('Selected valid key {} from a-{}'.format(chr(event.key), chr(last_letter)))
                    self.game.player.equip(list(self.game.player.inventory)[event.key-97])
                    break
                else:
                    logging.debug('Selected wrong key {} ({}?)'.format(event.key, chr(event.key)))

    def show_equipment(self):
        window = PygameWindow(self.game.interface, 4, 4, 20,
                              3 + len(self.game.player.equipped), 'Equipped items')
        window.print_at(2, 1, 'Press a letter or Esc to close:')
        for i, item in enumerate(self.game.player.equipped):
            window.print_at(1, 3 + i, item.icon['inv'])
            summary = '{}) {} ('.format(chr(i + 97), item.full_name)
            if item.type == Weapon:
                summary += '{:+d}/{})'.format(item.to_hit_modifier,
                                              item.damage_string)
            elif item.type == Armor:
                summary += '{:+d})'.format(item.armor_class_modifier)
            window.print_at(2, 3 + i, summary)
        self.game.interface.screen.blit(window, (window.left, window.top))
        self.game.interface.refresh()
        pygame.event.clear()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                self.game.interface.close()
            elif event.type == pygame.KEYDOWN:
                last_letter = 96 + len(self.game.player.equipped)
                if event.key == 27:
                    break
                elif event.key in range(97, last_letter + 1):
                    logging.debug('Selected valid key {} from a-{}'.format(chr(event.key), chr(last_letter)))
                    self.game.player.unequip(list(self.game.player.equipped)[event.key - 97])
                    break
                else:
                    logging.debug('Selected wrong key {} ({}?)'.format(event.key, chr(event.key)))


class Item(pygame.sprite.Sprite):
    """ Generic item class to hold universal data and methods.

    """
    def __init__(self, parent, name, material, base_weight, base_value,
                 icon_ids, slot, quality, ench_lvl):
        super().__init__()
        self.type_str = parent.__class__.__name__
        self.type = parent.__class__
        self.unidentified_name = name
        tmp_material = tuple(v for v in material.split())
        self.material = tmp_material[0]
        self.base_weight = base_weight
        self.weight = self.base_weight * float(tmp_material[1])
        self.base_value = base_value
        self.value = self.base_value * float(tmp_material[2])
        self.icon_id_world, self.icon_id_equipped, self.icon_id_inv = icon_ids
        self.icon = {
            'world': parent.game.interface.tileset[icon_ids[0]].copy(),
            'equip': parent.game.interface.tileset[icon_ids[1]].copy(),
            'inv': parent.game.interface.tileset[icon_ids[2]].copy() }
        self.slot = slot
        self.quality = int(quality)
        self.enchantment_level = int(ench_lvl)
        self.full_name = ('{} {} {} {}'.format(
            quality_levels[self.quality],
            enchantment_levels[self.enchantment_level],
            self.material,
            name)).strip()


class Weapon(Item):
    game = None

    def __init__(self, game, template, groups, randomize=False):
        self.game = game
        value = template['base_value']
        quality = template['quality']
        ench_lvl = template['ench_lvl']
        if randomize:
            quality = random.choice(list(quality_levels))
            ench_lvl = random.choice(list(enchantment_levels))
            value = value * (1 + 0.4 * quality) * (1 + 0.8 * ench_lvl)
        super().__init__(self,
                         template['name'],
                         template['material'],
                         template['base_weight'],
                         value,
                         tuple(int(id) for id in template['icon_ids'].split()),
                         template['slot'],
                         quality,
                         ench_lvl)
        self.speed_modifier = template['speed_modifier']
        self.to_hit_modifier = template['to_hit_modifier'] + quality + ench_lvl
        num, sides, mod = decompile_dmg_die(template['damage_string'])
        self.damage_string = compile_dmg_die(num, sides, mod + ench_lvl)
        self.add(groups)
        logging.debug('Created item {}'.format(self.full_name))


class Armor(Item):
    game = None

    def __init__(self, game, template, groups, randomize=False):
        self.game = game
        value = template['base_value']
        quality = template['quality']
        ench_lvl = template['ench_lvl']
        if randomize:
            quality = random.choice(list(quality_levels))
            ench_lvl = random.choice(list(enchantment_levels))
            value = value * (1 + 0.4 * quality) * (1 + 0.8 * ench_lvl)
        super().__init__(self,
                         template['name'],
                         template['material'],
                         template['base_weight'],
                         value,
                         tuple(int(id) for id in template['icon_ids'].split()),
                         template['slot'],
                         quality,
                         ench_lvl)
        self.armor_class_modifier = template['armor_class_modifier'] + quality +\
                                    ench_lvl * 3
        self.add(groups)
        logging.debug('Created item {}'.format(self.full_name))
