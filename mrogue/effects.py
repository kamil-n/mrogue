# -*- coding: utf-8 -*-
""""Module providing on-use effect implementation for consumables, spells, etc.

Classes:
    * Effect - an action or change of state to be triggered
"""
import mrogue.item
import mrogue.message
import mrogue.timers
import mrogue.unit
import mrogue.utils


class Effect:
    """Describes what will change at a specified moment.

    Currently defines feedback message and optionally a following effect
    (after a delay handled using Timer class).

    Methods:
        * apply() - make some changes and inform the player
    """

    def __init__(self, from_item: mrogue.item.Consumable, for_unit: mrogue.unit.Unit):
        """Define the source of the Effect (it must provide instructions) and a target - usually an Unit."""
        self.source = from_item
        self.target = for_unit

    def apply(self) -> str:
        """Perform the action described by the first word of the attribute 'effect', then gives feedback.
        Currently supports following keywords: 'identify', 'decurse', 'heal x' and 'ac_bonus x(hp) y(turns)'

        :return: a feedback message to be displayed to the player
        """
        feedback = ''
        keyword = self.source.effect.split()[0]

        # identify all items in the inventory
        if keyword == 'identify':
            for i in self.target.inventory:
                if not i.status_identified:
                    i.identified()
            feedback = 'Unknown items have been identified.'

        # remove all equipped cursed items
        elif keyword == 'decurse':
            for i in range(len(self.target.equipped) - 1, -1, -1):
                if self.target.equipped[i].enchantment_level < 0:
                    self.target.unequip(self.target.equipped[i], force=True)

        # heal a random amount of health points
        elif keyword == 'heal':
            self.target.heal(mrogue.utils.roll(self.source.effect.split()[1]))
            feedback = 'Some of your wounds are healed.'

        # grant additional armor for a duration
        elif keyword == 'ac_bonus':
            arg = int(self.source.effect.split()[1])
            duration = int(self.source.effect.split()[2])

            def lower_ac():
                self.target.armor_class -= arg
                mrogue.message.Messenger.add('Your skin turns back to normal.')

            mrogue.timers.Timer(duration, lower_ac)
            self.target.armor_class += arg
            feedback = 'Your skin turns into scales.'
        return feedback
