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


letters = dict(zip([(l, tcod.event.KMOD_NONE) for l in range(97, 97 + 26 + 1)], range(26)))
letters.update(dict(zip([(l, tcod.event.KMOD_LSHIFT) for l in range(97, 97 + 26 + 1)], range(26, 26 + 26))))
letters.update(dict(zip([(l, tcod.event.KMOD_RSHIFT) for l in range(97, 97 + 26 + 1)], range(26, 26 + 26))))
scroll_names = {}
potion_colors = {}
