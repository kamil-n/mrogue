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
from rogue import decompile_dmg_die, compile_dmg_die, roll_gaussian
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
    2: 'unique'
}

enchantment_levels = {
    -1: 'cursed',
    0: '',
    1: 'blessed'
}

materials = {
    'weapons': [
        'wooden 0.7 0.5',
        'bone 0.8 0.6',
        'copper 0.8 0.6',
        'bronze 0.8 0.8',
        'iron 1.0 1.0',
        'steel 1.0 1.25',
        'silver 0.8 2.0',
        'alloy 0.9 3.0'
    ],
    'armor': [
        'cloth 0.1 0.1',
        'fur 0.2 0.2',
        'leather 0.2 0.3',
        'hide 0.3 0.4',
        'copper 0.8 0.6',
        'bronze 0.8 0.8',
        'iron 1.0 1.0',
        'steel 1.0 1.25',
        'silver 0.8 2.0',
        'alloy 0.9 3.0'
    ]
}


def get_random_template(data) -> (dict, type):
    while type(data) != list:
        key, data = random.choice(list(data.items()))
    template = random.choice(data)
    guess_type = Item
    if 'damage_string' in template:
        guess_type = Weapon
    elif 'armor_class_modifier' in template:
        guess_type = Armor
    return template, guess_type


class ItemManager(object):
    loot = pygame.sprite.Group()
    templates = pygame.sprite.Group()
    item_templates = {}

    def __init__(self, game):
        self.game = game
        self.log = logging.getLogger(__name__)
        basedir = path.dirname(path.abspath(__file__))
        with open(path.join(basedir, 'item_templates.json')) as f:
            templates_file = loads(f.read())
        for category, category_dict in templates_file.items():
            self.item_templates[category] = {}
            for subtype, type_list in category_dict.items():
                self.item_templates[category][subtype] = []
                for item in type_list:
                    new_item = None
                    if category == 'weapons':
                        new_item = Weapon(self.game, item, self.templates)
                    elif category == 'armor':
                        new_item = Armor(self.game, item, self.templates)
                    self.item_templates[category][subtype].append(new_item)
        # create pre-set, default item
        preset = self.item_templates['weapons']['maces'][0]
        # create random mace
        Weapon(self.game, get_random_template(templates_file['weapons']['maces'])[0], self.loot, True)
        # create random piece of armor
        Armor(self.game, get_random_template(templates_file['armor'])[0], self.loot, True)
        # create random item
        random_template, random_type = get_random_template(templates_file)
        random_type(self.game, random_template, self.loot, True)

    def show_inventory(self):
        window = PygameWindow(self.game.interface, 4, 4, 20, 3 + len(self.game.player.inventory), 'Inventory')
        window.print_at(2, 1, 'Select an item to equip or Esc to close:')
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
                    self.log.debug('Selected valid key {} from a-{}'.format(chr(event.key), chr(last_letter)))
                    self.game.player.equip(list(self.game.player.inventory)[event.key-97])
                    break
                else:
                    self.log.debug('Selected wrong key {} ({}?)'.format(event.key, chr(event.key)))

    def show_equipment(self):
        window = PygameWindow(self.game.interface, 4, 4, 21, 3 + len(self.game.player.equipped), 'Equipped items')
        window.print_at(2, 1, 'Select an item to unequip or Esc to close:')
        for i, item in enumerate(self.game.player.equipped):
            window.print_at(1, 3 + i, item.icon['inv'])
            summary = '{}) {} ('.format(chr(i + 97), item.full_name)
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
                last_letter = 96 + len(self.game.player.equipped)
                if event.key == 27:
                    break
                elif event.key in range(97, last_letter + 1):
                    self.log.debug('Selected valid key {} from a-{}'.format(chr(event.key), chr(last_letter)))
                    self.game.player.unequip(list(self.game.player.equipped)[event.key - 97])
                    break
                else:
                    self.log.debug('Selected wrong key {} ({}?)'.format(event.key, chr(event.key)))


class Item(pygame.sprite.Sprite):
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
            'equip': [parent.game.interface.tileset[i].copy() for i in icon_ids[1]],
            'inv': parent.game.interface.tileset[icon_ids[2]].copy()}
        self.slot = slot
        self.quality = int(quality)
        self.enchantment_level = int(ench_lvl)
        self.full_name = ('{} {} {} {}'.format(
            quality_levels[self.quality],
            enchantment_levels[self.enchantment_level],
            self.material,
            name)).strip()
        self.full_name = ' '.join(self.full_name.split())


class Weapon(Item):
    game = None

    def __init__(self, game, template, groups, randomize=False):
        self.game = game
        self.log = logging.getLogger(__name__)
        value = template['base_value']
        quality = template['quality']
        ench_lvl = template['ench_lvl']
        material = template['material']
        if randomize:
            quality = roll_gaussian(1, 5, 1.15) - 3
            ench_lvl = roll_gaussian(1, 3, 0.5) - 2
            material = random.choice(materials['weapons'])
            value = value * (1 + 0.4 * quality) * (1 + 0.8 * ench_lvl)
        icon_triplet_list = template['icon_ids'].split(', ')
        super().__init__(self,
                         template['name'],
                         material,
                         template['base_weight'],
                         value,
                         (int(icon_triplet_list[0].split()[0]),
                          [int(icon_set.split()[1]) for icon_set in icon_triplet_list],
                          int(icon_triplet_list[0].split()[2])),
                         template['slot'],
                         quality,
                         ench_lvl)
        self.speed_modifier = template['speed_modifier']
        self.to_hit_modifier = template['to_hit_modifier'] + quality + ench_lvl
        num, sides, mod = decompile_dmg_die(template['damage_string'])
        self.damage_string = compile_dmg_die(num, sides, mod + ench_lvl)
        self.add(groups)
        self.log.debug('Created item {}'.format(self.full_name))


class Armor(Item):
    game = None

    def __init__(self, game, template, groups, randomize=False):
        self.game = game
        self.log = logging.getLogger(__name__)
        value = template['base_value']
        quality = template['quality']
        ench_lvl = template['ench_lvl']
        material = template['material']
        if randomize:
            quality = roll_gaussian(1, 5, 1.15) - 3
            ench_lvl = roll_gaussian(1, 3, 0.5) - 2
            material = random.choice(materials['armor'])
            value = value * (1 + 0.4 * quality) * (1 + 0.8 * ench_lvl)
        icon_triplet_list = template['icon_ids'].split(', ')
        super().__init__(self,
                         template['name'],
                         material,
                         template['base_weight'],
                         value,
                         (int(icon_triplet_list[0].split()[0]),
                          [int(icon_set.split()[1]) for icon_set in icon_triplet_list],
                          int(icon_triplet_list[0].split()[2])),
                         template['slot'],
                         quality,
                         ench_lvl)
        self.armor_class_modifier = template['armor_class_modifier'] + quality + ench_lvl * 3
        self.add(groups)
        self.log.debug('Created item {}'.format(self.full_name))
