# -*- coding: utf-8 -*-

import tcod.event

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
    -1: tcod.crimson,
    0: tcod.white,
    1: tcod.sea
}

materials = {
    'weapon': {
        'wooden': ('0.7', '0.5', 'darker_orange'),
        'bone': ('0.8', '0.6', 'lightest_amber'),
        'copper': ('0.8', '0.6', 'copper'),
        'bronze': ('0.8', '0.8', 'brass'),
        'iron': ('1.0', '1.0', 'darker_sky'),
        'steel': ('1.0', '1.25', 'light_sky'),
        'silver': ('0.8', '2.0', 'silver'),
        'alloy': ('0.9', '3.0', 'lighter_cyan')
    },
    'armor': {
        'cloth': ('0.1', '0.1', 'desaturated_fuchsia'),
        'fur': ('0.2', '0.2', 'dark_orange'),
        'leather': ('0.2', '0.3', 'dark_amber'),
        'hide': ('0.3', '0.4', 'dark_sepia'),
        'copper': ('0.8', '0.6', 'copper'),
        'bronze': ('0.8', '0.8', 'brass'),
        'iron': ('1.0', '1.0', 'darker_sky'),
        'steel': ('1.0', '1.25', 'light_sky'),
        'silver': ('0.8', '2.0', 'silver'),
        'alloy': ('0.9', '3.0', 'lighter_cyan')
    },
    'potions': {
        'red': tcod.red,
        'orange': tcod.orange,
        'amber': tcod.amber,
        'lime': tcod.lime,
        'chartreuse': tcod.chartreuse,
        'green': tcod.green,
        'turquoise': tcod.turquoise,
        'cyan': tcod.cyan,
        'azure': tcod.azure,
        'blue': tcod.blue,
        'violet': tcod.violet,
        'purple': tcod.purple,
        'fuchsia': tcod.fuchsia,
        'magenta': tcod.magenta,
        'pink': tcod.pink,
        'crimson': tcod.crimson
    }
}

# dictionary of 52 key mappings (a-zA-Z)- 26 for small letters and 26 capital letters for both shift keys pressed
letters = dict(zip([(letter, tcod.event.KMOD_NONE) for letter in range(97, 97 + 26 + 1)], range(26)))
letters.update(dict(zip([(letter, tcod.event.KMOD_LSHIFT) for letter in range(97, 97 + 26 + 1)], range(26, 26 + 26))))
letters.update(dict(zip([(letter, tcod.event.KMOD_RSHIFT) for letter in range(97, 97 + 26 + 1)], range(26, 26 + 26))))

scroll_names = {}
potion_colors = {}

templates = [
  {
    'type': 'weapon',
    'name': 'knife',
    'material': 'bronze',
    'base_weight': 0.5,
    'base_value': 20.0,
    'icon': '↓',
    'slot': 'hand',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': ['light'],
    'speed_modifier': 0.5,
    'to_hit_modifier': 0,
    'damage_string': '1d4'
  },
  {
    'type': 'weapon',
    'name': 'dagger',
    'material': 'iron',
    'base_weight': 0.7,
    'base_value': 30.0,
    'icon': '↓',
    'slot': 'hand',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': ['light'],
    'speed_modifier': 0.5,
    'to_hit_modifier': 0,
    'damage_string': '1d4'
  },
  {
    'type': 'weapon',
    'name': 'shortsword',
    'material': 'iron',
    'base_weight': 2.0,
    'base_value': 5.0,
    'icon': '(',
    'slot': 'hand',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': ['light'],
    'speed_modifier': 1.0,
    'to_hit_modifier': 0,
    'damage_string': '1d6'
  },
  {
    'type': 'weapon',
    'name': 'longsword',
    'material': 'steel',
    'base_weight': 3.5,
    'base_value': 80.0,
    'icon': '\\',
    'slot': 'hand',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': ['versatile'],
    'speed_modifier': 1.2,
    'to_hit_modifier': 0,
    'damage_string': '1d8'
  },
  {
    'type': 'weapon',
    'name': 'stick',
    'material': 'wooden',
    'base_weight': 1.0,
    'base_value': 10.0,
    'icon': '¡',
    'slot': 'hand',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': [],
    'speed_modifier': 1.0,
    'to_hit_modifier': 0,
    'damage_string': '1d6'
  },
  {
    'type': 'weapon',
    'name': 'mace',
    'material': 'iron',
    'base_weight': 4.0,
    'base_value': 60.0,
    'icon': '¡',
    'slot': 'hand',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': [],
    'speed_modifier': 1.2,
    'to_hit_modifier': 0,
    'damage_string': '1d8'
  },
  {
    'type': 'weapon',
    'name': 'axe',
    'material': 'iron',
    'base_weight': 3.0,
    'base_value': 40,
    'icon': '↑',
    'slot': 'hand',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': [],
    'speed_modifier': 1.0,
    'to_hit_modifier': 0,
    'damage_string': '1d6'
  },
  {
    'type': 'weapon',
    'name': 'battleaxe',
    'material': 'steel',
    'base_weight': 5.0,
    'base_value': 80.0,
    'icon': '↑',
    'slot': 'hand',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': ['versatile'],
    'speed_modifier': 1.5,
    'to_hit_modifier': 0,
    'damage_string': '1d8'
  },
  {
    'type': 'armor',
    'name': 'cap',
    'material': 'leather',
    'base_weight': 1.0,
    'base_value': 25.0,
    'icon': '^',
    'slot': 'head',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': [],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'helmet',
    'material': 'bronze',
    'base_weight': 2.0,
    'base_value': 65.0,
    'icon': '^',
    'slot': 'head',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': [],
    'armor_class_modifier': 2
  },
  {
    'type': 'armor',
    'name': 'tunic',
    'material': 'fur',
    'base_weight': 5.0,
    'base_value': 35.0,
    'icon': '¥',
    'slot': 'chest',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': [],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'breastplate',
    'material': 'leather',
    'base_weight': 10.0,
    'base_value': 100.0,
    'icon': '¥',
    'slot': 'chest',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': [],
    'armor_class_modifier': 2
  },
  {
    'type': 'armor',
    'name': 'shoes',
    'material': 'cloth',
    'base_weight': 0.7,
    'base_value': 8.0,
    'icon': '╚',
    'slot': 'feet',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': [],
    'armor_class_modifier': 0
  },
  {
    'type': 'armor',
    'name': 'boots',
    'material': 'leather',
    'base_weight': 2.0,
    'base_value': 40.0,
    'icon': '╚',
    'slot': 'feet',
    'quality': 0,
    'ench_lvl': 0,
    'keywords': [],
    'armor_class_modifier': 1
  },
  {
    'type': 'scroll',
    'name': 'identify',
    'base_weight': 0.01,
    'base_value': 100.0,
    'icon': '§',
    'color': 'lightest_sepia',
    'effect': 'identify',
    'number_of_uses': 1
  },
  {
    'type': 'scroll',
    'name': 'remove curse',
    'base_weight': 0.01,
    'base_value': 100.0,
    'icon': '§',
    'color': 'lightest_sepia',
    'effect': 'decurse',
    'number_of_uses': 1
  },
  {
    'type': 'potion',
    'name': 'healing',
    'base_weight': 0.1,
    'base_value': 50.0,
    'icon': '¿',
    'effect': 'heal 1d8+1',
    'number_of_uses': 1
  },
  {
    'type': 'potion',
    'name': 'scaleskin',
    'base_weight': 0.1,
    'base_value': 50.0,
    'icon': '¿',
    'effect': 'ac_bonus 2 10',
    'number_of_uses': 1
  }
]
