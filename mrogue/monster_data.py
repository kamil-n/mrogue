templates = {
    'rodents':
    {
        'level_range': (0, 3),
        'occurrences': {
            0: (1, 1, 0, 0),
            1: (1, 3, 1, 0),
            2: (0, 4, 4, 1),
            3: (0, 0, 1, 1)
        },
        'subtypes': [
            {
                'name': 'young rat',
                'color': 'desaturated_flame',
                'icon': 'r',
                'ability_scores': [3, 14, 10],
                'hit_dice': '1d2',
                'dmg_dice_unarmed': '1d1-2',
                'keywords': ['finesse'],
                'speed': 0.75,
                'proficiency': 0,
                'ac_bonus': 1
            },
            {
                'name': 'rat',
                'color': 'dark_grey',
                'icon': 'r',
                'ability_scores': [4, 14, 10],
                'hit_dice': '1d3',
                'dmg_dice_unarmed': '1d2-2',
                'keywords': ['finesse'],
                'speed': 0.75,
                'proficiency': 0,
                'ac_bonus': 1
            },
            {
                'name': 'dire rat',
                'color': 'grey',
                'icon': 'r',
                'ability_scores': [6, 14, 12],
                'hit_dice': '1d3',
                'dmg_dice_unarmed': '1d3-2',
                'keywords': ['finesse'],
                'speed': 0.75,
                'proficiency': 0,
                'ac_bonus': 1
            },
            {
                'name': 'rat matriarch',
                'color': 'lighter_grey',
                'icon': 'R',
                'ability_scores': [8, 14, 14],
                'hit_dice': '1d4',
                'dmg_dice_unarmed': '1d3-1',
                'keywords': ['finesse'],
                'speed': 0.75,
                'proficiency': 1,
                'ac_bonus': 0
            }
        ]
    },
    'kobolds':
    {
        'level_range': (0, 3),
        'occurrences': {
            0: (2, 1, 0),
            1: (1, 1, 1),
            2: (1, 2, 2),
            3: (0, 1, 2)
        },
        'subtypes': [
            {
                'name': 'kobold outcast',
                'color': 'dark_flame',
                'icon': 'k',
                'ability_scores': [8, 14, 10],
                'hit_dice': '1d4',
                'dmg_dice_unarmed': '1d2+1',
                'keywords': [],
                'speed': 0.95,
                'proficiency': 2,
                'ac_bonus': 0
            },
            {
                'name': 'kobold guard',
                'color': 'darker_flame',
                'icon': 'k',
                'ability_scores': [9, 14, 12],
                'hit_dice': '1d4',
                'dmg_dice_unarmed': '1d3+1',
                'keywords': [],
                'weapon': ['light'],
                'speed': 0.95,
                'proficiency': 3,
                'ac_bonus': 1
            },
            {
                'name': 'kobold warrior',
                'color': 'darkest_flame',
                'icon': 'k',
                'ability_scores': [9, 14, 12],
                'hit_dice': '1d5',
                'dmg_dice_unarmed': '1d3+2',
                'keywords': [],
                'weapon': ['light'],
                'speed': 0.95,
                'proficiency': 3,
                'ac_bonus': 2
            }
        ]
    },
    'goblins':
    {
        'level_range': (0, 7),
        'occurrences': {
            0: (4, 1, 0, 0),
            1: (1, 1, 0, 0),
            2: (1, 3, 0, 0),
            3: (1, 3, 3, 0),
            4: (0, 2, 2, 1),
            5: (0, 1, 3, 3),
            6: (0, 0, 1, 2),
            7: (0, 0, 1, 4)
        },
        'subtypes': [
            {
                'name': 'goblin wanderer',
                'color': 'darker_sea',
                'icon': 'g',
                'ability_scores': [8, 12, 8],
                'hit_dice': '1d6',
                'dmg_dice_unarmed': '1d3+1',
                'keywords': [],
                'speed': 0.95,
                'proficiency': 2,
                'ac_bonus': 1
            },
            {
                'name': 'goblin guard',
                'color': 'darker_sea',
                'icon': 'g',
                'ability_scores': [9, 12, 12],
                'hit_dice': '1d5',
                'dmg_dice_unarmed': '1d2+2',
                'keywords': [],
                'weapon': ['light'],
                'speed': 0.95,
                'proficiency': 3,
                'ac_bonus': 2
            },
            {
                'name': 'goblin warrior',
                'color': 'darker_sea',
                'icon': 'g',
                'ability_scores': [9, 12, 14],
                'hit_dice': '1d5',
                'dmg_dice_unarmed': '1d4+1',
                'keywords': [],
                'weapon': ['light'],
                'speed': 0.95,
                'proficiency': 4,
                'ac_bonus': 2
            },
            {
                'name': 'goblin champion',
                'color': 'darker_sea',
                'icon': 'g',
                'ability_scores': [10, 12, 14],
                'hit_dice': '1d6',
                'dmg_dice_unarmed': '1d4+1',
                'keywords': [],
                'weapon': ['light'],
                'speed': 0.95,
                'proficiency': 4,
                'ac_bonus': 3
            }
        ]
    },
    'orcs':
    {
        'level_range': (2, 8),
        'occurrences': {
            2: (3, 2, 1, 0, 0),
            3: (1, 1, 1, 0, 0),
            4: (1, 2, 3, 1, 0),
            5: (0, 1, 1, 1, 0),
            6: (0, 1, 2, 2, 0),
            7: (0, 0, 1, 2, 1),
            8: (0, 0, 0, 2, 1)
        },
        'subtypes': [
            {
                'name': 'hobgoblin warrior',
                'color': 'darker_crimson',
                'icon': 'g',
                'ability_scores': [10, 12, 10],
                'hit_dice': '1d8',
                'dmg_dice_unarmed': '1d6',
                'keywords': [],
                'weapon': ['versatile'],
                'speed': 1.0,
                'proficiency': 2,
                'ac_bonus': 2
            },
            {
                'name': 'hobgoblin officer',
                'color': 'darker_crimson',
                'icon': 'g',
                'ability_scores': [12, 12, 12],
                'hit_dice': '1d7',
                'dmg_dice_unarmed': '1d5-1',
                'keywords': [],
                'weapon': ['versatile'],
                'speed': 1.0,
                'proficiency': 2,
                'ac_bonus': 3
            },
            {
                'name': 'orc warrior',
                'color': 'darker_amber',
                'icon': 'g',
                'ability_scores': [12, 12, 14],
                'hit_dice': '1d7',
                'dmg_dice_unarmed': '1d6',
                'keywords': [],
                'weapon': ['versatile'],
                'speed': 1.0,
                'proficiency': 2,
                'ac_bonus': 3
            },
            {
                'name': 'orc officer',
                'color': 'darker_amber',
                'icon': 'g',
                'ability_scores': [14, 12, 16],
                'hit_dice': '1d6',
                'dmg_dice_unarmed': '1d5',
                'keywords': [],
                'weapon': ['versatile'],
                'speed': 1.1,
                'proficiency': 2,
                'ac_bonus': 4
            },
            {
                'name': 'orc chieftain',
                'color': 'darker_amber',
                'icon': 'G',
                'ability_scores': [14, 14, 18],
                'hit_dice': '1d6',
                'dmg_dice_unarmed': '1d6',
                'keywords': [],
                'weapon': ['versatile'],
                'speed': 1.2,
                'proficiency': 2,
                'ac_bonus': 4
            }
        ]
    },
    'skeletons':
    {
        'level_range': (0, 8),
        'occurrences': {
            0: (2, 1, 0, 0, 0, 0),
            1: (1, 2, 1, 0, 0, 0),
            2: (1, 2, 3, 1, 0, 0),
            3: (0, 1, 2, 2, 0, 0),
            4: (0, 1, 3, 3, 0, 0),
            5: (0, 0, 1, 2, 1, 0),
            6: (0, 0, 0, 3, 2, 1),
            7: (0, 0, 0, 1, 2, 1),
            8: (0, 0, 0, 0, 2, 1)
        },
        'subtypes': [
            {
                'name': 'canine skeleton',
                'color': 'lightest_orange',
                'icon': 's',
                'ability_scores': [6, 12, 10],
                'hit_dice': '1d5',
                'dmg_dice_unarmed': '1d3+2',
                'keywords': [],
                'speed': 0.90,
                'proficiency': 5,
                'ac_bonus': 0
            },
            {
                'name': 'goblinoid skeleton',
                'color': 'lightest_lime',
                'icon': 's',
                'ability_scores': [7, 12, 10],
                'hit_dice': '1d6',
                'dmg_dice_unarmed': '1d4+2',
                'keywords': [],
                'speed': 1.0,
                'proficiency': 4,
                'ac_bonus': 1
            },
            {
                'name': 'humanoid skeleton',
                'color': 'lightest_grey',
                'icon': 's',
                'ability_scores': [10, 12, 10],
                'hit_dice': '1d7',
                'dmg_dice_unarmed': '1d4+1',
                'keywords': [],
                'speed': 1.05,
                'proficiency': 2,
                'ac_bonus': 0
            },
            {
                'name': 'orc skeleton',
                'color': 'lightest_red',
                'icon': 's',
                'ability_scores': [12, 12, 10],
                'hit_dice': '1d8',
                'dmg_dice_unarmed': '1d4+1',
                'keywords': [],
                'speed': 1.10,
                'proficiency': 2,
                'ac_bonus': 1
            },
            {
                'name': 'monstrous skeleton',
                'color': 'light_yellow',
                'icon': 's',
                'ability_scores': [12, 14, 12],
                'hit_dice': '1d8',
                'dmg_dice_unarmed': '1d6',
                'keywords': [],
                'speed': 1.15,
                'proficiency': 2,
                'ac_bonus': 1
            },
            {
                'name': 'skeletal golem',
                'color': 'white',
                'icon': 'S',
                'ability_scores': [14, 10, 20],
                'hit_dice': '1d5',
                'dmg_dice_unarmed': '1d6',
                'keywords': [],
                'speed': 1.25,
                'proficiency': 2,
                'ac_bonus': 4
            }
        ]
    }
}
