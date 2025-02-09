import discord
from dotenv import load_dotenv
import os

from roller import RollerBot

if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.message_content = True
    # Retrieve token from the .env file
    load_dotenv()
    client = RollerBot(intents=intents)
    client.run(os.getenv('TOKEN'))
