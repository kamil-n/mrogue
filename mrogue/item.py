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
import mrogue.io
import mrogue.item_data
import mrogue.map
import mrogue.message
import mrogue.player
import mrogue.unit
import mrogue.utils


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
        * interface_name - name used for displaying in a list (equipment window, etc)
        * identified_name - full name including quality and enchantment
    Methods:
        * dropped() - state change when item is dropped on the ground
        * picked() - state change when item is put into some kind of inventory
        * identified() - state change when this Item instance is identified
    """

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

    def __repr__(self):
        return f"Item('{self.name}', {self.type}, '{self.icon}')"  # ", {self.color})"

    def __str__(self):
        return f"{self.icon} '{self.name}' ({self.amount})"  # " [{self.color}]"

    def dropped(self, coordinates: tuple[int, int]) -> None:
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
        self.interface_name = self.identified_name
        self.value = self.identified_value


class Wearable(Item):
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

        def __init__(self, quality, enchantment_level, speed_modifier, base_to_hit, damage_string):
            self.speed_modifier = speed_modifier
            self.base_to_hit = base_to_hit
            self.to_hit_modifier = self.base_to_hit + quality + enchantment_level
            num, sides, mod = mrogue.utils.decompile_dmg_dice(damage_string)
            self.base_damage = mrogue.utils.compile_dmg_dice(num, sides, mod)
            self.damage = mrogue.utils.compile_dmg_dice(num, sides, mod + enchantment_level)

    class Armor:
        """Hold all the stats related to armor class.

        Object attributes:
            * base_armor_class - baseline armor class modifier
            * armor_class_modifier - armor class modifier after adding quality and enchantment bonuses
        """

        def __init__(self, quality, enchantment_level, ac_mod):
            self.base_armor_class = ac_mod
            self.armor_class_modifier = ac_mod + quality + enchantment_level * 2

    def __init__(self, template, groups, randomize=False):
        """Copies most init data  from the template but can nradomize the quality and enchantment level."""
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

    def __repr__(self):
        return f"Wearable('{self.name}', {self.subtype}, '{self.icon}')"  # ", {self.color})"


class Stackable(Item):
    """Adds count on top of the Item class

    Extends:
        * Item
    Object attributes:
        * amount - object should remove itself when amount reaches 0
    Methods:
        * used() - reduces the amount when used (as Consumable)
    """

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

    def used(self, *args) -> None:
        """Remove self from any list when amount reaches 0"""
        self.amount -= 1
        if self.amount == 0:
            self.kill()


class Consumable(Stackable):
    """Class description.

    Extends:
        * Stackable
    Object attributes:
        * subtype - currently either scroll or potion
        * effect - a string representing the action to perform on use
        * uses - how many times Consumable can be used before reducting the amount
    Methods:
        * used() - apply the effect on use
        * identified() - identifies each copy of this item
        * identify_all() - loops through dungeon and inventory item groups to identfy all copies
    """

    def __init__(self, template, amount, groups):
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
        self.interface_name = self.name
        self.slot = ''
        self.effect = template['effect']
        # self.uses = template['number_of_uses']
        self.add(groups)
        if self.name in mrogue.player.Player.get().identified_consumables:
            self.identified()

    def __repr__(self):
        return f"Consumable('{self.name}', {self.subtype}, '{self.icon}')"  # ", {self.color})"

    def used(self, target: mrogue.unit.Unit) -> str:
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
            if i.type == Consumable and not i.status_identified and i.effect == self.effect:
                i.identified()


class ItemManager:
    """A helper class with multiple static and class methods for easy access to the item engine.

    Object attributes:
        * screen - the single Screen instance, will be called many times by this class
    Methods:
        * create_loot() - drops required number of items on current level's floor
        * random_item() - creates a random item of either required type or any type from the template list
        * try_equip() - equips the Item by the Entity if possible
        * print_list() - prints the attached Item list on the screen
        * show_inventory() - prints the inventory (backpack) menu
        * get_item_on_map() - fetches the list of any items lying on an indicated level map coordinates
        * show_equipment() - prints the equipped items menu
    """

    def __init__(self):
        """Assign random scroll names and potion colors during this session"""
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
        if target['type'] in ('weapon', 'armor'):
            return Wearable(target, groups, True)
        elif target['type'] in ('scroll', 'potion'):
            return Consumable(target, 1, groups)

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
    def print_list(inventory: list[Wearable or Consumable], window: tcod.Console,
                   height: int, offset: int, scroll: int, limit: int, show_details: bool = False) -> None:
        """Print a frame with all the Items in specified group. Allows scrolling

        :param inventory: which group to show
        :param window: parent window that will be drawn over
        :param height: how many lines in the parent window can be used
        :param offset: what line in the parent window to start drawing from
        :param scroll: which index to start printing from
        :param limit: how many lines with Items can be displayed at once
        :param show_details: whether to print additional info after item name
        """
        if scroll > 0:
            # if already scrolled down, print the up arrow
            window.print(0, 1 + offset, chr(0x2191), tcod.black, tcod.white)
        for i in range(len(inventory)):
            if i > limit - 1:
                break
            it = inventory[i+scroll]
            prefix = '' if it.amount == 1 else f'({it.amount}) '
            if it in mrogue.player.Player.get().equipped:
                prefix = '(E) '
            suffix = ''
            if it.type == Wearable and it.subtype == 'weapon':
                suffix = ' ({:+d}/{})'.format(
                    it.props.to_hit_modifier if it.status_identified else it.props.base_to_hit,
                    it.props.damage if it.status_identified else it.props.base_damage)
            elif it.type == Wearable and it.subtype == 'armor':
                suffix = f' ({it.props.armor_class_modifier if it.status_identified else it.props.base_armor_class:+d})'
            name = it.interface_name
            # if full name would be too wide, cut off after 40 characters
            if len(prefix) + len(name) + len(suffix) > 40:
                name = name[:40 - len(prefix) - len(suffix) - 1] + '+'
            summary = prefix + name + suffix
            color = tcod.white
            if it in mrogue.player.Player.get().equipped:
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
            # if there are more items that would fit in the limit, print the down arrow
            window.print(0, height - 3, chr(0x2193), tcod.black, tcod.white)

    def show_inventory(self) -> bool:
        """Print the list of Items in the 'inventory' (backpack) group

        :return: False if no inventory action was taken, True otherwise (would finish player's turn)
        """
        def circular(sequence):
            """Pick next item from the sequence indefinitely"""
            while sequence:
                for element in sequence:
                    yield element

        def select_option(options: list[tuple[str, str, Item]]) -> None:
            """Present a small sub-window with a range of available options to perform

            :param options: a list of options as tuples: (a letter, action description string, Item)
            """
            num_options = len(options)
            w, h = 23, num_options + 2
            dialog = tcod.console.Console(w, h, 'F')
            dialog.draw_frame(0, 0, w, h, 'Select an action:')
            for i in range(num_options):
                dialog.print(2, i + 1, f'{options[i][0]}) {options[i][1]}')
            dialog.blit(self.screen, 4 + 10, 4 + 1)
            self.screen.present()
        player = mrogue.player.Player.get()
        # allow to sort the list by one of four attributes
        sorts = circular([('slot', 47), ('weight', 56), ('value', 62), ('name', 5)])
        sort = next(sorts)
        raw_inventory = player.inventory + player.equipped
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
            self.screen.present()
            key = mrogue.io.wait()
            # ignore NumLock:
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
                i = inventory[mrogue.item_data.letters[key]]
                highlight_line = 3 + mrogue.item_data.letters[key] - scroll
                if 3 <= highlight_line <= window_height - 3:
                    window.draw_rect(1, highlight_line, width - 2, 1, 0, bg=tcod.blue)
                    window.blit(self.screen, 4, 4)
                context_actions = []
                if i.type == Consumable:
                    context_actions.append(('a', 'Use item', player.use))
                elif i in player.equipped:
                    context_actions.append(('a', 'Unequip item', player.unequip))
                elif i.type == Wearable:
                    context_actions.append(('a', 'Equip item', self.try_equip))
                if i not in player.equipped:
                    context_actions.append(('b', 'Drop item', player.drop_item))
                select_option(context_actions)
                while True:
                    selection = mrogue.io.wait()
                    if mrogue.io.key_is(selection, tcod.event.K_ESCAPE):
                        break
                    elif selection[0] in range(97, 97 + len(context_actions)):
                        result = context_actions[selection[0] - 97][2](i)  # TODO: better lookup of appropriate action
                        return result if result is not None else True

    @staticmethod
    def get_item_on_map(coordinates: tuple[int, int]) -> list[Item]:
        """Get all the Items at the coordinates on the map of current level

        :param coordinates: x, y coordinates on the map
        :return: all the Items lying at this spot, as a list
        """
        return mrogue.utils.find_in(mrogue.map.Dungeon.current_level.objects_on_map, 'pos', coordinates, Item, True)

    def show_equipment(self) -> bool:
        """Print the list of Items in the 'equipped' group

        :return: False if no inventory action was taken, True otherwise (would finish player's turn)
        """
        w, h = 49, 8
        window = tcod.Console(w, h, 'F')
        while True:
            window.draw_frame(0, 0, w, h, 'Equipment')
            window.print(2, 1, 'Select a slot to manage or Esc to close:')
            i = 3
            slots = ('hand', 'head', 'chest', 'feet')
            for slot in slots:
                window.print(2, i, f'{chr(94+i)}) {slot.capitalize():>5}:')
                item = mrogue.utils.find_in(mrogue.player.Player.get().equipped, 'slot', slot)
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
            self.screen.present()
            key = mrogue.io.wait()
            if mrogue.io.key_is(key, tcod.event.K_ESCAPE):
                return False
            elif key[0] in range(97, 97 + len(slots)):
                item = mrogue.utils.find_in(mrogue.player.Player.get().equipped, 'slot', slots[key[0] - 97])
                if item:
                    return mrogue.player.Player.get().unequip(item)
                else:
                    items = list(filter(lambda x: x.slot == slots[key[0] - 97], mrogue.player.Player.get().inventory))
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
                        self.screen.present()
                        reaction = mrogue.io.wait()
                        if mrogue.io.key_is(reaction, tcod.event.K_ESCAPE):
                            break
                        elif mrogue.io.key_is(reaction, tcod.event.K_DOWN):
                            scroll += 1 if limit + scroll < total_items else 0
                        elif mrogue.io.key_is(reaction, tcod.event.K_UP):
                            scroll -= 1 if scroll > 0 else 0
                        elif reaction[0] in range(97, last_letter + 1):
                            mrogue.player.Player.get().equip(items[reaction[0] - 97])
                            return True
