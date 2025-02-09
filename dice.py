import argparse
from collections import defaultdict
import discord
import os
from random import Random
import re
import sys
import unittest

from discord.ext import commands
from dotenv import load_dotenv

DICE_RE = '^(?P<count>\\d+)?d(?P<die>\\d+)(?:k(?P<keep>\\d+)(?P<hilo>[hl])?)?$'


class DiceRETest(unittest.TestCase):
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


random = Random()


def perform_roll(die: int,
                 count: int = 1, keep: int = 0, hilo: str = 'h'
                 ) -> tuple[list[int], list[int]]:
    if keep == 0 or keep > count:
        keep = count
    dice = [random.randint(1, die) for x in range(count)]
    in_order = sorted(dice)
    if hilo == 'h':
        in_order.reverse()
    kept = in_order[0:keep]
    return dice, kept


def format_dice(dice: list[int], kept: list[int]) -> str:
    kept_dict = defaultdict(int)
    for die in kept:
        kept_dict[die] += 1
    dice_strs = []
    for die in dice:
        if kept_dict[die] > 0:
            dice_strs.append(f'**{die}**')
            kept_dict[die] -= 1
        else:
            dice_strs.append(f'{die}')
    response = ', '.join(dice_strs)
    if len(kept) > 1:
        response += f' (sum = {sum(kept)})'
    return response


class DiceRollTest(unittest.TestCase):
    def setUp(self) -> None:
        global random
        random = Random(12345)

    def test_5_for_5(self) -> None:
        dice, kept = perform_roll(20, count=5)
        self.assertEqual(dice, [14, 1, 10, 12, 7], "5 random dice")
        self.assertEqual(kept, [14, 12, 10, 7, 1], "5 random dice from high")

    def test_5_for_5_low(self) -> None:
        dice, kept = perform_roll(20, count=5, hilo='l')
        self.assertEqual(kept, [1, 7, 10, 12, 14], "5 random dice from low")

    def test_roll_2_keep_high(self) -> None:
        dice, kept = perform_roll(20, count=2, keep=1)
        self.assertEqual(dice, [14, 1], "2 dice keep high")
        self.assertEqual(kept, [14], "1 high die kept")

    def test_roll_2_keep_low(self) -> None:
        dice, kept = perform_roll(20, count=2, keep=1, hilo='l')
        self.assertEqual(dice, [14, 1], "2 dice keep low")
        self.assertEqual(kept, [1], "1 low die kept")

    def test_other_dice(self) -> None:
        dice, kept = perform_roll(6, count=3)
        self.assertEqual(dice, [4, 6, 1], "3 6-sided dice")

    def test_formatting(self) -> None:
        dice, kept = perform_roll(20, count=2, keep=1)
        response = format_dice(dice, kept)
        self.assertEqual(response, '**14**, 1',
                         "formatting advantage roll")

    def test_formatting_sum(self) -> None:
        dice, kept = perform_roll(6, count=3, keep=3)
        response = format_dice(dice, kept)
        self.assertEqual(response, '**4**, **6**, **1** (sum = 11)',
                         "formatting 3d6")

    def test_formatting_repeated(self) -> None:
        dice, kept = perform_roll(6, count=5, keep=2, hilo='l')
        response = format_dice(dice, kept)
        self.assertEqual(response, '4, 6, **1**, **3**, 3 (sum = 4)',
                         "formatting 5d6k2 with duplicates")


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
# Set the commands for your bot


@bot.command()
async def roll(ctx, dice: str):
    '''Rolls dice in [M]dN[kP[h|l]] format.'''
    dice_format = re.match(DICE_RE, dice)
    if dice_format is None:
        response = f"I didn't understand that: {dice}"
    else:
        count = 1
        if dice_format.group('count'):
            count = int(dice_format.group('count'))
        die = int(dice_format.group('die'))
        keep = count
        if dice_format.group('keep'):
            keep = min(int(dice_format.group('keep')), keep)
        hilo = dice_format.group('hilo') or 'h'
        dice, kept = perform_roll(die, count=count, keep=keep, hilo=hilo)
        response = format_dice(dice, kept)
    await ctx.send(response)


@bot.command()
async def list_command(ctx):
    response = '''
You can use the following commands:
\t!roll
\t!list_command
\t!functions
    '''
    await ctx.send(response)


@bot.command()
async def functions(ctx):
    response = 'I am a simple Discord chatbot! I will reply to your command!'
    await ctx.send(response)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Discord Dice Roller',
        description='Roll Dice as a Discord Bot')
    parser.add_argument('-t', '--test', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    if args.test:
        test_args = [sys.argv[0]]
        if args.verbose:
            test_args.append('--verbose')
        unittest.main(argv=test_args)
        exit(0)
    else:
        # Retrieve token from the .env file
        load_dotenv()
        bot.run(os.getenv('TOKEN'))
