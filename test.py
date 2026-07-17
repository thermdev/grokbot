# /// script
# requires-python = ">=X.XX" TODO: Update this to the minimum Python version you want to support
# dependencies = [
#   TODO: Add any dependencies your script requires
# ]
# ///

# TODO: Update the main function to your needs or remove it.
import requests
from dotenv import load_dotenv
import discord
import logging
import os
from discord.ext.commands import Bot

debug = True
intents = discord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix='!', intents=intents) # Grok
@bot.event
async def on_ready():
    logging.debug(f'Hi! - {bot.user.name}')

@bot.event
async def on_message(message: discord.Message):
    logging.info(f'{message.author} just said: {message.content}')
    if bot.user.name != message.author.name:
        await message.channel.send("Hi")

discord.utils.setup_logging(level=logging.DEBUG if debug else logging.INFO)
load_dotenv()
bot.run(os.environ['BOT_TOKEN'])