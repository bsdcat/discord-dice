import argparse
import discord
import os
import random
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


intents = discord.Intents.default()
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
        count = int(dice_format.group('count')) or 1
        die = int(dice_format.group('die'))
        keep = int(dice_format.group('keep')) or count
        hilo = dice_format.group('hilo') or 'h'
        dice = [random.randint(1, die) for x in range(count)]
        if keep < count:
            dice.sort()
            if hilo == 'h':
                dice.reverse
        response = ''
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
