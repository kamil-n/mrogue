# -*- coding: utf-8 -*-

import tcod.event

quality_levels = {
    -2: ('broken', 'brittle'),
    -1: ('flimsy', 'worn'),
    0: '',
    1: ('masterwork', 'ornate'),
    2: ('unique', 'expert')
}

enchantment_levels = {
    -2: 'cursed',
    -1: 'spent',
    0: '',
    1: 'energized',
    2: 'blessed'
}

# color list at https://libtcod.github.io/docs/html2/color.html or via tcod.constants
enchantment_colors = {
    -2: tcod.light_crimson,
    -1: tcod.lighter_crimson,
    0: tcod.white,
    1: tcod.lighter_sea,
    2: tcod.light_sea
}

materials = {
    'weapons': {
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
        'organic': {
          'cloth': ('0.1', '0.1', 'desaturated_fuchsia'),
          'wooden': ('0.7', '0.5', 'darker_orange'),
          'fur': ('0.2', '0.2', 'dark_orange'),
          'leather': ('0.2', '0.3', 'dark_amber'),
          'hide': ('0.3', '0.4', 'dark_sepia')
        },
        'metal': {
          'copper': ('0.8', '0.6', 'copper'),
          'bronze': ('0.8', '0.8', 'brass'),
          'iron': ('1.0', '1.0', 'darker_sky'),
          'steel': ('1.0', '1.25', 'light_sky'),
          'silver': ('0.8', '2.0', 'silver'),
          'alloy': ('0.9', '3.0', 'lighter_cyan')
        }
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

# dictionary of 52 key mappings (a-zA-Z)- 26 for small letters and 26 capital letters for either shift key
letters = dict(zip([(letter, tcod.event.KMOD_NONE) for letter in range(97, 97 + 26 + 1)], range(26)))
letters.update(dict(zip([(letter, tcod.event.KMOD_LSHIFT) for letter in range(97, 97 + 26 + 1)], range(26, 26 + 26))))
letters.update(dict(zip([(letter, tcod.event.KMOD_RSHIFT) for letter in range(97, 97 + 26 + 1)], range(26, 26 + 26))))

scroll_names = {}
potion_colors = {}

templates = [
  {
    'type': 'weapon',
    'name': 'shank',
    'material': 'bone',
    'base_weight': 0.2,
    'base_value': 1.0,
    'icon': 0x2193,
    'slot': 'main',
    'keywords': ['light'],
    'speed_modifier': 0.5,
    'to_hit_modifier': 0,
    'damage_range': (1, 1)
  },
  {
    'type': 'weapon',
    'name': 'knife',
    'material': 'bronze',
    'base_weight': 0.3,
    'base_value': 2.0,
    'icon': 0x2193,
    'slot': 'main',
    'keywords': ['light'],
    'speed_modifier': 0.5,
    'to_hit_modifier': 0,
    'damage_range': (1, 2)
  },
  {
    'type': 'weapon',
    'name': 'dagger',
    'material': 'iron',
    'base_weight': 0.5,
    'base_value': 5.0,
    'icon': 0x2193,
    'slot': 'main',
    'keywords': ['light'],
    'speed_modifier': 0.5,
    'to_hit_modifier': 0,
    'damage_range': (1, 3)
  },
  {
    'type': 'weapon',
    'name': 'stiletto',
    'material': 'iron',
    'base_weight': 0.4,
    'base_value': 4.0,
    'icon': 0x2193,
    'slot': 'main',
    'keywords': ['light'],
    'speed_modifier': 0.5,
    'to_hit_modifier': 0,
    'damage_range': (1, 3)
  },
  {
    'type': 'weapon',
    'name': 'shortsword',
    'material': 'bronze',
    'base_weight': 2.0,
    'base_value': 5.0,
    'icon': 0x5C,
    'slot': 'main',
    'keywords': ['light'],
    'speed_modifier': 0.8,
    'to_hit_modifier': 0,
    'damage_range': (1, 3)
  },
  {
    'type': 'weapon',
    'name': 'longsword',
    'material': 'iron',
    'base_weight': 3.5,
    'base_value': 20.0,
    'icon': 0x2502,
    'slot': 'main',
    'keywords': ['versatile'],
    'speed_modifier': 1.1,
    'to_hit_modifier': 1,
    'damage_range': (1, 4)
  },
  {
    'type': 'weapon',
    'name': 'broadsword',
    'material': 'bronze',
    'base_weight': 3.0,
    'base_value': 18.0,
    'icon': 0x49,
    'slot': 'main',
    'keywords': [],
    'speed_modifier': 1.1,
    'to_hit_modifier': 0,
    'damage_range': (2, 4)
  },
  {
    'type': 'weapon',
    'name': 'greatsword',
    'material': 'iron',
    'base_weight': 6.0,
    'base_value': 50.0,
    'icon': 0x2F,
    'slot': 'both',
    'keywords': ['2handed'],
    'speed_modifier': 1.2,
    'to_hit_modifier': -1,
    'damage_range': (2, 5)
  },
  {
    'type': 'weapon',
    'name': 'claymore',
    'material': 'iron',
    'base_weight': 7.0,
    'base_value': 55.0,
    'icon': 0x2F,
    'slot': 'both',
    'keywords': ['2handed'],
    'speed_modifier': 1.2,
    'to_hit_modifier': -1,
    'damage_range': (3, 5)
  },
  {
    'type': 'weapon',
    'name': 'flamberge',
    'material': 'iron',
    'base_weight': 8.0,
    'base_value': 60.0,
    'icon': 0x7C,
    'slot': 'both',
    'keywords': ['2handed'],
    'speed_modifier': 1.2,
    'to_hit_modifier': -1,
    'damage_range': (2, 5)
  },
  {
    'type': 'weapon',
    'name': 'twig',
    'material': 'wooden',
    'base_weight': 1.0,
    'base_value': 0.1,
    'icon': 0x266A,
    'slot': 'main',
    'keywords': ['light'],
    'speed_modifier': 0.7,
    'to_hit_modifier': 0,
    'damage_range': (1, 1)
  },
  {
    'type': 'weapon',
    'name': 'mace',
    'material': 'iron',
    'base_weight': 3.0,
    'base_value': 15.0,
    'icon': 0xED,
    'slot': 'main',
    'keywords': [],
    'speed_modifier': 1.1,
    'to_hit_modifier': 0,
    'damage_range': (2, 3)
  },
  {
    'type': 'weapon',
    'name': 'cudgel',
    'material': 'wooden',
    'base_weight': 2.0,
    'base_value': 10.0,
    'icon': 0xA1,
    'slot': 'main',
    'keywords': ['light'],
    'speed_modifier': 1.0,
    'to_hit_modifier': 0,
    'damage_range': (1, 3)
  },
  {
    'type': 'weapon',
    'name': 'hammer',
    'material': 'iron',
    'base_weight': 4.0,
    'base_value': 12.0,
    'icon': 0x2564,
    'slot': 'main',
    'keywords': [],
    'speed_modifier': 1.2,
    'to_hit_modifier': 0,
    'damage_range': (1, 4)
  },
  {
    'type': 'weapon',
    'name': 'club',
    'material': 'wooden',
    'base_weight': 3.0,
    'base_value': 8.0,
    'icon': 0x21,
    'slot': 'main',
    'keywords': [],
    'speed_modifier': 1.0,
    'to_hit_modifier': 0,
    'damage_range': (2, 3)
  },
  {
    'type': 'weapon',
    'name': 'morningstar',
    'material': 'iron',
    'base_weight': 5.0,
    'base_value': 25.0,
    'icon': 0xEE,
    'slot': 'main',
    'keywords': [],
    'speed_modifier': 1.2,
    'to_hit_modifier': 0,
    'damage_range': (2, 4)
  },
  {
    'type': 'weapon',
    'name': 'axe',
    'material': 'iron',
    'base_weight': 3.0,
    'base_value': 20.0,
    'icon': 0x2555,
    'slot': 'main',
    'keywords': [],
    'speed_modifier': 1.0,
    'to_hit_modifier': 0,
    'damage_range': (2, 4)
  },
  {
    'type': 'weapon',
    'name': 'battleaxe',
    'material': 'iron',
    'base_weight': 6.0,
    'base_value': 50.0,
    'icon': 0x2191,
    'slot': 'both',
    'keywords': ['2handed'],
    'speed_modifier': 1.5,
    'to_hit_modifier': -1,
    'damage_range': (3, 5)
  },
  {
    'type': 'weapon',
    'name': 'scythe',
    'material': 'iron',
    'base_weight': 5.0,
    'base_value': 40.0,
    'icon': 0x0393,
    'slot': 'both',
    'keywords': ['2handed'],
    'speed_modifier': 1.6,
    'to_hit_modifier': -2,
    'damage_range': (1, 6)
  },
  {
    'type': 'weapon',
    'name': 'trident',
    'material': 'wooden',
    'base_weight': 6.0,
    'base_value': 35.0,
    'icon': 0x03C5,
    'slot': 'both',
    'keywords': ['2handed'],
    'speed_modifier': 1.4,
    'to_hit_modifier': -1,
    'damage_range': (3, 5)
  },
  {
    'type': 'weapon',
    'name': 'stick',
    'material': 'wooden',
    'base_weight': 2.0,
    'base_value': 0.5,
    'icon': 0x2D,
    'slot': 'main',
    'keywords': ['light'],
    'speed_modifier': 0.6,
    'to_hit_modifier': 0,
    'damage_range': (1, 3)
  },
  {
    'type': 'weapon',
    'name': 'rod',
    'material': 'iron',
    'base_weight': 1.0,
    'base_value': 2.0,
    'icon': 0xEC,
    'slot': 'main',
    'keywords': ['versatile'],
    'speed_modifier': 0.9,
    'to_hit_modifier': 1,
    'damage_range': (2, 4)
  },
  {
    'type': 'weapon',
    'name': 'cane',
    'material': 'wooden',
    'base_weight': 1.5,
    'base_value': 5.0,
    'icon': 0x2320,
    'slot': 'main',
    'keywords': ['versatile'],
    'speed_modifier': 1.0,
    'to_hit_modifier': 1,
    'damage_range': (1, 3)
  },
  {
    'type': 'weapon',
    'name': 'staff',
    'material': 'wooden',
    'base_weight': 3.5,
    'base_value': 8.0,
    'icon': 0x2551,
    'slot': 'both',
    'keywords': ['2handed'],
    'speed_modifier': 1.5,
    'to_hit_modifier': 1,
    'damage_range': (2, 4)
  },
  # armor
  {
    'type': 'armor',
    'name': 'hat',
    'material': 'cloth',
    'base_weight': 0.2,
    'base_value': 8.0,
    'icon': 0xAA,
    'slot': 'head',
    'keywords': ['organic'],
    'armor_class_modifier': 0
  },
  {
    'type': 'armor',
    'name': 'cowl',
    'material': 'fur',
    'base_weight': 0.1,
    'base_value': 5.0,
    'icon': 0x03A9,
    'slot': 'head',
    'keywords': ['organic'],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'hood',
    'material': 'leather',
    'base_weight': 0.3,
    'base_value': 10.0,
    'icon': 0x2229,
    'slot': 'head',
    'keywords': ['organic'],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'cap',
    'material': 'bronze',
    'base_weight': 0.8,
    'base_value': 15.0,
    'icon': 0x25B2,
    'slot': 'head',
    'keywords': [],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'helmet',
    'material': 'iron',
    'base_weight': 1.0,
    'base_value': 25.0,
    'icon': 0x25B2,
    'slot': 'head',
    'keywords': ['metal'],
    'armor_class_modifier': 2
  },
  {
    'type': 'armor',
    'name': 'garb',
    'material': 'fur',
    'base_weight': 1.0,
    'base_value': 12.0,
    'icon': 0xA5,
    'slot': 'chest',
    'keywords': ['organic'],
    'armor_class_modifier': 0
  },
  {
    'type': 'armor',
    'name': 'coat',
    'material': 'cloth',
    'base_weight': 2.0,
    'base_value': 10.0,
    'icon': 0x2321,
    'slot': 'chest',
    'keywords': ['organic'],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'robe',
    'material': 'cloth',
    'base_weight': 1.5,
    'base_value': 20.0,
    'icon': 0x2562,
    'slot': 'chest',
    'keywords': ['organic'],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'tunic',
    'material': 'leather',
    'base_weight': 2.0,
    'base_value': 25.0,
    'icon': 0xA5,
    'slot': 'chest',
    'keywords': [],
    'armor_class_modifier': 2
  },
  {
    'type': 'armor',
    'name': 'breastplate',
    'material': 'iron',
    'base_weight': 3.0,
    'base_value': 60.0,
    'icon': 0x2567,
    'slot': 'chest',
    'keywords': ['metal'],
    'armor_class_modifier': 3
  },
  {
    'type': 'armor',
    'name': 'chainmail',
    'material': 'iron',
    'base_weight': 6.0,
    'base_value': 120.0,
    'icon': 0x2592,
    'slot': 'chest',
    'keywords': ['metal'],
    'armor_class_modifier': 4
  },
  {
    'type': 'armor',
    'name': 'shoes',
    'material': 'cloth',
    'base_weight': 0.5,
    'base_value': 18.0,
    'icon': 0x2558,
    'slot': 'feet',
    'keywords': ['organic'],
    'armor_class_modifier': 0
  },
  {
    'type': 'armor',
    'name': 'boots',
    'material': 'leather',
    'base_weight': 1.5,
    'base_value': 25.0,
    'icon': 0x255A,
    'slot': 'feet',
    'keywords': ['organic'],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'sabatons',
    'material': 'iron',
    'base_weight': 2.5,
    'base_value': 60.0,
    'icon': 0x255A,
    'slot': 'feet',
    'keywords': ['metal'],
    'armor_class_modifier': 2
  },
  {
    'type': 'armor',
    'name': 'trousers',
    'material': 'cloth',
    'base_weight': 0.5,
    'base_value': 10.0,
    'icon': 0x256B,
    'slot': 'legs',
    'keywords': ['organic'],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'leggings',
    'material': 'leather',
    'base_weight': 1.0,
    'base_value': 18.0,
    'icon': 0x256B,
    'slot': 'legs',
    'keywords': ['organic'],
    'armor_class_modifier': 2
  },
  {
    'type': 'armor',
    'name': 'greaves',
    'material': 'iron',
    'base_weight': 3.5,
    'base_value': 45.0,
    'icon': 0x256B,
    'slot': 'legs',
    'keywords': ['metal'],
    'armor_class_modifier': 3
  },
  {
    'type': 'armor',
    'name': 'mitts',
    'material': 'cloth',
    'base_weight': 0.2,
    'base_value': 8.0,
    'icon': 0xBB,
    'slot': 'hands',
    'keywords': ['organic'],
    'armor_class_modifier': 0
  },
  {
    'type': 'armor',
    'name': 'gloves',
    'material': 'leather',
    'base_weight': 0.3,
    'base_value': 15.0,
    'icon': 0xBB,
    'slot': 'hands',
    'keywords': [],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'bracers',
    'material': 'leather',
    'base_weight': 0.7,
    'base_value': 12.0,
    'icon': 0xAB,
    'slot': 'hands',
    'keywords': [],
    'armor_class_modifier': 2
  },
  {
    'type': 'armor',
    'name': 'gauntlets',
    'material': 'iron',
    'base_weight': 1.0,
    'base_value': 40.0,
    'icon': 0xAB,
    'slot': 'hands',
    'keywords': ['metal'],
    'armor_class_modifier': 3
  },
  # shields
  {
    'type': 'armor',
    'name': 'buckler',
    'material': 'wooden',
    'base_weight': 1.0,
    'base_value': 30.0,
    'icon': 0x2022,
    'slot': 'off',
    'keywords': [],
    'armor_class_modifier': 1
  },
  {
    'type': 'armor',
    'name': 'shield',
    'material': 'wooden',
    'base_weight': 2.7,
    'base_value': 40.0,
    'icon': 0x2666,
    'slot': 'off',
    'keywords': [],
    'armor_class_modifier': 2
  },
  {
    'type': 'armor',
    'name': 'kite shield',
    'material': 'wooden',
    'base_weight': 3.5,
    'base_value': 50.0,
    'icon': 0x25BC,
    'slot': 'off',
    'keywords': [],
    'armor_class_modifier': 3
  },
  {
    'type': 'armor',
    'name': 'tower shield',
    'material': 'wooden',
    'base_weight': 8.0,
    'base_value': 45.0,
    'icon': 0x25D9,
    'slot': 'off',
    'keywords': [],
    'armor_class_modifier': 4
  },
  # consumables
  {
    'type': 'scroll',
    'name': 'identify',
    'base_weight': 0.01,
    'base_value': 25.0,
    'icon': 0xA7,
    'color': 'lightest_sepia',
    'effect': 'identify',
    'number_of_uses': 1
  },
  {
    'type': 'scroll',
    'name': 'remove curse',
    'base_weight': 0.01,
    'base_value': 50.0,
    'icon': 0xA7,
    'color': 'lightest_sepia',
    'effect': 'decurse',
    'number_of_uses': 1
  },
  {
    'type': 'scroll',
    'name': 'fortify',
    'base_weight': 0.01,
    'base_value': 25.0,
    'icon': 0xA7,
    'color': 'lightest_sepia',
    'effect': 'fortify_armor 1',
    'number_of_uses': 1
  },
  {
    'type': 'scroll',
    'name': 'enchant',
    'base_weight': 0.01,
    'base_value': 50.0,
    'icon': 0xA7,
    'color': 'lightest_sepia',
    'effect': 'enchant 1',
    'number_of_uses': 1
  },
  {
    'type': 'potion',
    'name': 'healing',
    'base_weight': 0.1,
    'base_value': 25.0,
    'icon': 0xBF,
    'effect': 'heal 4 8',
    'number_of_uses': 1
  },
  {
    'type': 'potion',
    'name': 'scaleskin',
    'base_weight': 0.1,
    'base_value': 25.0,
    'icon': 0xBF,
    'effect': 'ac_bonus 4 15',
    'number_of_uses': 1
  },
  {
    'type': 'potion',
    'name': 'barkskin',
    'base_weight': 0.1,
    'base_value': 50.0,
    'icon': 0xBF,
    'effect': 'ac_bonus 2 30',
    'number_of_uses': 1
  },
  {
    'type': 'potion',
    'name': 'speed',
    'base_weight': 0.1,
    'base_value': 50.0,
    'icon': 0xBF,
    'effect': 'speed_bonus 0.5 10',
    'number_of_uses': 1
  }
]