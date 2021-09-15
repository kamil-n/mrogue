# -*- coding: utf-8 -*-

import mrogue.item
import mrogue.unit
import mrogue.utils


class Effect:
    def __init__(self, messenger, from_item: mrogue.item.Consumable, for_unit: mrogue.unit.Unit):
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
            for i in range(len(self.target.equipped) - 1, -1, -1):
                if self.target.equipped[i].enchantment_level < 0:
                    self.target.unequip(self.target.equipped[i], force=True)

        elif keyword == 'heal':
            self.target.heal(mrogue.utils.roll(self.source.effect.split()[1]))
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
