# -*- coding: utf-8 -*-
"""
Module to support items (equipment) implementation.

"""

import logging
from json import loads
from os import path
import random
import tcod
import tcod.console
import tcod.constants
import tcod.event
from mrogue import decompile_dmg_die, compile_dmg_die, roll_gaussian, wait
from mrogue.console import Char

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

enchantment_colors = {
    -1: tcod.red,
    0: tcod.white,
    1: tcod.green
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
    item_type = Item
    if 'damage_string' in template:
        item_type = Weapon
    elif 'armor_class_modifier' in template:
        item_type = Armor
    return template, item_type


def get_item_equipped_in_slot(unit, slot):
    for item in unit.equipped:
        if item.slot == slot:
            return item
    return None


class ItemManager(object):
    loot = []
    templates = []
    items_on_ground = []
    item_templates = {}

    def __init__(self, game, num_items):
        self.game = game
        self.log = logging.getLogger(__name__)
        with open(path.join(game.dir, 'item_templates.json')) as f:
            self.templates_file = loads(f.read())
        self.log.debug('Creating pre-set items from templates:')
        for category, category_dict in self.templates_file.items():
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
        '''
        # create pre-set, default item
        preset = self.item_templates['weapons']['maces'][0].copy()
        # create random mace
        self.random_item('maces')
        # create random piece of armor
        self.random_item('armor')
        # create random item
        self.random_item()'''
        self.log.debug('Creating random loot ({}):'.format(num_items))
        for i in range(num_items):
            r_tmp, r_tpe = get_random_template(self.templates_file)
            r_tpe(self, r_tmp, self.loot, True).dropped(game.level.find_spot())

    def random_item(self, target=None, groups=None):
        tmp = None
        itype = None
        if not target:
            tmp, itype = get_random_template(self.templates_file)
        elif target in self.templates_file:
            tmp, itype = get_random_template(self.templates_file[target])
        else:
            if target in self.templates_file['weapons']:
                return Weapon(self, get_random_template(
                    self.templates_file['weapons'][target])[0], groups, True)
            elif target in self.templates_file['armor']:
                return Armor(self, get_random_template(
                    self.templates_file['armor'][target])[0], groups, True)
        return itype(self, tmp, groups, True)

    def show_inventory(self):
        total_items = len(self.game.player.inventory)
        item_limit = 14
        window_height = 4 + total_items
        if total_items > item_limit:
            window_height = 4 + item_limit
        width = 68
        last_letter = 96 + total_items
        window = tcod.console.Console(width, window_height, 'F')
        # tcod.console_set_default_foreground(window, tcod.light_orange)
        scroll = 0
        inventory = dict(zip(range(len(self.game.player.inventory)),
                             self.game.player.inventory))
        while True:
            window.clear()
            window.draw_frame(0, 0, width, window_height, 'Inventory')
            window.print(2, 1, 'Select an item or Esc to close:')
            window.print(5, 2, 'Name')
            window.print(48, 2, 'Slot     Wt    Val')
            if scroll > 0:
                window.print(0, 3, '^')
            for i in range(len(inventory)):
                if i > item_limit - 1:
                    break
                j = i + scroll
                it = inventory[j]
                suffix = ''
                if it.type == Weapon:
                    suffix = ' ({:+d}/{})'.format(
                        it.to_hit_modifier if it.status_identified else
                        it.base_to_hit,
                        it.damage if it.status_identified else it.base_damage)
                elif it.type == Armor:
                    suffix = ' ({:+d})'.format(
                        it.armor_class_modifier if it.status_identified else
                        it.base_armor_class)
                name = it.interface_name
                if len(name) + len(suffix) > 40:
                    name = name[:40-len(suffix)-1] + '+'
                summary = '{}'.format(name + suffix)
                details = '{:>6} {:6.2f} {:>6.2f}'.format(
                    it.slot,
                    it.weight,
                    it.value)
                window.print(1, 3 + i, it.icon, it.color)
                window.print(3, 3 + i, '{}) '.format(chr(j + 97)))
                window.print(6, 3 + i, summary,
                             enchantment_colors[it.enchantment_level] if
                             it.status_identified else tcod.white)
                window.print(46, 3 + i, details)
            if item_limit + scroll < total_items:
                window.print(0, window_height - 2, 'v')
            window.blit(self.game.screen, 4, 4)
            tcod.console_flush()
            key = wait()
            if key == 27:
                return False
            elif key == tcod.event.K_DOWN:
                scroll += 1 if item_limit + scroll < total_items else 0
            elif key == tcod.event.K_UP:
                scroll -= 1 if scroll > 0 else 0
            elif key in range(97, last_letter + 1):
                k = key - 97
                window.draw_rect(1, 3 + k, width - 2, 1, 0, bg=tcod.blue)
                window.blit(self.game.screen, 4, 4)
                w, h = 30, 4
                dialog = tcod.console.Console(w, h, 'F')
                dialog.draw_frame(0, 0, w, h, 'Select an action:')
                dialog.print(2, 1, 'a) Equip item')
                dialog.print(2, 2, 'b) Drop item')
                dialog.blit(self.game.screen, 4 + 10, 4 + 1)
                tcod.console_flush()
                while True:
                    selection = wait()
                    if selection == 27:
                        break
                    elif selection == tcod.event.K_a:
                        for i in self.game.player.equipped:
                            if self.game.player.inventory[k].slot == i.slot:
                                if i.enchantment_level < 0:
                                    self.game.messenger.add(
                                        'You can\'t replace cursed items.')
                                    return False
                        self.game.player.equip(
                            self.game.player.inventory[k])
                        return True
                    elif selection == tcod.event.K_b:
                        self.game.player.drop_item(
                            self.game.player.inventory[k])
                        return True

    def get_item_on_map(self, coordinates):
        return [i for i in self.items_on_ground if i.pos == coordinates]

    def show_equipment(self):
        w, h = 49, 8
        window = tcod.console.Console(w, h, 'F')
        while True:
            window.draw_frame(0, 0, w, h, 'Equipment')
            window.print(2, 1, 'Select a slot to manage or Esc to close:')
            i = 3
            slots = ('hand', 'head', 'chest', 'feet')
            for slot in slots:
                window.print(2, i, '{}) {:>5}:'.format(
                    chr(94 + i),
                    slot[0].upper() + slot[1:]))
                item = get_item_equipped_in_slot(self.game.player, slot)
                if item:
                    summary = '{:22.22}{}('.format(
                        item.interface_name,
                        '+' if len(item.interface_name) > 22 else ' ')
                    if item.type == Weapon:
                        summary += '{:+d}/{})'.format(
                            item.to_hit_modifier if item.status_identified else
                            item.base_to_hit,
                            item.damage if item.status_identified else
                            item.base_damage)
                    elif item.type == Armor:
                        summary += '{:+d})'.format(item.armor_class_modifier)
                    window.print(12, i, item.icon, item.color)
                    window.print(14, i, summary,
                                 enchantment_colors[item.enchantment_level])
                i += 1
            window.blit(self.game.screen, 4, 4)
            tcod.console_flush()
            key = wait()
            if key == 27:
                return False
            elif key in range(97, 97 + len(slots)):
                item = get_item_equipped_in_slot(
                    self.game.player, slots[key - 97])
                if item:
                    if item.enchantment_level < 0:
                        self.game.messenger.add(
                            'Cursed items can\'t be unequipped.')
                        return False
                    self.game.player.unequip(item)
                    return True
                else:
                    items = list(filter(lambda x: x.slot == slots[key - 97],
                                        self.game.player.inventory))
                    if len(items) < 1:
                        continue
                    window.draw_rect(1, 3 + key - 97, w - 2, 1, 0, bg=tcod.blue)
                    window.blit(self.game.screen, 4, 4)
                    total_items = len(items)
                    height = 2 + total_items
                    width = 48
                    last_letter = 96 + total_items
                    selection = tcod.console.Console(width, height, 'F')
                    inventory = dict(zip(range(len(items)), items))
                    selection.draw_frame(0, 0, width, height,
                                         'Select item to equip:')
                    for i in range(len(inventory)):
                        it = inventory[i]
                        suffix = ''
                        if it.type == Weapon:
                            suffix = ' ({:+d}/{})'.format(
                                it.to_hit_modifier if it.status_identified else
                                it.base_to_hit,
                                it.damage if it.status_identified else
                                it.base_damage)
                        elif it.type == Armor:
                            suffix = ' ({:+d})'.format(
                                it.armor_class_modifier if it.status_identified
                                else it.base_armor_class)
                        name = it.interface_name
                        if len(name) + len(suffix) > 40:
                            name = name[:40 - len(suffix) - 1] + '+'
                        summary = '{}'.format(name + suffix)
                        selection.print(1, 1 + i, it.icon,
                                        it.color)
                        selection.print(3, 1 + i, '{}) '.format(chr(i + 97)))
                        selection.print(6, 1 + i, summary,
                                        enchantment_colors[it.enchantment_level]
                                        if it.status_identified else tcod.white)
                    selection.blit(self.game.screen, 4 + 2, 4 + 2)
                    tcod.console_flush()
                    while True:
                        reaction = wait()
                        if reaction == 27:
                            break
                        elif reaction in range(97, last_letter + 1):
                            self.game.player.equip(items[reaction - 97])
                            return True


class Item(Char):
    def __init__(self, parent, manager, name, material, base_weight, base_value,
                 icon, slot, quality, ench_lvl):
        super().__init__()
        self.type_str = parent.__class__.__name__
        self.type = parent.__class__
        self.manager = manager

        self.pos = None
        tmp_material = tuple(v for v in material.split())
        self.material = tmp_material[0]
        self.base_weight = base_weight
        self.weight = self.base_weight * float(tmp_material[1])
        self.base_value = base_value
        self.value = self.base_value * float(tmp_material[2])
        self.icon = icon[0]
        self.color = vars(tcod.constants)[icon[1]]
        self.layer = 2
        self.slot = slot
        self.quality = int(quality)
        self.enchantment_level = int(ench_lvl)
        self.status_identified = False
        self.name = self.material + ' ' + name
        self.interface_name = '* ' + self.name
        self.identified_name = ('{} {} {}'.format(
            quality_levels[self.quality],
            enchantment_levels[self.enchantment_level], self.name)).strip()
        self.identified_name = ' '.join(self.identified_name.split())

    def dropped(self, coords):
        self.add(self.manager.items_on_ground,
                 self.manager.game.level.objects_on_map)
        self.pos = coords

    def picked(self):
        self.remove(self.manager.items_on_ground,
                    self.manager.game.level.objects_on_map)
        self.pos = None

    def identified(self):
        self.status_identified = True
        self.name = self.identified_name
        self.interface_name = self.identified_name


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
        super().__init__(
             self,
             manager,
             template['name'],
             material,
             template['base_weight'],
             value,
             (template['icon'], template['color']),
             template['slot'],
             quality,
             ench_lvl)
        self.speed_modifier = template['speed_modifier']
        self.base_to_hit = template['to_hit_modifier']
        self.to_hit_modifier = self.base_to_hit + quality + ench_lvl
        num, sides, mod = decompile_dmg_die(template['damage_string'])
        self.base_damage = compile_dmg_die(num, sides, mod)
        self.damage = compile_dmg_die(num, sides, mod + ench_lvl)
        self.add(groups)
        self.log.debug('Created item {}'.format(self.identified_name))


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
        super().__init__(
             self,
             manager,
             template['name'],
             material,
             template['base_weight'],
             value,
             (template['icon'], template['color']),
             template['slot'],
             quality,
             ench_lvl)
        ac_mod = template['armor_class_modifier']
        self.base_armor_class = ac_mod
        self.armor_class_modifier = ac_mod + quality + ench_lvl * 3
        self.add(groups)
        self.log.debug('Created item {}'.format(self.identified_name))
