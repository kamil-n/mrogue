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
        keyword, *args = self.source.effect.split()

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
            self.target.heal(mrogue.utils.roll(int(args[0]), int(args[1])))
            feedback = 'Some of your wounds are healed.'

        # grant additional armor for a duration
        elif keyword == 'ac_bonus':
            def lower_ac():
                self.target.armor_class -= int(args[0])
                mrogue.message.Messenger.add('Your skin turns back to normal.')

            mrogue.timers.Timer(int(args[1]), lower_ac)
            self.target.armor_class += int(args[0])
            feedback = 'Your skin turns into scales.'
        return feedback
