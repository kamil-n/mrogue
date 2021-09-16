# -*- coding: utf-8 -*-

from random import choice
import string
import tcod
import tcod.constants
import tcod.event
import mrogue.item_data
import mrogue.utils
from mrogue.io import Screen
import mrogue.map
from mrogue.message import Messenger
from mrogue.player import Player


class ItemManager:
    def __init__(self):
        for s in filter(lambda x: x['type'] == 'scroll', mrogue.item_data.templates):
            mrogue.item_data.scroll_names[s['name']] = mrogue.utils.random_scroll_name()
        for p in filter(lambda x: x['type'] == 'potion', mrogue.item_data.templates):
            mrogue.item_data.potion_colors[p['name']] = choice(list(mrogue.item_data.materials['potions'].items()))
        self.screen = Screen.get()

    @classmethod
    def create_loot(cls, num_items):  # , level):
        for _ in range(num_items):
            cls.random_item().dropped(mrogue.map.Dungeon.find_spot())

    @staticmethod
    def random_item(keyword=None, groups=None):
        if keyword:
            target = choice(list(filter(lambda x: keyword[0] in (x.get('keywords') or []), mrogue.item_data.templates)))
        else:
            target = choice(mrogue.item_data.templates)
        if target['type'] in ('weapon', 'armor'):
            return Wearable(target, groups, True)
        elif target['type'] in ('scroll', 'potion'):
            return Consumable(target, 2, groups)

    @staticmethod
    def try_equip(item):
        existing = Player.get().get().in_slot(item.slot)
        if existing and existing.enchantment_level < 0:
            Messenger.add('You can\'t replace cursed items.')
            return False
        Player.get().equip(item)
        return True

    @staticmethod
    def print_list(inventory, window, height, offset, scroll, limit, show_details=False):
        if scroll > 0:
            window.print(0, 1 + offset, chr(24), tcod.black, tcod.white)
        for i in range(len(inventory)):
            if i > limit - 1:
                break
            it = inventory[i+scroll]
            prefix = '' if it.amount == 1 else f'({it.amount}) '
            if it in Player.get().equipped:
                prefix = '(E) '
            suffix = ''
            if it.type == Wearable and it.subtype == 'weapon':
                suffix = ' ({:+d}/{})'.format(
                    it.props.to_hit_modifier if it.status_identified else it.props.base_to_hit,
                    it.props.damage if it.status_identified else it.props.base_damage)
            elif it.type == Wearable and it.subtype == 'armor':
                suffix = f' ({it.props.armor_class_modifier if it.status_identified else it.props.base_armor_class:+d})'
            name = it.interface_name
            if len(prefix) + len(name) + len(suffix) > 40:
                name = name[:40 - len(prefix) - len(suffix) - 1] + '+'
            summary = prefix + name + suffix
            color = tcod.white
            if it in Player.get().equipped:
                color = tcod.gray
            elif it.status_identified and hasattr(it, 'enchantment_level'):
                color = mrogue.item_data.enchantment_colors[it.enchantment_level]
            window.print(1, 1 + i + offset, f'{string.ascii_letters[i+scroll]}) ')
            window.print(4, 1 + i + offset, it.icon, it.color)
            window.print(6, 1 + i + offset, summary, color)
            if show_details:
                details = f'{it.slot:>6} {it.weight * it.amount:6.2f}  {it.value * it.amount:>6.2f}'
                window.print(46, 1 + i + offset, details)
        if limit + scroll < len(inventory):
            window.print(0, height - 3, chr(25), tcod.black, tcod.white)

    def show_inventory(self):
        def circular(sequence):
            while sequence:
                for element in sequence:
                    yield element

        def select_option(options):
            num_options = len(options)
            w, h = 23, num_options + 2
            dialog = tcod.console.Console(w, h, 'F')
            dialog.draw_frame(0, 0, w, h, 'Select an action:')
            for i in range(num_options):
                dialog.print(2, i + 1, f'{options[i][0]}) {options[i][1]}')
            dialog.blit(self.screen, 4 + 10, 4 + 1)
            self.screen.context.present(self.screen)
        sorts = circular([('slot', 47), ('weight', 56), ('value', 62), ('name', 5)])
        sort = next(sorts)
        raw_inventory = Player.get().inventory + Player.get().equipped
        inventory = sorted(raw_inventory, key=lambda x: (getattr(x, sort[0]), x.name))
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
            inventory = sorted(raw_inventory, key=lambda x: (getattr(x, sort[0]), x.name))
            self.print_list(inventory, window, window_height, 2, scroll, item_limit, True)
            window.blit(self.screen, 4, 4)
            self.screen.context.present(self.screen)
            key = mrogue.io.wait()
            # ignore NumLock
            if key[1] & mrogue.io.ignore_mods == mrogue.io.ignore_mods:
                key = (key[0], key[1] - mrogue.io.ignore_mods)
            if mrogue.io.key_is(key, 27):
                return False
            elif mrogue.io.key_is(key, tcod.event.K_DOWN):
                scroll += 1 if item_limit + scroll < total_items else 0
            elif mrogue.io.key_is(key, tcod.event.K_UP):
                scroll -= 1 if scroll > 0 else 0
            elif mrogue.io.key_is(key, tcod.event.K_SLASH):
                sort = next(sorts)
            elif key in mrogue.item_data.letters and mrogue.item_data.letters[key] in range(total_items):
                i = inventory[mrogue.item_data.letters[key]]
                highlight_line = 3 + mrogue.item_data.letters[key] - scroll
                if 3 <= highlight_line <= window_height - 3:
                    window.draw_rect(1, highlight_line, width - 2, 1, 0, bg=tcod.blue)
                    window.blit(self.screen, 4, 4)
                context_actions = []
                if i.type == Consumable:
                    context_actions.append(('a', 'Use item', Player.get().use))
                elif i in Player.get().equipped:
                    context_actions.append(('a', 'Unequip item', Player.get().unequip))
                elif i.type == Wearable:
                    context_actions.append(('a', 'Equip item', self.try_equip))
                if i not in Player.get().equipped:
                    context_actions.append(('b', 'Drop item', Player.get().drop_item))
                select_option(context_actions)
                while True:
                    selection = mrogue.io.wait()
                    if mrogue.io.key_is(selection, 27):
                        break
                    elif selection[0] in range(97, 97 + len(context_actions)):
                        result = context_actions[selection[0] - 97][2](i)  # TODO: better lookup of appropriate action
                        return result if result is not None else True

    @staticmethod
    def get_item_on_map(coordinates):
        return [i for i in mrogue.map.Dungeon.current_level.objects_on_map if
                isinstance(i, Item) and i.pos == coordinates]

    def show_equipment(self):
        def get_item_equipped_in_slot(which):
            for worn in Player.get().equipped:
                if worn.slot == which:
                    return worn
            return None
        w, h = 49, 8
        window = tcod.Console(w, h, 'F')
        while True:
            window.draw_frame(0, 0, w, h, 'Equipment')
            window.print(2, 1, 'Select a slot to manage or Esc to close:')
            i = 3
            slots = ('hand', 'head', 'chest', 'feet')
            for slot in slots:
                window.print(2, i, f'{chr(94+i)}) {slot.capitalize():>5}:')
                item = get_item_equipped_in_slot(slot)
                if item:
                    summary = f"{item.interface_name:22.22}{'+' if len(item.interface_name) > 22 else ' '}("
                    if item.type == Wearable and item.subtype == 'weapon':
                        summary += '{:+d}/{})'.format(
                            item.props.to_hit_modifier if item.status_identified else
                            item.props.base_to_hit,
                            item.props.damage if item.status_identified else
                            item.props.base_damage)
                    elif item.type == Wearable and item.subtype == 'armor':
                        summary += '{:+d})'.format(item.props.armor_class_modifier)
                    window.print(12, i, item.icon, item.color)
                    window.print(14, i, summary,
                                 mrogue.item_data.enchantment_colors[item.enchantment_level])
                i += 1
            window.blit(self.screen, 4, 4)
            self.screen.context.present(self.screen)
            key = mrogue.io.wait()
            if mrogue.io.key_is(key, 27):
                return False
            elif key[0] in range(97, 97 + len(slots)):
                item = get_item_equipped_in_slot(slots[key[0] - 97])
                if item:
                    return Player.get().unequip(item)
                else:
                    items = list(filter(lambda x: x.slot == slots[key[0] - 97], Player.get().inventory))
                    items.sort(key=lambda x: (getattr(x, 'enchantment_level'), x.name))
                    if len(items) < 1:
                        continue
                    window.draw_rect(1, 3 + key[0] - 97, w - 2, 1, 0, bg=tcod.blue)
                    window.blit(self.screen, 4, 4)
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
                        selection.draw_frame(0, 0, width, height, 'Select item to equip:')
                        self.print_list(items, selection, height,  0, scroll, limit, False)
                        selection.blit(self.screen, 4 + 10, 4 + 2)
                        self.screen.context.present(self.screen)
                        reaction = mrogue.io.wait()
                        if mrogue.io.key_is(reaction, 27):
                            break
                        elif mrogue.io.key_is(reaction, tcod.event.K_DOWN):
                            scroll += 1 if limit + scroll < total_items else 0
                        elif mrogue.io.key_is(reaction, tcod.event.K_UP):
                            scroll -= 1 if scroll > 0 else 0
                        elif reaction[0] in range(97, last_letter + 1):
                            Player.get().equip(items[reaction[0] - 97])
                            return True


class Item(mrogue.Entity):
    def __init__(self, sub, name, base_weight, base_value, icon):
        super().__init__()
        self.type = sub.__class__
        self.pos = None
        self.base_weight = base_weight
        self.base_value = base_value
        self.identified_value = base_value
        self.value = base_value
        self.icon = chr(icon) if isinstance(icon, int) else icon
        self.layer = 2
        self.status_identified = False
        self.name = name
        self.amount = 1
        self.interface_name = name  # TEMP
        self.identified_name = name  # TEMP

    def dropped(self, coords):
        self.add(mrogue.map.Dungeon.current_level.objects_on_map)
        self.pos = coords

    def picked(self):
        self.remove(mrogue.map.Dungeon.current_level.objects_on_map)
        self.pos = None

    def identified(self):
        self.status_identified = True
        self.name = self.identified_name
        self.interface_name = self.identified_name
        self.value = self.identified_value


class Wearable(Item):
    class Weapon:
        def __init__(self, quality, enchantment_level, speed_modifier, base_to_hit, damage_string):
            self.speed_modifier = speed_modifier
            self.base_to_hit = base_to_hit
            self.to_hit_modifier = self.base_to_hit + quality + enchantment_level
            num, sides, mod = mrogue.utils.decompile_dmg_die(damage_string)
            self.base_damage = mrogue.utils.compile_dmg_die(num, sides, mod)
            self.damage = mrogue.utils.compile_dmg_die(num, sides, mod + enchantment_level)

    class Armor:
        def __init__(self, quality, enchantment_level, ac_mod):
            self.base_armor_class = ac_mod
            self.armor_class_modifier = ac_mod + quality + enchantment_level * 3

    def __init__(self, template, groups, randomize=False):
        super().__init__(
            self,
            template['name'],
            template['base_weight'],
            template['base_value'],
            template['icon'])
        if randomize:
            r_key, r_val = choice(list(mrogue.item_data.materials[template['type']].items()))
            self.material = r_val
            self.quality = mrogue.utils.roll_gaussian(1, 5, 1.15) - 3
            self.enchantment_level = mrogue.utils.roll_gaussian(1, 3, 0.5) - 2
            self.name = r_key + ' ' + self.name
        else:
            self.material = mrogue.item_data.materials[template['type']][template['material']]
            self.quality = int(template['quality'])
            self.enchantment_level = int(template['ench_lvl'])
            self.name = template['material'] + ' ' + self.name
        self.weight = self.base_weight * float(self.material[0])
        self.identified_value = self.base_value * (1 + 0.4 * self.quality) * (1 + 0.8 * self.enchantment_level)
        self.color = vars(tcod.constants)[self.material[2]]
        self.slot = template['slot']
        self.interface_name = '* ' + self.name
        self.identified_name = ('{} {} {}'.format(
            mrogue.item_data.quality_levels[self.quality],
            mrogue.item_data.enchantment_levels[self.enchantment_level],
            self.name)).strip()
        self.identified_name = ' '.join(self.identified_name.split())
        self.subtype = template['type']
        if self.subtype == 'weapon':
            self.props = Wearable.Weapon(self.quality, self.enchantment_level, template['speed_modifier'],
                                         template['to_hit_modifier'], template['damage_string'])
        elif self.subtype == 'armor':
            self.props = Wearable.Armor(self.quality, self.enchantment_level, template['armor_class_modifier'])
        self.add(groups)


class Stackable(Item):
    def __init__(self, template, amount, groups):
        super().__init__(self, template['name'], template['base_weight'], template['base_value'], template['icon'])
        self.amount = amount
        self.weight = self.base_weight * self.amount
        self.value = self.base_value * self.amount
        self.add(groups)

    # @property
    # def s_name(self):
    #     prefix = 'a' if self.amount == 1 else self.amount
    #     suffix = 's' if self.amount > 1 else ''
    #     return f"{prefix} {self.name}{suffix}"
    #
    # @property
    # def identified_s_name(self):
    #     prefix = 'a' if self.amount == 1 else self.amount
    #     suffix = 's' if self.amount > 1 else ''
    #     return f"{prefix} {self.name}{suffix}"

    def used(self, _):
        self.amount -= 1
        if self.amount == 0:
            self.kill()


class Consumable(Stackable):
    def __init__(self, template, amount, groups):
        super().__init__(template, amount, groups)
        self.subtype = template['type']
        if self.subtype == 'scroll':
            self.color = vars(tcod.constants)[template['color']]
            self.name = f"scroll titled {mrogue.item_data.scroll_names[template['name']]}"
        elif self.subtype == 'potion':
            self.color = mrogue.item_data.potion_colors[template['name']][1]
            self.name = f"{mrogue.item_data.potion_colors[template['name']][0]} potion"
        self.identified_name = f"{template['type']} of {template['name']}"
        self.interface_name = self.name
        self.slot = ''
        self.effect = template['effect']
        self.uses = template['number_of_uses']
        self.add(groups)
        if self.name in Player.get().identified_consumables:
            self.identified()

    def used(self, target):
        self.identified()
        Messenger.add('This is {}.'.format(self.name))
        super().used(None)
        from mrogue.effects import Effect
        effect = Effect(self, target)
        return effect.apply()

    def identified(self):
        Player.get().identified_consumables.append(self.name)
        super().identified()
        self.identify_all()

    def identify_all(self,):
        for i in mrogue.map.Dungeon.current_level.objects_on_map:
            if isinstance(i, Consumable) and not i.status_identified and i.effect == self.effect:
                i.identified()
        for i in Player.get().inventory:
            if i.type == Consumable and not i.status_identified and i.effect == self.effect:
                i.identified()
