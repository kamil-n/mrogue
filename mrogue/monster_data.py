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
                'icon': 0x72,
                'ability_scores': [3, 14, 10],
                'hp_range': (1, 2),
                'dmg_range_unarmed': (0, 1),
                'keywords': ['finesse'],
                'speed': 0.75,
                'proficiency': 0,
                'ac_bonus': 1
            },
            {
                'name': 'rat',
                'color': 'dark_grey',
                'icon': 0x72,
                'ability_scores': [4, 14, 10],
                'hp_range': (1, 3),
                'dmg_range_unarmed': (0, 1),
                'keywords': ['finesse'],
                'speed': 0.75,
                'proficiency': 0,
                'ac_bonus': 1
            },
            {
                'name': 'dire rat',
                'color': 'grey',
                'icon': 0x72,
                'ability_scores': [6, 14, 12],
                'hp_range': (1, 3),
                'dmg_range_unarmed': (1, 1),
                'keywords': ['finesse'],
                'speed': 0.75,
                'proficiency': 0,
                'ac_bonus': 1
            },
            {
                'name': 'rat matriarch',
                'color': 'lighter_grey',
                'icon': 0x52,
                'ability_scores': [8, 14, 14],
                'hp_range': (1, 4),
                'dmg_range_unarmed': (1, 1),
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
                'icon': 0x6B,
                'ability_scores': [8, 14, 10],
                'hp_range': (1, 4),
                'dmg_range_unarmed': (0, 2),
                'keywords': [],
                'speed': 0.95,
                'proficiency': 2,
                'ac_bonus': 0
            },
            {
                'name': 'kobold guard',
                'color': 'darker_flame',
                'icon': 0x6B,
                'ability_scores': [9, 14, 12],
                'hp_range': (1, 4),
                'dmg_range_unarmed': (1, 3),
                'keywords': [],
                'weapon': 'light',
                'speed': 0.95,
                'proficiency': 3,
                'ac_bonus': 1
            },
            {
                'name': 'kobold warrior',
                'color': 'darkest_flame',
                'icon': 0x6B,
                'ability_scores': [9, 14, 12],
                'hp_range': (1, 5),
                'dmg_range_unarmed': (2, 3),
                'keywords': [],
                'weapon': 'light',
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
                'icon': 0x67,
                'ability_scores': [8, 12, 8],
                'hp_range': (1, 6),
                'dmg_range_unarmed': (1, 3),
                'keywords': [],
                'speed': 0.95,
                'proficiency': 2,
                'ac_bonus': 1
            },
            {
                'name': 'goblin guard',
                'color': 'darker_sea',
                'icon': 0x67,
                'ability_scores': [9, 12, 12],
                'hp_range': (1, 5),
                'dmg_range_unarmed': (2, 3),
                'keywords': [],
                'weapon': 'light',
                'speed': 0.95,
                'proficiency': 3,
                'ac_bonus': 2
            },
            {
                'name': 'goblin warrior',
                'color': 'darker_sea',
                'icon': 0x67,
                'ability_scores': [9, 12, 14],
                'hp_range': (1, 5),
                'dmg_range_unarmed': (2, 4),
                'keywords': [],
                'weapon': 'light',
                'speed': 0.95,
                'proficiency': 4,
                'ac_bonus': 2
            },
            {
                'name': 'goblin champion',
                'color': 'darker_sea',
                'icon': 0x67,
                'ability_scores': [10, 12, 14],
                'hp_range': (1, 6),
                'dmg_range_unarmed': (2, 5),
                'keywords': [],
                'weapon': 'light',
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
                'icon': 0x67,
                'ability_scores': [10, 12, 10],
                'hp_range': (1, 8),
                'dmg_range_unarmed': (1, 4),
                'keywords': [],
                'weapon': 'versatile',
                'speed': 1.0,
                'proficiency': 2,
                'ac_bonus': 2
            },
            {
                'name': 'hobgoblin officer',
                'color': 'darker_crimson',
                'icon': 0x67,
                'ability_scores': [12, 12, 12],
                'hp_range': (1, 5),
                'dmg_range_unarmed': (2, 4),
                'keywords': [],
                'weapon': 'versatile',
                'speed': 1.0,
                'proficiency': 2,
                'ac_bonus': 3
            },
            {
                'name': 'orc warrior',
                'color': 'darker_amber',
                'icon': 0x67,
                'ability_scores': [12, 12, 14],
                'hp_range': (1, 6),
                'dmg_range_unarmed': (2, 5),
                'keywords': [],
                'weapon': 'versatile',
                'speed': 1.0,
                'proficiency': 2,
                'ac_bonus': 3
            },
            {
                'name': 'orc officer',
                'color': 'darker_amber',
                'icon': 0x67,
                'ability_scores': [14, 12, 16],
                'hp_range': (1, 6),
                'dmg_range_unarmed': (3, 5),
                'keywords': [],
                'weapon': 'versatile',
                'speed': 1.1,
                'proficiency': 2,
                'ac_bonus': 4
            },
            {
                'name': 'orc chieftain',
                'color': 'darker_amber',
                'icon': 0x47,
                'ability_scores': [14, 14, 18],
                'hp_range': (1, 6),
                'dmg_range_unarmed': (3, 6),
                'keywords': [],
                'weapon': 'versatile',
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
                'icon': 0x73,
                'ability_scores': [6, 12, 10],
                'hp_range': (1, 5),
                'dmg_range_unarmed': (1, 3),
                'keywords': [],
                'speed': 0.90,
                'proficiency': 5,
                'ac_bonus': 0
            },
            {
                'name': 'goblinoid skeleton',
                'color': 'lightest_lime',
                'icon': 0x73,
                'ability_scores': [7, 12, 10],
                'hp_range': (1, 6),
                'dmg_range_unarmed': (1, 4),
                'keywords': [],
                'speed': 1.0,
                'proficiency': 4,
                'ac_bonus': 1
            },
            {
                'name': 'humanoid skeleton',
                'color': 'lightest_grey',
                'icon': 0x73,
                'ability_scores': [10, 12, 10],
                'hp_range': (1, 7),
                'dmg_range_unarmed': (2, 4),
                'keywords': [],
                'speed': 1.05,
                'proficiency': 2,
                'ac_bonus': 0
            },
            {
                'name': 'orc skeleton',
                'color': 'lightest_red',
                'icon': 0x73,
                'ability_scores': [12, 12, 10],
                'hp_range': (1, 8),
                'dmg_range_unarmed': (1, 4),
                'keywords': [],
                'speed': 1.10,
                'proficiency': 2,
                'ac_bonus': 1
            },
            {
                'name': 'monstrous skeleton',
                'color': 'light_yellow',
                'icon': 0x73,
                'ability_scores': [12, 14, 12],
                'hp_range': (1, 8),
                'dmg_range_unarmed': (3, 5),
                'keywords': [],
                'speed': 1.15,
                'proficiency': 2,
                'ac_bonus': 1
            },
            {
                'name': 'skeletal golem',
                'color': 'white',
                'icon': 0x53,
                'ability_scores': [14, 10, 20],
                'hp_range': (1, 5),
                'dmg_range_unarmed': (4, 6),
                'keywords': [],
                'speed': 1.25,
                'proficiency': 2,
                'ac_bonus': 4
            }
        ]
    }
}
