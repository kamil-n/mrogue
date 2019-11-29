# -*- coding: utf-8 -*-

from mrogue import roll
from mrogue.item import Consumable
from mrogue.unit import Unit


class Effect(object):
    def __init__(self, messenger, from_item: Consumable, for_unit: Unit):
        self.source = from_item
        self.target = for_unit
        self.messenger = messenger

    def apply(self):
        feedback = ''
        keyword = self.source.effect.split()[0]

        if keyword == 'identify':
            for i in self.target.inventory:
                if not i.status_identified:
                    i.identified()
            feedback = 'Unknown items have been identified.'

        elif keyword == 'decurse':
            for i in self.target.equipped:
                if i.enchantment_level < 0:
                    self.target.unequip(i)
            feedback = 'Cursed items have been unequipped.'

        elif keyword == 'heal':
            self.target.current_HP += roll(self.source.effect.split()[1])
            feedback = 'Some of your wounds are healed.'

        elif keyword == 'ac_bonus':
            arg = int(self.source.effect.split()[1])
            duration = int(self.source.effect.split()[2])

            def lower_ac():
                self.target.armor_class -= arg
                self.messenger.add('Your skin turns back to normal.')

            from mrogue.timers import Timer
            Timer(duration, lower_ac)
            self.target.armor_class += arg
            feedback = 'Your skin turns into scales.'
        return feedback
