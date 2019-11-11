# -*- coding: utf-8 -*-
"""
Module to support items (equipment) implementation.

"""

import logging
from json import loads
from os import path
import pygame
import random
from rogue import decompile_dmg_die, compile_dmg_die, roll_gaussian
from rogue.pgame import PygameWindow, PygameDialog

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
    items_on_ground = pygame.sprite.LayeredUpdates()
    item_templates = {}

    def __init__(self, game, num_items):
        self.game = game
        self.log = logging.getLogger(__name__)
        basedir = path.dirname(path.abspath(__file__))
        with open(path.join(basedir, 'item_templates.json')) as f:
            templates_file = loads(f.read())
        self.log.debug('Creating pre-set items from templates:')
        for category, category_dict in templates_file.items():
            self.item_templates[category] = {}
            for subtype, type_list in category_dict.items():
                self.item_templates[category][subtype] = []
                for item in type_list:
                    new_item = None
                    if category == 'weapons':
                        new_item = Weapon(self, item, self.templates)
                    elif category == 'armor':
                        new_item = Armor(self, item, self.templates)
                    self.item_templates[category][subtype].append(new_item)
        ''' create pre-set, default item
        preset = self.item_templates['weapons']['maces'][0].copy()
        create random mace
        Weapon(self.game, get_random_template(templates_file[
            'weapons']['maces'])[0], self.loot, True)
        create random piece of armor
        Armor(self.game, get_random_template(templates_file[
            'armor'])[0], self.loot, True)
        create random item
        random_template, random_type = get_random_template(templates_file)
        random_type(self.game, random_template, self.loot, True) '''
        self.log.debug('Creating random loot ({}):'.format(num_items))
        for i in range(num_items):
            random_template, random_type = get_random_template(templates_file)
            random_type(self, random_template, self.loot, True).dropped(game.level.find_spot())

    def show_inventory(self):
        total_items = len(self.game.player.inventory)
        item_limit = 14
        window_height = 4 + total_items
        if total_items > item_limit:
            window_height = 4 + item_limit
        last_letter = 96 + total_items
        window = PygameWindow(self.game.interface, 4, 3, 32, window_height)
        scroll = 0
        inventory = dict(zip(range(len(self.game.player.inventory)),
                             self.game.player.inventory))
        pygame.event.clear()
        while True:
            window.clear()
            window.print_at(1, 0, 'Inventory')
            window.print_at(2, 1, 'Select an item or Esc to close:')
            window.print_at(3, 2, 'Name')
            window.print_at(22, 2, 'Slot     Wt    Val')
            if scroll > 0:
                window.print_at(0, 3, '^')
            for i in range(len(inventory)):
                if i > item_limit - 1:
                    break
                j = i + scroll
                window.print_at(1, 3 + i, inventory[j].icon['inv'])
                summary = '{}) {:29.29}{}('.format(
                    chr(j + 97),
                    inventory[j].full_name,
                    '\u2026' if len(inventory[j].full_name) > 29 else ' ')
                if inventory[j].type == Weapon:
                    summary += '{:+d}/{})'.format(
                        inventory[j].to_hit_modifier,
                        inventory[j].damage_string).ljust(10)
                elif inventory[j].type == Armor:
                    summary += '{:+d})'.format(
                        inventory[j].armor_class_modifier).ljust(10)
                summary += '{:>6} {:6.2f} {:>6.2f}'.format(
                    inventory[j].slot,
                    inventory[j].weight,
                    inventory[j].value)
                window.print_at(2, 3 + i, summary)
            if item_limit + scroll < total_items:
                window.print_at(0, window_height - 2, 'v')
            window.update()
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                self.game.interface.close()
            elif event.type == pygame.KEYDOWN:
                if event.key == 27:
                    break
                elif event.key == 274:
                    scroll += 1 if item_limit + scroll < total_items else 0
                elif event.key == 273:
                    scroll -= 1 if scroll > 0 else 0
                elif event.key in range(97, last_letter + 1):
                    rect = (14 * 32, 12 * 32, 20 * 32, 3 * 32)
                    save = self.game.interface.screen.subsurface(rect).copy()
                    dialog = PygameDialog(self.game.interface, 'Select an action:', [(pygame.K_a, 'Equip item'), (pygame.K_b, 'Drop item')])
                    key = dialog.loop()
                    self.game.interface.screen.blit(save, (14 * 32, 12 * 32))
                    pygame.display.update(rect)
                    if key:
                        if key == pygame.K_a:
                            self.game.player.equip(list(self.game.player.inventory)[event.key - 97])
                            break
                        elif key == pygame.K_b:
                            self.game.player.drop_item(list(self.game.player.inventory)[event.key - 97])
                            break
                    else:
                        continue

    def get_item_equipped_in_slot(self, unit, slot):
        for item in unit.equipped:
            if item.slot == slot:
                return item
        return None

    def get_item_on_map(self, coordinates):
        return [i for i in self.items_on_ground if i.pos == coordinates]

    def show_equipment(self):
        window = PygameWindow(self.game.interface, 4, 3, 22, 10)
        window.print_at(1, 0, 'Equipment')
        window.print_at(2, 1, 'Select a slot to unequip or Esc to close:')
        i = 3
        slots = ('hand', 'head', 'chest', 'feet')
        for slot in slots:
            window.print_at(1, i, '{}) {:>6}:'.format(
                chr(94 + i),
                slot[0].upper() + slot[1:]))
            item = self.get_item_equipped_in_slot(self.game.player, slot)
            if item:
                summary = '{:22.22}{}('.format(
                    item.full_name,
                    '\u2026' if len(item.full_name) > 22 else ' ')
                if item.type == Weapon:
                    summary += '{:+d}/{})'.format(item.to_hit_modifier,
                                                  item.damage_string)
                elif item.type == Armor:
                    summary += '{:+d})'.format(item.armor_class_modifier)
                window.print_at(6, i, item.icon['inv'])
                window.print_at(7, i, summary)
            i += 1
        window.update()
        pygame.event.clear()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                self.game.interface.close()
            elif event.type == pygame.KEYDOWN:
                if event.key == 27:
                    break
                elif event.key in range(97, 97 + len(slots)):
                    item = self.get_item_equipped_in_slot(
                        self.game.player, slots[event.key - 97])
                    if item:
                        self.game.player.unequip(item)
                        break


class Item(pygame.sprite.Sprite):
    def __init__(self, parent, manager, name, material, base_weight, base_value,
                 icon_ids, slot, quality, ench_lvl):
        super().__init__()
        self.type_str = parent.__class__.__name__
        self.type = parent.__class__
        self.manager = manager
        self.unidentified_name = name
        self.pos = None
        tmp_material = tuple(v for v in material.split())
        self.material = tmp_material[0]
        self.base_weight = base_weight
        self.weight = self.base_weight * float(tmp_material[1])
        self.base_value = base_value
        self.value = self.base_value * float(tmp_material[2])
        self.icon_id_world, self.icon_id_equipped, self.icon_id_inv = icon_ids
        tileset = manager.game.interface.tileset
        self.icon = {
            'equip': [tileset[i].copy() for i in icon_ids[1]],
            'inv': tileset[icon_ids[2]].copy()}
        self.image = tileset[icon_ids[0]].copy()
        self.rect = self.image.get_rect()
        self.layer = 2
        self.slot = slot
        self.quality = int(quality)
        self.enchantment_level = int(ench_lvl)
        self.full_name = ('{} {} {} {}'.format(
            quality_levels[self.quality],
            enchantment_levels[self.enchantment_level],
            self.material,
            name)).strip()
        self.full_name = ' '.join(self.full_name.split())

    def update(self):
        self.rect.topleft = (self.pos[0] * 32, self.pos[1] * 32)

    def dropped(self, coords):
        self.manager.items_on_ground.add(self)
        self.manager.game.interface.objects_on_map.add(self)
        self.pos = coords

    def picked(self, unit):
        self.remove((self.manager.items_on_ground,
                     self.manager.game.interface.objects_on_map))
        self.pos = None


class Weapon(Item):
    def __init__(self, manager, template, groups, randomize=False):
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
        super().__init__(
             self,
             manager,
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
    def __init__(self, manager, template, groups, randomize=False):
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
        super().__init__(
             self,
             manager,
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
        ac_mod = template['armor_class_modifier']
        self.armor_class_modifier = ac_mod + quality + ench_lvl * 3
        self.add(groups)
        self.log.debug('Created item {}'.format(self.full_name))
