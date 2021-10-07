# -*- coding: utf-8 -*-
"""Item management - item functions, printing various inventory screens, etc

Classes:
    * ItemManager - helper class to create random items, show and manage held and used items
    * Item - base class for a single type of an item
    * Wearable - a subclass of Item that can be equipped and modifies player's statistics and abilities
    * Stackable - a subclass of Item that can has the amount property
    * Consumable - a subclass of Item that produces an Effect on single use
"""
from random import choice
import string
import tcod
import tcod.constants
import tcod.event
import mrogue.item_data
import mrogue.map
import mrogue.message
import mrogue.player
import mrogue.utils
from mrogue import Point


class Item(mrogue.Entity):
    """Base class for an item. Should not be used directly

    Extends:
        * Entity
    Object attributes:
        * type - class name from the extending class
        * pos - position on the game map
        * base_weight - base weight for this type of item (default material)
        * base_value - base value shown for unidentified items
        * identified_value - value shown after the item is identified
        * value - value when material and quality is taken is into account
        * icon - variable inherited from Entity
        * layer - for the order of rendering if several Entities overlap
        * status_identified - whether the item is identified (all details revealed)
        * name - name for the unidentified version
        * amount - default = 1 for unstackable items
        * identified_name - full name including quality and enchantment
    Methods:
        * dropped() - state change when item is dropped on the ground
        * picked() - state change when item is put into some kind of inventory
        * identified() - state change when this Item instance is identified
    """
    _subclass_registry = {}
    max_name = 39

    def __init_subclass__(cls, subtype, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._subclass_registry[subtype] = cls

    def __new__(cls, template, *args, **kwargs):
        subtype = None
        if template['type'] in ('weapon', 'armor'):
            subtype = 'Wearable'
        elif template['type'] in ('scroll', 'potion'):
            subtype = 'Consumable'
        subclass = cls._subclass_registry[subtype]
        obj = object.__new__(subclass)
        obj.template = template
        return obj

    def __init__(self, name, base_weight, base_value, icon):
        super().__init__()
        self.pos = None
        self.base_weight = base_weight
        self.base_value = base_value
        self.identified_value = base_value
        self.value = base_value
        self.icon = icon
        self.background = tcod.blue * 0.3
        # self.layer = 2
        self.status_identified = False
        self.name = name
        self.amount = 1
        self.identified_name = name  # TEMP

    def __getnewargs__(self):
        return self.template,

    def __repr__(self):
        return f"Item('{self.name}', {self.__class__}, 0x{self.icon:x})"  # ", {self.color})"

    def __str__(self):
        return f"{chr(self.icon)} '{self.name}' ({self.amount})"  # " [{self.color}]"

    def dropped(self, coordinates: Point) -> None:
        """Assign a position on the map and add this item to current level's objects group

        :param coordinates: a pair of (x, y) coordinates
        """
        self.add(mrogue.map.Dungeon.current_level.objects_on_map)
        self.pos = coordinates

    def picked(self) -> None:
        """Remove placement data and remove the item from current level's objects group"""
        self.remove(mrogue.map.Dungeon.current_level.objects_on_map)
        self.pos = None

    def identified(self) -> None:
        """Change the name and show real value of the item"""
        self.status_identified = True
        self.name = self.identified_name
        self.value = self.identified_value

    @property
    def interface_name(self):
        color = tcod.white
        prefix = ''
        suffix = ''
        if self.status_identified:
            if hasattr(self, 'enchantment_level'):
                color = mrogue.item_data.enchantment_colors[self.enchantment_level]
            if self.subtype == 'weapon':
                suffix = f' ({self.props.damage[0]}-{self.props.damage[1]}/{self.props.to_hit_modifier:+d})'
            elif self.subtype == 'armor':
                suffix = f' ({self.props.armor_class_modifier:+d})'
        if self.amount > 1:
            prefix = f'{self.amount} '
        elif self in mrogue.player.Player.get().equipped:
            prefix = '(E) '
            color = tcod.light_grey
        elif not self.status_identified:
            prefix = '(?) '
        name = self.name
        if len(prefix + name + suffix) > Item.max_name:
            name = name[:Item.max_name - len(prefix) - len(suffix) - 1] + '+'
        return prefix + name + suffix, color


class Wearable(Item, subtype='Wearable'):
    """An item that can be held or worn. Encapsulates two types of functional types: weapons and armor.

    Extends:
        * Item
    Object attributes:
        * material - affects weight, value and Glyph color
        * quality - affects Item stats slightly
        * enchantment_level - affects Item stats severely
        * weight - self explanatory
        * slot - which equipment slot the Item takes
        * subtype - currently either Weapon or Armor
    """

    class Weapon:
        """Holds all the stats related to damage and accuracy.

        Object attributes:
            * speed_modifier - affects global player speed
            * base_to_hit - baseline accuracy bonus
            * to_hit_modifier - accuracy bonus after adding quality and enchantment modifiers
            * base_damage - baseline damage dice (range for the random number generator)
            * damage - damage dice after adding enchantment modifiers
        """

        def __init__(self, quality, enchantment_level, speed_modifier, base_to_hit, damage_range):
            self.speed_modifier = speed_modifier
            self.base_to_hit = base_to_hit
            self.to_hit_modifier = self.base_to_hit + quality + enchantment_level
            self.base_damage = damage_range
            self.damage = (damage_range[0] + enchantment_level, damage_range[1] + enchantment_level)

    class Armor:
        """Hold all the stats related to armor class.

        Object attributes:
            * base_armor_class - baseline armor class modifier
            * armor_class_modifier - armor class modifier after adding quality and enchantment bonuses
        """

        def __init__(self, quality, enchantment_level, ac_mod):
            self.base_armor_class = ac_mod
            self.armor_class_modifier = ac_mod + quality + enchantment_level * 2

    def __init__(self, template, _, groups, randomize=False):
        """Copies most init data  from the template but can randomize the quality and enchantment level."""
        super().__init__(
            template['name'],
            template['base_weight'],
            template['base_value'],
            template['icon'])
        if randomize:
            r_key, r_val = choice(list(mrogue.item_data.materials[template['type']].items()))
            self.material = r_val
            self.quality = mrogue.utils.roll_gaussian(1, 5, 0.7) - 3
            self.enchantment_level = mrogue.utils.roll_gaussian(1, 3, 0.35) - 2
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
        self.identified_name = ('{} {} {}'.format(
            mrogue.item_data.quality_levels[self.quality],
            mrogue.item_data.enchantment_levels[self.enchantment_level],
            self.name)).strip()
        self.identified_name = ' '.join(self.identified_name.split())
        self.subtype = template['type']
        if self.subtype == 'weapon':
            self.props = Wearable.Weapon(self.quality, self.enchantment_level, template['speed_modifier'],
                                         template['to_hit_modifier'], template['damage_range'])
        elif self.subtype == 'armor':
            self.props = Wearable.Armor(self.quality, self.enchantment_level, template['armor_class_modifier'])
        self.add(groups)

    def __repr__(self):
        return f"Wearable('{self.name}', {self.subtype}, 0x{self.icon:x})"  # ", {self.color})"


class Stackable(Item, subtype='Stackable'):
    """Adds count on top of the Item class

    Extends:
        * Item
    Object attributes:
        * amount - object should remove itself when amount reaches 0
    Methods:
        * used() - reduces the amount when used (as Consumable)
    """

    def __init__(self, template, amount, groups):
        super().__init__(template['name'], template['base_weight'], template['base_value'], template['icon'])
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

    def used(self, *args) -> None:
        """Remove self from any list when amount reaches 0"""
        self.amount -= 1
        if self.amount == 0:
            self.kill()


class Consumable(Stackable, subtype='Consumable'):
    """Class description.

    Extends:
        * Stackable
    Object attributes:
        * subtype - currently either scroll or potion
        * effect - a string representing the action to perform on use
        * uses - how many times Consumable can be used before reducing the amount
    Methods:
        * used() - apply the effect on use
        * identified() - identifies each copy of this item
        * identify_all() - loops through dungeon and inventory item groups to identify all copies
    """

    def __init__(self, template, amount, groups, _):
        """Sets appropriate color and name based on subtype (scroll or potion)"""
        super().__init__(template, amount, groups)
        self.subtype = template['type']
        if self.subtype == 'scroll':
            self.color = vars(tcod.constants)[template['color']]
            self.name = f"scroll titled {mrogue.item_data.scroll_names[template['name']]}"
        elif self.subtype == 'potion':
            self.color = mrogue.item_data.potion_colors[template['name']][1]
            self.name = f"{mrogue.item_data.potion_colors[template['name']][0]} potion"
        self.identified_name = f"{template['type']} of {template['name']}"
        self.slot = ''
        self.effect = template['effect']
        # self.uses = template['number_of_uses']
        self.add(groups)
        if self.name in mrogue.player.Player.get().identified_consumables:
            self.identified()

    def __repr__(self):
        return f"Consumable('{self.name}', {self.subtype}, 0x{self.icon:x})"  # ", {self.color})"

    def used(self, target) -> str:
        """Apply the related effect and fetch it's feedback message

        :param target: a unit to apply the effect to
        :return: the description of the effect to show the player
        """
        self.identified()
        mrogue.message.Messenger.add('This is {}.'.format(self.name))
        super().used(None)
        from mrogue.effects import Effect
        effect = Effect(self, target)
        return effect.apply()

    def identified(self) -> None:
        """Add this item to the list of consumables known to player"""
        mrogue.player.Player.get().identified_consumables.append(self.name)
        super().identified()
        self.identify_all()

    def identify_all(self) -> None:
        """Identify each item of this type in map and player inventory"""
        for i in mrogue.map.Dungeon.current_level.objects_on_map:
            if isinstance(i, Consumable) and not i.status_identified and i.effect == self.effect:
                i.identified()
        for i in mrogue.player.Player.get().inventory:
            if i.subtype in ('scroll', 'potion') and not i.status_identified and i.effect == self.effect:
                i.identified()


class ItemManager:
    """A helper class with multiple static and class methods for easy access to the item engine.

    Object attributes:
        * screen - the single Screen instance, will be called many times by this class
    Methods:
        * create_loot() - drops required number of items on current level's floor
        * random_item() - creates a random item of either required type or any type from the template list
        * try_equip() - equips the Item by the Entity if possible
        * get_item_on_map() - fetches the list of any items lying on an indicated level map coordinates
        * print_list() - prints the passed Item list on the screen
        * print_inventory_ui() - prints the frame, header and some static labels
        * show_inventory() - prints the inventory (backpack) menu
        * show_equipment() - prints the equipped items menu
        * show_pickup_choice() - prints the list of items on the ground
    """

    def __init__(self):
        """Assign random scroll names and potion colors for this session"""
        for s in filter(lambda x: x['type'] == 'scroll', mrogue.item_data.templates):
            mrogue.item_data.scroll_names[s['name']] = mrogue.utils.random_scroll_name()
        for p in filter(lambda x: x['type'] == 'potion', mrogue.item_data.templates):
            mrogue.item_data.potion_colors[p['name']] = choice(list(mrogue.item_data.materials['potions'].items()))
        self.screen = mrogue.io.Screen.get()

    @classmethod
    def create_loot(cls, num_items: int) -> None:  # , level):
        """Create some items and put them on the floor

        :param num_items: total number of unowned items for this level
        """
        for _ in range(num_items):
            cls.random_item().dropped(mrogue.map.Dungeon.find_spot())

    @staticmethod
    def random_item(keyword: str = None, groups: list = None) -> Item:
        """Create either a specific or fully random item

        :param keyword: if present, will create an Item of this particular type or property
        :param groups:  a list of groups that should include this Item
        :return: a new Item
        """
        if keyword:
            # random choice from templates containing a specific keyword
            target = choice(list(filter(lambda x: keyword[0] in (x.get('keywords') or []), mrogue.item_data.templates)))
        else:
            target = choice(mrogue.item_data.templates)
        return Item(target, 1, groups, True)

    @staticmethod
    def try_equip(item: Wearable) -> bool:
        """Equip an item unless there is a cursed item in related slot

        :param item: which Wearable to equip
        :return: True if Item could be equipped, False if there was a cursed Item in that slot
        """
        existing = mrogue.player.Player.get().in_slot(item.slot)
        if existing and existing.enchantment_level < 0:
            mrogue.message.Messenger.add('You can\'t replace cursed items.')
            return False
        mrogue.player.Player.get().equip(item)
        return True

    @staticmethod
    def get_item_on_map(coordinates: Point) -> list[Item]:
        """Get all the Items at the coordinates on the map of current level

        :param coordinates: x, y coordinates on the map
        :return: all the Items lying at this spot, as a list
        """
        return mrogue.utils.find_in(mrogue.map.Dungeon.current_level.objects_on_map, 'pos', coordinates, Item, True)

    @staticmethod
    def print_list(inventory: list[Wearable or Consumable], scroll: int,
                   width: int, limit: int, show_details: bool = False) -> tcod.Console:
        """Print a frame with all the Items in specified group. Allows scrolling

        :param inventory: which group to show
        :param scroll: which index to start printing 'inventory' from
        :param width: allowed width of the window
        :param limit: how many lines with Items can be displayed at once
        :param show_details: whether to print additional info after item name
        :return: tcod.Console with the list of items
        """
        window = tcod.Console(width, limit)
        if scroll > 0:
            window.print(0, 0, chr(0x2191), tcod.black, tcod.white)
        for i in range(len(inventory)):
            if i > limit - 1:
                break
            it = inventory[i+scroll]
            window.print(1, i, f'{string.ascii_letters[i+scroll]}) ')
            window.print(4, i, chr(it.icon), it.color)
            window.print(6, i, *it.interface_name)
            if show_details:
                window.print(Item.max_name+6, i, f'{it.slot:>6} {it.weight*it.amount:6.2f} {it.value*it.amount:>7.2f}')
        if limit + scroll < len(inventory):
            window.print(0, limit-1, chr(0x2193), tcod.black, tcod.white)
        return window

    @staticmethod
    def print_inventory_ui(window: tcod.Console, selected_sort: int, weight: int, value: int) -> None:
        """
        Print all the information related to inventory management

        :param window: parent window
        :param selected_sort: which column to print the arrow
        :param weight: total weight of all items
        :param value: total value of all items
        """
        window.clear()
        window.draw_frame(0, 0, window.width, window.height, decoration='╔═╗║ ║╚═╝')
        window.print_box(0, 0, window.width, 1, ' Inventory ', alignment=tcod.CENTER)
        window.print(2, 1, 'Select an item or Esc to close:')
        window.print(Item.max_name + 11, 1, '[/] Sort', tcod.yellow)
        window.print(6, 2, 'Name', tcod.lighter_gray)
        window.print(Item.max_name + 9, 2, 'Slot     Wt     Val', tcod.lighter_gray)
        window.print(selected_sort, 2, chr(0x2193), tcod.yellow)
        window.print(Item.max_name + 7, window.height - 2, f'Total: {weight:6.2f} {value:7.2f}', tcod.lighter_gray)

    def show_inventory(self) -> bool:
        """Print the list of Items in the 'inventory' (backpack) group

        :return: False if no inventory action was taken, True otherwise (would finish player's turn)
        """
        player = mrogue.player.Player.get()
        # allow to sort the list by one of four attributes
        sorts = mrogue.utils.circular([
            ('slot', Item.max_name + 8),
            ('weight', Item.max_name + 17),
            ('value', Item.max_name + 24),
            ('name', 5)])
        sort = next(sorts)
        raw_inventory = player.inventory + player.equipped
        total_items = len(raw_inventory)
        item_limit, scroll = 14, 0
        window_height, window_width = 5 + min(total_items, item_limit), Item.max_name + 30
        total_weight, total_value = sum([i.weight for i in raw_inventory]), sum([i.value for i in raw_inventory])
        inventory_window = tcod.Console(window_width, window_height, 'F')
        while True:
            # present the whole inventory screen
            self.print_inventory_ui(inventory_window, sort[1], total_weight, total_value)
            inventory = sorted(raw_inventory, key=lambda x: (getattr(x, sort[0]), x.name))
            self.print_list(inventory, scroll, window_width - 2, window_height - 5, True).blit(inventory_window, 1, 3)
            inventory_window.blit(self.screen, 4, 4)
            self.screen.present()
            # wait for input
            key = mrogue.io.wait()
            if key[1] & mrogue.io.ignore_mods == mrogue.io.ignore_mods:
                key = (key[0], key[1] - mrogue.io.ignore_mods)
            if mrogue.io.key_is(key, tcod.event.K_ESCAPE):
                return False
            elif mrogue.io.key_is(key, tcod.event.K_DOWN):
                scroll += 1 if item_limit + scroll < total_items else 0
            elif mrogue.io.key_is(key, tcod.event.K_UP):
                scroll -= 1 if scroll > 0 else 0
            elif mrogue.io.key_is(key, tcod.event.K_SLASH):
                sort = next(sorts)
            # if an a-zA-z key was pressed and it represents an item on the list:
            elif key in mrogue.item_data.letters and mrogue.item_data.letters[key] in range(total_items):
                # highlight selected item and present context actions
                i = inventory[mrogue.item_data.letters[key]]
                highlight_line = 3 + mrogue.item_data.letters[key] - scroll
                if 3 <= highlight_line <= window_height - 3:
                    inventory_window.draw_rect(1, highlight_line, window_width - 2, 1, 0, bg=tcod.blue)
                    inventory_window.blit(self.screen, 4, 4)
                context_actions = []
                if i.subtype in ('scroll', 'potion'):
                    context_actions.append(('Use item', i, player.use))
                elif i in player.equipped:
                    context_actions.append(('Unequip item', i, player.unequip))
                elif i.subtype in ('weapon', 'armor'):
                    context_actions.append(('Equip item', i, self.try_equip))
                if i not in player.equipped:
                    context_actions.append(('Drop item', i, player.drop_item))
                effect = mrogue.io.select_action(context_actions)
                if effect[0]:
                    return effect[1] if effect[1] is not None else True

    def show_equipment(self) -> bool:
        """Print the list of Items in the 'equipped' group

        :return: False if no inventory action was taken, True otherwise (would finish player's turn)
        """
        width, height = Item.max_name + 12, 8
        slots = ('hand', 'head', 'chest', 'feet')
        window = tcod.Console(width, height, 'F')
        while True:
            # present the whole equipment window
            window.clear()
            window.draw_frame(0, 0, width, height, decoration='╔═╗║ ║╚═╝')
            window.print_box(0, 0, width, 1, ' Equipment ', alignment=tcod.CENTER)
            window.print(2, 1, 'Select a slot to manage or Esc to close:')
            for line, slot in enumerate(slots):
                window.print(2, line + 3, f'{chr(97 + line)}) {slot.capitalize():>5}:')
                item = mrogue.utils.find_in(mrogue.player.Player.get().equipped, 'slot', slot)
                if item:
                    name, _ = item.interface_name
                    window.print(12, line+3, chr(item.icon), item.color)
                    window.print(14, line+3, f'{name[4:]}', mrogue.item_data.enchantment_colors[item.enchantment_level])
            window.blit(self.screen, 4, 4)
            self.screen.present()
            # wait for input
            key = mrogue.io.wait()
            if key[1] & mrogue.io.ignore_mods == mrogue.io.ignore_mods:
                key = (key[0], key[1] - mrogue.io.ignore_mods)
            if mrogue.io.key_is(key, tcod.event.K_ESCAPE):
                return False
            # if a-z was pressed and it represents one of the slots:
            elif key[0] in range(97, 97 + len(slots)):
                item = mrogue.utils.find_in(mrogue.player.Player.get().equipped, 'slot', slots[key[0] - 97])
                if item:
                    return mrogue.player.Player.get().unequip(item)
                else:
                    # if the slot is empty, highlight it and present list of available items
                    items = list(filter(lambda x: x.slot == slots[key[0] - 97], mrogue.player.Player.get().inventory))
                    if not items:
                        continue
                    items.sort(key=lambda x: (getattr(x, 'enchantment_level'), x.name))
                    window.draw_rect(1, 3 + key[0] - 97, width - 2, 1, 0, bg=tcod.blue)
                    window.blit(self.screen, 4, 4)
                    total_items = len(items)
                    limit, scroll = 10, 0
                    selection = tcod.Console(Item.max_name + 9, 2 + min(limit, total_items), 'F')
                    selection.draw_frame(0, 0, selection.width, selection.height, 'Select item to equip:')
                    while True:
                        self.print_list(items, scroll, selection.width - 2, selection.height - 2).blit(selection, 1, 1)
                        selection.blit(self.screen, 4 + 10, 4 + 2)
                        self.screen.present()
                        selected = mrogue.io.wait()
                        if mrogue.io.key_is(selected, tcod.event.K_ESCAPE):
                            break
                        elif mrogue.io.key_is(selected, tcod.event.K_DOWN):
                            scroll += 1 if limit + scroll < total_items else 0
                        elif mrogue.io.key_is(selected, tcod.event.K_UP):
                            scroll -= 1 if scroll > 0 else 0
                        elif selected[0] in range(97, 97 + total_items):
                            mrogue.player.Player.get().equip(items[selected[0] - 97])
                            return True

    def show_pickup_choice(self, items: list[Item]) -> Item or bool:
        total = len(items)
        w, limit, scroll = Item.max_name + 9, 6, 0
        h = 3 + min(limit, total)
        char = string.ascii_letters[total-1]
        window = tcod.Console(w, h, 'F')
        while True:
            window.clear()
            window.draw_frame(0, 0, w, h, decoration='╔═╗║ ║╚═╝')
            window.print_box(0, 0, w, 1, ' Pick up: ', alignment=tcod.CENTER)
            window.print_box(0, 1, w, 1, f'[a-{char}] single item, [,] - all:', tcod.light_gray, alignment=tcod.CENTER)
            self.print_list(items, scroll, w - 2, h - 3).blit(window, 1, 2)
            window.blit(self.screen, self.screen.width - w - 1, self.screen.height - h - 1)
            self.screen.present()
            key = mrogue.io.wait()
            if key[1] & mrogue.io.ignore_mods == mrogue.io.ignore_mods:
                key = (key[0], key[1] - mrogue.io.ignore_mods)
            if mrogue.io.key_is(key, tcod.event.K_ESCAPE):
                return False
            elif mrogue.io.key_is(key, tcod.event.K_COMMA):
                return items
            elif key[0] in range(97, 97 + total):
                return [items[key[0]-97]]
            elif mrogue.io.key_is(key, tcod.event.K_DOWN):
                scroll += 1 if limit + scroll < total else 0
            elif mrogue.io.key_is(key, tcod.event.K_UP):
                scroll -= 1 if scroll > 0 else 0
