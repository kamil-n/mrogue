# -*- coding: utf-8 -*-

from json import loads
from os import path
import random
import string
import tcod
import tcod.constants
import tcod.event
from mrogue import Char, decompile_dmg_die, compile_dmg_die, roll_gaussian, wait, select_option, random_scroll_name, ignore_mods, key_is, cap
from mrogue.item_data import *


def get_random_template(data, level) -> (dict, type):
    while type(data) != list:
        key, data = random.choice(list(data.items()))
    template = data[level]
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


def circular(sequence):
    while sequence:
        for element in sequence:
            yield element


class ItemManager(object):
    def __init__(self, game):
        self.game = game
        with open(path.join(game.dir, 'item_templates.json')) as f:
            self.templates_file = loads(f.read())
        for s in self.templates_file['consumables']['scrolls']:
            scroll_names[s['name']] = random_scroll_name()
        for p in self.templates_file['consumables']['potions']:
            potion_colors[p['name']] = random.choice(list(materials['potions'].items()))

    def create_loot(self, num_items, level):
        for i in range(num_items):
            self.random_item(None, level=level).dropped(self.game.dungeon.find_spot())

    def random_item(self, target=None, groups=None, level=0):
        tmp = None
        itype = None
        if not target:
            target = random.choices(
                list(self.templates_file.keys()), [1, 2, 2])[0]
        if target in self.templates_file:
            tmp, itype = get_random_template(self.templates_file[target], level)
        else:
            if target in self.templates_file['weapons']:
                return Weapon(self, get_random_template(
                    self.templates_file['weapons'][target], level)[0], groups, True)
            elif target in self.templates_file['armor']:
                return Armor(self, get_random_template(
                    self.templates_file['armor'][target], level)[0], groups, True)
            elif target in self.templates_file['consumables']:
                return Consumable(self, get_random_template(
                    self.templates_file['consumables'][target], level)[0], groups)
        return itype(self, tmp, groups) if itype == Consumable else itype(self, tmp, groups, True)

    def try_equip(self, item):
        existing = self.game.player.in_slot(item.slot)
        if existing and existing.enchantment_level < 0:
            self.game.messenger.add('You can\'t replace cursed items.')
            return False
        self.game.player.equip(item)
        return True

    def prepare_inventory(self, item_list, sort):
        item_list.sort(key=lambda x: (getattr(x, sort), x.name))
        items = []
        i = 0
        while i < len(item_list):
            sublist = [item_list[i]]
            while i < len(item_list) - 1 and item_list[i+1].name == item_list[i].name:
                i += 1
                sublist.append(item_list[i])
            items.append(sublist)
            i += 1
        return items

    def print_list(self, inventory, window, height, offset, scroll, limit, show_details=False):
        if scroll > 0:
            window.print(0, 1 + offset, chr(24), tcod.black, tcod.white)
        for i in range(len(inventory)):
            if i > limit - 1:
                break
            j = i + scroll
            it = inventory[j][0]
            amount = len(inventory[j])
            prefix = '' if amount == 1 else '({}) '.format(amount)
            if it in self.game.player.equipped:
                prefix = '(E) '
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
            if len(prefix) + len(name) + len(suffix) > 40:
                name = name[:40 - len(prefix) - len(suffix) - 1] + '+'
            summary = '{}'.format(prefix + name + suffix)
            color = tcod.white
            if it in self.game.player.equipped:
                color = tcod.gray
            elif it.status_identified and hasattr(it, 'enchantment_level'):
                color = enchantment_colors[it.enchantment_level]
            window.print(1, 1 + i + offset, '{}) '.format(string.ascii_letters[j]))
            window.print(4, 1 + i + offset, it.icon, it.color)
            window.print(6, 1 + i + offset, summary, color)
            if show_details:
                details = '{:>6} {:6.2f}  {:>6.2f}'.format(
                    it.slot,
                    it.weight * amount,
                    it.value * amount)
                window.print(46, 1 + i + offset, details)
        if limit + scroll < len(inventory):
            window.print(0, height - 3, chr(25), tcod.black, tcod.white)

    def show_inventory(self):
        sorts = circular([('slot', 47), ('weight', 56), ('value', 62), ('name', 5)])
        sort = next(sorts)
        raw_inventory = self.game.player.inventory + self.game.player.equipped
        inventory = self.prepare_inventory(raw_inventory, sort[0])
        total_items = len(inventory)
        item_limit = 14
        window_height = 5 + total_items
        if total_items > item_limit:
            window_height = 5 + item_limit
        width = 68
        window = tcod.Console(width, window_height, 'F')
        scroll = 0
        while True:
            window.clear()
            window.draw_frame(0, 0, width, window_height, 'Inventory')
            window.print(2, 1, 'Select an item or Esc to close:')
            window.print(50, 1, '[/] Sort', tcod.yellow)
            window.print(6, 2, 'Name')
            window.print(48, 2, 'Slot     Wt     Val')
            window.print(sort[1], 2, chr(25), tcod.yellow)
            window.print(46, window_height - 2, 'Total:')
            window.print(53, window_height - 2, '{:6.2f} {:7.2f}'.format(
                sum([i.weight for i in raw_inventory]),
                sum([i.value for i in raw_inventory])))
            inventory = self.prepare_inventory(raw_inventory, sort[0])
            self.print_list(inventory, window, window_height, 2, scroll, item_limit, True)
            window.blit(self.game.screen, 4, 4)
            self.game.context.present(self.game.screen)
            key = wait()
            # ignore NumLock
            if key[1] & ignore_mods == ignore_mods:
                key = (key[0], key[1] - ignore_mods)
            if key_is(key, 27):
                return False
            elif key_is(key, tcod.event.K_DOWN):
                scroll += 1 if item_limit + scroll < total_items else 0
            elif key_is(key, tcod.event.K_UP):
                scroll -= 1 if scroll > 0 else 0
            elif key_is(key, tcod.event.K_SLASH):
                sort = next(sorts)
            elif key in letters and letters[key] in range(total_items):
                i = inventory[letters[key]][0]
                highlight_line = 3 + letters[key] - scroll
                if 3 <= highlight_line <= window_height - 3:
                    window.draw_rect(1, highlight_line, width - 2, 1, 0, bg=tcod.blue)
                    window.blit(self.game.screen, 4, 4)
                context_actions = []
                if i.type == Consumable:
                    context_actions.append(('a', 'Use item', self.game.player.use))
                elif i in self.game.player.equipped:
                    context_actions.append(('a', 'Unequip item', self.game.player.unequip))
                elif i.type == Weapon or i.type == Armor:
                    context_actions.append(('a', 'Equip item', self.try_equip))
                if not i in self.game.player.equipped:
                    context_actions.append(('b', 'Drop item', self.game.player.drop_item))
                select_option(self.game.screen, self.game.context, context_actions)
                while True:
                    selection = wait()
                    if key_is(selection, 27):
                        break
                    elif selection[0] in range(97, 97 + len(context_actions)):
                        result = context_actions[selection[0] - 97][2](i)  # TODO: better lookup of appropriate action
                        return result if result is not None else True

    def get_item_on_map(self, coordinates):
        return [i for i in self.game.dungeon.level.objects_on_map if
                isinstance(i, Item) and i.pos == coordinates]

    def show_equipment(self):
        w, h = 49, 8
        window = tcod.Console(w, h, 'F')
        while True:
            window.draw_frame(0, 0, w, h, 'Equipment')
            window.print(2, 1, 'Select a slot to manage or Esc to close:')
            i = 3
            slots = ('hand', 'head', 'chest', 'feet')
            for slot in slots:
                window.print(2, i, '{}) {:>5}:'.format(chr(94+i), cap(slot)))
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
            self.game.context.present(self.game.screen)
            key = wait()
            if key_is(key, 27):
                return False
            elif key[0] in range(97, 97 + len(slots)):
                item = get_item_equipped_in_slot(
                    self.game.player, slots[key[0] - 97])
                if item:
                    return self.game.player.unequip(item)
                else:
                    items = list(filter(lambda x: x.slot == slots[key[0] - 97], self.game.player.inventory))
                    items = self.prepare_inventory(items, sort='enchantment_level')
                    if len(items) < 1:
                        continue
                    window.draw_rect(1, 3 + key[0] - 97, w - 2, 1, 0, bg=tcod.blue)
                    window.blit(self.game.screen, 4, 4)
                    total_items = len(items)
                    limit = 10
                    height = 2 + total_items
                    if total_items > limit:
                        height = 2 + limit
                    width = 48
                    last_letter = 96 + total_items
                    scroll = 0
                    selection = tcod.Console(width, height, 'F')
                    while True:
                        selection.draw_frame(0, 0, width, height,
                                             'Select item to equip:')
                        self.print_list(items, selection, height,  0, scroll, limit, False)
                        selection.blit(self.game.screen, 4 + 10, 4 + 2)
                        self.game.context.present(self.game.screen)
                        reaction = wait()
                        if key_is(reaction, 27):
                            break
                        elif key_is(reaction, tcod.event.K_DOWN):
                            scroll += 1 if limit + scroll < total_items else 0
                        elif key_is(reaction, tcod.event.K_UP):
                            scroll -= 1 if scroll > 0 else 0
                        elif reaction[0] in range(97, last_letter + 1):
                            self.game.player.equip(items[reaction[0] - 97][0])
                            return True


class Item(Char):
    def __init__(self, sub, manager, name, base_weight, base_value, icon):
        super().__init__()
        self.type = sub.__class__
        self.manager = manager
        self.pos = None
        self.base_weight = base_weight
        self.base_value = base_value
        self.identified_value = base_value
        self.value = base_value
        if isinstance(icon, int):
            self.icon = chr(icon)
        else:
            self.icon = icon
        self.layer = 2
        self.status_identified = False
        self.name = name
        self.interface_name = name  # TEMP
        self.identified_name = name  # TEMP

    def dropped(self, coords):
        self.add(self.manager.game.dungeon.level.objects_on_map)
        self.pos = coords

    def picked(self):
        self.remove(self.manager.game.dungeon.level.objects_on_map)
        self.pos = None

    def identified(self):
        self.status_identified = True
        self.name = self.identified_name
        self.interface_name = self.identified_name
        self.value = self.identified_value


class Weapon(Item):
    def __init__(self, manager, template, groups, randomize=False):
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
        self.identified_value = self.base_value * (1 + 0.4 * self.quality) * (1 + 0.8 * self.enchantment_level)
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


class Armor(Item):
    def __init__(self, manager, template, groups, randomize=False):
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
        self.identified_value = self.base_value * (1 + 0.4 * self.quality) * (1 + 0.8 * self.enchantment_level)
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


class Consumable(Item):
    def __init__(self, manager, template, groups):
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
        self.slot = ''
        self.effect = template['effect']
        self.uses = template['number_of_uses']
        self.add(groups)
        if self.name in self.manager.game.player.identified_consumables:
            self.identified()

    def used(self, target):
        self.identified()
        self.manager.game.messenger.add('This is {}.'.format(self.name))
        from mrogue.effects import Effect
        effect = Effect(self.manager.game.messenger, self, target)
        return effect.apply()

    def identified(self):
        self.manager.game.player.identified_consumables.append(self.name)
        super().identified()
        self.identify_all()

    def identify_all(self,):
        for i in self.manager.game.dungeon.level.objects_on_map:
            if isinstance(i, Consumable) and not i.status_identified and i.effect == self.effect:
                i.identified()
        for i in self.manager.game.player.inventory:
            if i.type == Consumable and not i.status_identified and i.effect == self.effect:
                i.identified()
