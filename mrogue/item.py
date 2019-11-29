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
from mrogue import Char, decompile_dmg_die, compile_dmg_die, roll_gaussian, wait, select_option, random_scroll_name
from mrogue.item_data import *


def get_random_template(data) -> (dict, type):
    while type(data) != list:
        key, data = random.choice(list(data.items()))
    template = random.choice(data)
    item_type = Item
    if template['type'] == 'wearable':
        if template['subtype'] == 'weapon':
            item_type = Weapon
        elif template['subtype'] == 'armor':
            item_type = Armor
    elif template['type'] == 'consumable':
        item_type = Consumable
    return template, item_type


def get_item_equipped_in_slot(unit, slot):
    for item in unit.equipped:
        if item.slot == slot:
            return item
    return None


def print_list(inventory, window, height, offset, scroll, limit, show_details=False):
    if scroll > 0:
        window.print(0, 1 + offset, '^')
    for i in range(len(inventory)):
        if i > limit - 1:
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
            name = name[:40 - len(suffix) - 1] + '+'
        summary = '{}'.format(name + suffix)
        window.print(1, 1 + i + offset, it.icon, it.color)
        window.print(3, 1 + i + offset, '{}) '.format(chr(j + 97)))
        window.print(6, 1 + i + offset, summary,
                     enchantment_colors[it.enchantment_level] if
                     it.status_identified and hasattr(it, 'enchantment_level') else tcod.white)
        if show_details:
            details = '{:>6} {:6.2f} {:>6.2f}'.format(
                it.slot if hasattr(it, 'slot') else '',
                it.weight,
                it.value)
            window.print(46, 1 + i + offset, details)
    if limit + scroll < len(inventory):
        window.print(0, height - 2, 'v')


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
        for s in self.templates_file['consumables']['scrolls']:
            scroll_names[s['name']] = random_scroll_name()
        for p in self.templates_file['consumables']['potions']:
            potion_colors[p['name']] = random.choice(list(materials['potions'].items()))
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
                    elif category == 'consumables':
                        new_item = Consumable(self, item, self.templates)
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
            self.random_item(None, self.loot).dropped(game.level.find_spot())

    def random_item(self, target=None, groups=None):
        tmp = None
        itype = None
        if not target:
            target = random.choices(list(self.templates_file.keys()), [1, 2, 10])[0]
        if target in self.templates_file:
            tmp, itype = get_random_template(self.templates_file[target])
        else:
            if target in self.templates_file['weapons']:
                return Weapon(self, get_random_template(
                    self.templates_file['weapons'][target])[0], groups, True)
            elif target in self.templates_file['armor']:
                return Armor(self, get_random_template(
                    self.templates_file['armor'][target])[0], groups, True)
            elif target in self.templates_file['consumables']:
                return Consumable(self, get_random_template(
                    self.templates_file['consumables'][target])[0], groups)
        return itype(self, tmp, groups) if itype == Consumable else itype(self, tmp, groups, True)

    def try_equip(self, item):
        existing = self.game.player.in_slot(item.slot)
        if existing and existing.enchantment_level < 0:
            self.game.messenger.add('You can\'t replace cursed items.')
            return False
        self.game.player.equip(item)
        return True

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
            print_list(inventory, window, window_height, 2, scroll, item_limit, True)
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
                i = self.game.player.inventory[key - 97]
                window.draw_rect(1, 3 + key - 97, width - 2, 1, 0, bg=tcod.blue)
                window.blit(self.game.screen, 4, 4)
                context_actions = []
                if i.type == Consumable:
                    context_actions.append(('a', 'Use item', self.game.player.use))
                elif i.type == Weapon or i.type == Armor:
                    context_actions.append(('a', 'Equip item', self.try_equip))
                context_actions.append(('b', 'Drop item', self.game.player.drop_item))
                select_option(self.game.screen, context_actions)
                while True:
                    selection = wait()
                    if selection == 27:
                        break
                    elif selection in range(97, 97 + len(context_actions)):
                        result = context_actions[selection - 97][2](i)  # TODO: better lookup of appropriate action
                        return result if result is not None else True

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
                    return self.game.player.unequip(item)
                else:
                    items = list(filter(lambda x: hasattr(x, 'slot'), self.game.player.inventory))
                    items = list(filter(lambda x: x.slot == slots[key - 97], items))
                    if len(items) < 1:
                        continue
                    window.draw_rect(1, 3 + key - 97, w - 2, 1, 0, bg=tcod.blue)
                    window.blit(self.game.screen, 4, 4)
                    total_items = len(items)
                    limit = 10
                    height = 2 + total_items
                    if total_items > limit:
                        height = 2 + limit
                    width = 48
                    last_letter = 96 + total_items
                    scroll = 0
                    selection = tcod.console.Console(width, height, 'F')
                    inventory = dict(zip(range(len(items)), items))
                    while True:
                        selection.draw_frame(0, 0, width, height,
                                             'Select item to equip:')
                        print_list(inventory, selection, height,  0, scroll, limit, False)
                        selection.blit(self.game.screen, 4 + 2, 4 + 2)
                        tcod.console_flush()
                        reaction = wait()
                        if reaction == 27:
                            break
                        elif reaction == tcod.event.K_DOWN:
                            scroll += 1 if limit + scroll < total_items else 0
                        elif reaction == tcod.event.K_UP:
                            scroll -= 1 if scroll > 0 else 0
                        elif reaction in range(97, last_letter + 1):
                            self.game.player.equip(items[reaction - 97])
                            return True


class Item(Char):
    def __init__(self, sub, manager, name, base_weight, base_value, icon):
        super().__init__()
        self.type = sub.__class__
        self.manager = manager
        self.pos = None
        self.base_weight = base_weight
        self.base_value = base_value
        self.icon = icon
        self.layer = 2
        self.status_identified = False
        self.name = name
        self.interface_name = name  # TEMP
        self.identified_name = name  # TEMP

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
        super().__init__(
            self,
            manager,
            template['name'],
            template['base_weight'],
            template['base_value'],
            template['icon'])
        if randomize:
            r_key, r_val = random.choice(list(materials['weapons'].items()))
            self.material = r_val
            self.quality = roll_gaussian(1, 5, 1.15) - 3
            self.enchantment_level = roll_gaussian(1, 3, 0.5) - 2
            self.name = r_key + ' ' + self.name
        else:
            self.material = materials['weapons'][template['material']]
            self.quality = int(template['quality'])
            self.enchantment_level = int(template['ench_lvl'])
            self.name = template['material'] + ' ' + self.name
        self.weight = self.base_weight * float(self.material[0])
        self.value = self.base_value * (1 + 0.4 * self.quality) * (1 + 0.8 * self.enchantment_level)
        self.color = vars(tcod.constants)[self.material[2]]
        self.slot = template['slot']
        self.interface_name = '* ' + self.name
        self.identified_name = ('{} {} {}'.format(
            quality_levels[self.quality],
            enchantment_levels[self.enchantment_level], self.name)).strip()
        self.identified_name = ' '.join(self.identified_name.split())
        self.speed_modifier = template['speed_modifier']
        self.base_to_hit = template['to_hit_modifier']
        self.to_hit_modifier = self.base_to_hit + self.quality + self.enchantment_level
        num, sides, mod = decompile_dmg_die(template['damage_string'])
        self.base_damage = compile_dmg_die(num, sides, mod)
        self.damage = compile_dmg_die(num, sides, mod + self.enchantment_level)
        self.add(groups)
        self.log.debug('Created item {}'.format(self.identified_name))


class Armor(Item):
    def __init__(self, manager, template, groups, randomize=False):
        self.log = logging.getLogger(__name__)
        super().__init__(
            self,
            manager,
            template['name'],
            template['base_weight'],
            template['base_value'],
            template['icon'])
        if randomize:
            r_key, r_val = random.choice(list(materials['armor'].items()))
            self.material = r_val
            self.quality = roll_gaussian(1, 5, 1.15) - 3
            self.enchantment_level = roll_gaussian(1, 3, 0.5) - 2
            self.name = r_key + ' ' + self.name
        else:
            self.material = materials['armor'][template['material']]
            self.quality = int(template['quality'])
            self.enchantment_level = int(template['ench_lvl'])
            self.name = template['material'] + ' ' + self.name
        self.weight = self.base_weight * float(self.material[0])
        self.value = self.base_value * (1 + 0.4 * self.quality) * (1 + 0.8 * self.enchantment_level)
        self.color = vars(tcod.constants)[self.material[2]]
        self.slot = template['slot']
        self.interface_name = '* ' + self.name
        self.identified_name = ('{} {} {}'.format(
            quality_levels[self.quality],
            enchantment_levels[self.enchantment_level], self.name)).strip()
        self.identified_name = ' '.join(self.identified_name.split())
        ac_mod = template['armor_class_modifier']
        self.base_armor_class = ac_mod
        self.armor_class_modifier = ac_mod + self.quality + self.enchantment_level * 3
        self.add(groups)
        self.log.debug('Created item {}'.format(self.identified_name))


class Consumable(Item):
    def __init__(self, manager, template, groups):
        self.log = logging.getLogger(__name__)
        super().__init__(
            self,
            manager,
            template['name'],
            template['base_weight'],
            template['base_value'],
            template['icon'])
        self.weight = self.base_weight
        self.value = self.base_value
        if template['subtype'] == 'scroll':
            self.color = vars(tcod.constants)[template['color']]
            self.name = 'a scroll titled ' + scroll_names[template['name']]
        elif template['subtype'] == 'potion':
            self.color = potion_colors[template['name']][1]
            self.name = potion_colors[template['name']][0] + ' potion'
        self.identified_name = 'a {} of {}'.format(template['subtype'], template['name'])
        self.interface_name = self.name
        self.subtype = template['subtype']
        self.effect = template['effect']
        self.uses = template['number_of_uses']
        self.add(groups)
        self.log.debug('Created item {}'.format(self.identified_name))

    def used(self, target):
        self.identified()
        self.manager.game.messenger.add('This is {}.'.format(self.name))
        from mrogue.effects import Effect
        effect = Effect(self.manager.game.messenger, self, target)
        return effect.apply()

    def identified(self):
        super().identified()
        self.identify_all()

    def identify_all(self,):
        for i in self.manager.loot:
            if not i.status_identified and i.type == Consumable and i.effect == self.effect:
                i.identified()
        for i in self.manager.game.player.inventory:
            if not i.status_identified and i.type == Consumable and i.effect == self.effect:
                i.identified()
