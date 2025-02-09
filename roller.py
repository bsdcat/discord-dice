from collections import defaultdict
import random
import re

import discord

DICE_RE = '^(?P<count>\\d+)?d(?P<die>\\d+)(?:k(?P<keep>\\d+)(?P<hilo>[hl])?)?$'
CONSTANT_RE = '^(?P<const>\\d+)$'
OP_RE = '^(?P<op>[+-])$'


def filter_empty(x: str) -> bool:
    '''Filter method for empty string arguments after reprocessing.'''
    if x is None:
        return False
    if re.match('^ *$', x):
        return False
    return True


class RollerBot(discord.Client):
    '''Dice rolling bot for Discord.

    It mainly handles a '!roll' command, and determines what dice to roll.

    A roll consists of one or more addition constants or roll directives,
    separating by '+' or '-' operators.

    Addition constants must be integers.

    Roll directives are of the form: [X]dY[kZ[h|l]] where
         X is the number of dice to roll
         Y is the upper value of the dice (e.g. 'd6' refers to a cube with
           numbers 1-6 on its faces)
         Z is the number of those dice to keep
         h|l refers to whether high dice, or low dice, should be kept
    '''

    async def on_ready(self) -> None:
        print(f'Logged in as {self.user}')
        return

    async def on_message(self, message) -> None:
        if message.author == self.user:
            return
        if not message.content.startswith('!'):
            return
        args = message.content.split(' ')
        args[0] = args[0][1:]
        await message.channel.send(self.process_message(args))

    def process_roll_args(self, args: list[str]) -> list[str]:
        arg_str = ' '.join(args)
        new_args = list(filter(
            filter_empty,
            re.split(r'([ +-])', arg_str)))
        return new_args

    def process_message(self, args: list[str]) -> str:
        match args[0]:
            case 'roll':
                return self.roll(self.process_roll_args(args)[1:])
            case 'commands' | 'list_command' | 'list_commands':
                return self.commands(args[1:])
            case _:
                return f"I don't understand {args[0]}"

    def roll(self, args: list[str]) -> str:
        response = ''
        my_sum = 0
        op = '+'
        first_arg = True
        for arg in args:
            op_match = re.match(OP_RE, arg)
            if op_match:
                match op_match.group('op'):
                    case '-':
                        match op:
                            case '-':
                                op = '+'
                            case '+':
                                op = '-'
                            case _:
                                op = '-'
                    case '+':
                        match op:
                            case '':
                                op = '+'
                first_arg = False
                continue

            const_match = re.match(CONSTANT_RE, arg)
            if const_match:
                match op:
                    case '+':
                        my_sum += int(const_match.group('const'))
                    case '-':
                        my_sum -= int(const_match.group('const'))
                    case _:
                        return f"I can't process {op=}"
                if (first_arg and op == '+'):
                    response += const_match.group('const') + ' '
                else:
                    response += f'{op} {const_match.group('const')} '
                first_arg = False
                op = ''
                continue

            dice_match = re.match(DICE_RE, arg)
            if dice_match:
                count = 1
                if dice_match.group('count'):
                    count = int(dice_match.group('count'))
                die = int(dice_match.group('die'))
                keep = count
                if dice_match.group('keep'):
                    keep = min(int(dice_match.group('keep')), keep)
                hilo = dice_match.group('hilo') or 'h'
                dice, kept = self.perform_roll(
                    die, count=count, keep=keep, hilo=hilo)
                match op:
                    case '+':
                        my_sum += sum(kept)
                    case '-':
                        my_sum -= sum(kept)
                    case _:
                        return f"I can't process {op=}"
                if len(args) > 1 and (not first_arg or op == '-'):
                    response += f'{op} '
                response += self.format_dice(dice, kept) + ' '
                op = ''
                first_arg = False
        if len(args) > 1:
            response += f'(sum = {my_sum})'
        return response

    def perform_roll(self, die: int,
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

    def format_dice(self, dice: list[int], kept: list[int]) -> str:
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
        response = '(' + ', '.join(dice_strs) + ')'
        return response
