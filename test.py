# /// script
# requires-python = ">=X.XX" TODO: Update this to the minimum Python version you want to support
# dependencies = [
#   TODO: Add any dependencies your script requires
# ]
# ///

# TODO: Update the main function to your needs or remove it.
import requests
import random
from dotenv import load_dotenv
import discord
import logging
import os
import datetime
import json
from discord.ext.commands import Bot
from discord import app_commands

debug = True
intents = discord.Intents.default()
intents.message_content = True

class GrokBot(Bot):
    async def setup_hook(self):
        await self.tree.sync()
        logging.info(f'Setup complete!')

bot = GrokBot(command_prefix='>', intents=intents) # Grok


possible_responses = ['Haha sometimes', 'No', 'Yes', 'Yeah', 'Sure', 'Maybe', 'Haha probably', 'fuh no']
@bot.event
async def on_ready():
    logging.debug(f'Hi! - {bot.user.name}')

@bot.event
async def on_message(message: discord.Message):
    logging.info(f'{message.author} just said: {message.content}')
    if message.reference is not None and bot.user in message.mentions:
        who = message.reference.cached_message.author
        what = message.reference.cached_message.content
        logging.info(f'replying to {who}, who said: {what}')
        response = random.choice(possible_responses)
        await message.reply(response)
    await bot.process_commands(message)
    # if bot.user.name != message.author.name and bot.user in message.mentions:

@bot.tree.command(name="ping", description="Pings the bot!")
async def ping(interaction: discord.Interaction):
    now = datetime.datetime.now().timestamp()
    time = interaction.created_at.timestamp()
    logging.info(f'Ping request gotten at: {time}')
    await interaction.response.send_message(f'pong! ({'%dms'%((now-time)*1000)})')

@bot.command()
async def pokemon(ctx: discord.ext.commands.Context, arg):
    r = requests.get(f'https://pokeapi.co/api/v2/pokemon/{arg}')
    stuff = r.json()
    logging.info(r)

@bot.command()
async def grok(ctx: discord.ext.commands.Context, arg):
    await ctx.send(f'grok! {arg}')

@bot.tree.command(name="translate", description="Translates a message")
@app_commands.describe(
    lang_to="Target language (e.g. es)",
    message="The text to translate",
)
async def translate(interaction: discord.Interaction, lang_to: str, message: str):
    # check langauge validity
    r = requests.get('https://api-free.deepl.com/v3/languages?resource=glossary', headers={
        'Content-Type': 'application/json',
        'Authorization': f'DeepL-Auth-Key {os.environ["DEEPL_API_KEY"]}'})
    logging.info(r)
    output = {_['lang']: _['usable_as_target'] for _ in r.json()}
    if lang_to not in output:
        await interaction.response.send_message(f'Sorry, {lang_to} is not supported.')
        return
    payload = {"text": [message], "target_lang": lang_to}
    r = requests.post('https://api-free.deepl.com/v2/translate', headers={
        'Content-Type': 'application/json',
        'Authorization': f'DeepL-Auth-Key {os.environ["DEEPL_API_KEY"]}'}, data=json.dumps(payload))
    output = r.json()["translations"][0]["text"]

    await interaction.response.send_message(f'{output}')


discord.utils.setup_logging(level=logging.DEBUG if debug else logging.INFO)
load_dotenv()
bot.run(os.environ['BOT_TOKEN'])