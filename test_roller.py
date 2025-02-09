import discord
import random
import re
import unittest

from roller import DICE_RE, CONSTANT_RE, RollerBot


class DiceRETest(unittest.TestCase):
    bot: RollerBot

    def test_d20(self) -> None:
        my_match = re.match(DICE_RE, 'd20')
        self.assertNotEqual(my_match, None, 'dXX matches')
        self.assertEqual(my_match.group('count'), None, 'd20 has no count')
        self.assertEqual(my_match.group('die'), '20', 'd20')
        self.assertEqual(my_match.group('keep'), None, 'd20 has no keep')
        self.assertEqual(my_match.group('hilo'), None, 'd20 has no hilo')

    def test_1d20(self) -> None:
        my_match = re.match(DICE_RE, '1d20')
        self.assertNotEqual(my_match, None, 'XdXX matches')
        self.assertEqual(my_match.group('count'), '1', '1dXX')
        self.assertEqual(my_match.group('die'), '20', '1d20')
        self.assertEqual(my_match.group('keep'), None, '1d20 has no keep')
        self.assertEqual(my_match.group('hilo'), None, '1d20 has no hilo')

    def test_stray_hilo(self) -> None:
        my_match = re.match(DICE_RE, 'd20l')
        self.assertEqual(my_match, None, 'stray [hilo] fails')

    def test_stay_k(self) -> None:
        my_match = re.match(DICE_RE, 'd20k')
        self.assertEqual(my_match, None, 'stray k fails')

    def test_d20k1(self) -> None:
        my_match = re.match(DICE_RE, 'd20k1')
        self.assertNotEqual(my_match, None, 'dXXkX matches')
        self.assertEqual(my_match.group('count'), None, 'd20k1 has no count')
        self.assertEqual(my_match.group('die'), '20', 'd20kX')
        self.assertEqual(my_match.group('keep'), '1', 'dXXk1')
        self.assertEqual(my_match.group('hilo'), None, 'dXXkX has no hilo')

    def test_d20k1h(self) -> None:
        my_match = re.match(DICE_RE, 'd20k1h')
        self.assertNotEqual(my_match, None, 'dXXkXh matches')
        self.assertEqual(my_match.group('count'), None, 'd20k1h has no count')
        self.assertEqual(my_match.group('die'), '20', 'd20kX[hl]')
        self.assertEqual(my_match.group('keep'), '1', 'dXXk1[hl]')
        self.assertEqual(my_match.group('hilo'), 'h', 'dXXkXh')

    def test_constant(self) -> None:
        my_match = re.match(CONSTANT_RE, '300')
        self.assertNotEqual(my_match, None, 'XXX matches constant')
        self.assertEqual(my_match.group('const'), '300', '300 matches')

    def test_false_constant(self) -> None:
        my_match = re.match(CONSTANT_RE, '30.0')
        self.assertEqual(my_match, None, 'XX.X is not matched')
        my_match = re.match(CONSTANT_RE, '-30')
        self.assertEqual(my_match, None, '-XX is not matched')


class DiceRollTest(unittest.TestCase):
    def setUp(self) -> None:
        random.seed(12345)
        intents = discord.Intents.default()
        self.bot = RollerBot(intents=intents)

    def test_5_for_5(self) -> None:
        dice, kept = self.bot.perform_roll(20, count=5)
        self.assertEqual(dice, [14, 1, 10, 12, 7], "5 random dice")
        self.assertEqual(kept, [14, 12, 10, 7, 1], "5 random dice from high")

    def test_5_for_5_low(self) -> None:
        dice, kept = self.bot.perform_roll(20, count=5, hilo='l')
        self.assertEqual(kept, [1, 7, 10, 12, 14], "5 random dice from low")

    def test_roll_2_keep_high(self) -> None:
        dice, kept = self.bot.perform_roll(20, count=2, keep=1)
        self.assertEqual(dice, [14, 1], "2 dice keep high")
        self.assertEqual(kept, [14], "1 high die kept")

    def test_roll_2_keep_low(self) -> None:
        dice, kept = self.bot.perform_roll(20, count=2, keep=1, hilo='l')
        self.assertEqual(dice, [14, 1], "2 dice keep low")
        self.assertEqual(kept, [1], "1 low die kept")

    def test_other_dice(self) -> None:
        dice, kept = self.bot.perform_roll(6, count=3)
        self.assertEqual(dice, [4, 6, 1], "3 6-sided dice")

    def test_formatting(self) -> None:
        dice, kept = self.bot.perform_roll(20, count=2, keep=1)
        response = self.bot.format_dice(dice, kept)
        self.assertEqual(response, '(**14**, 1)',
                         "formatting advantage roll")

    def test_formatting_sum(self) -> None:
        dice, kept = self.bot.perform_roll(6, count=3, keep=3)
        response = self.bot.format_dice(dice, kept)
        self.assertEqual(response, '(**4**, **6**, **1**)',
                         "formatting 3d6")

    def test_formatting_repeated(self) -> None:
        dice, kept = self.bot.perform_roll(6, count=5, keep=2, hilo='l')
        response = self.bot.format_dice(dice, kept)
        self.assertEqual(response, '(4, 6, **1**, **3**, 3)',
                         "formatting 5d6k2 with duplicates")

    def test_process_roll_args_d20(self) -> None:
        args = self.bot.process_roll_args(['d20'])
        self.assertEqual(args, ['d20'], 'process_roll_args handles d20')

    def test_roll_method_d20(self) -> None:
        response = self.bot.roll(['d20'])
        self.assertEqual(response, '(**14**) ', 'roll formats d20')

    def test_process_roll_args_d20_plus_3(self) -> None:
        result = ['d20', '+', '3']
        args = self.bot.process_roll_args(['d20+3'])
        self.assertEqual(args, result, 'd20+3 split correctly')
        args = self.bot.process_roll_args(['d20+', '3'])
        self.assertEqual(args, result, 'd20+ 3 split correctly')
        args = self.bot.process_roll_args(['d20', '+', '3'])
        self.assertEqual(args, result, 'd20 + 3 split correctly')

    def test_roll_method_d20_plus_3(self) -> None:
        response = self.bot.roll(['d20', '+', '3'])
        self.assertEqual(
            response,
            '(**14**) + 3 (sum = 17)',
            'roll formats d20+3')

    def test_process_roll_args_3d8_plus_2d6(self) -> None:
        result = ['3d8', '+', '2d6']
        args = self.bot.process_roll_args(['3d8+2d6'])
        self.assertEqual(args, result, '3d8+2d6 split correctly')
        args = self.bot.process_roll_args(['3d8', '+', '2d6'])
        self.assertEqual(args, result, '3d8 + 2d6 split correctly')
        args = self.bot.process_roll_args(['3d8', '+2d6'])
        self.assertEqual(args, result, '3d8 +2d6 split correctly')

    def test_roll_method_3d8_plus_2d6(self) -> None:
        response = self.bot.roll(['3d8', '+', '2d6'])
        self.assertEqual(
            response,
            '(**7**, **1**, **5**) + (**3**, **2**) (sum = 18)',
            'roll formats 3d8 + 2d6')

    def test_roll_method_2d20k1_plus_5(self) -> None:
        response = self.bot.roll(['2d20k1h', '+', '5'])
        self.assertEqual(
            response,
            '(**14**, 1) + 5 (sum = 19)',
            'roll 2d20k1 + 5')

    def test_roll_method_initial_negative(self) -> None:
        response = self.bot.roll(['-', '5', '+', '2d20k1'])
        self.assertEqual(
            response,
            '- 5 + (**14**, 1) (sum = 9)',
            'roll method with inital negative')


if __name__ == '__main__':
    unittest.main()
