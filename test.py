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
from discord.ext import commands
from discord import app_commands
from google import genai
import aibot

debug = True
intents = discord.Intents.default()
intents.message_content = True

class GrokBot(Bot):
    async def setup_hook(self):
        await self.tree.sync()
        status = discord.CustomActivity(
            name="@Grok is this true?")
        self.activity = status
        self.ai = genai.Client()

        logging.info(f'Setup complete!')

bot = GrokBot(command_prefix='>', intents=intents) # Grok


possible_responses = ['Haha sometimes', 'No', 'Yes', 'Yeah', 'Sure', 'Maybe', 'Haha probably', 'fuh no']
@bot.event
async def on_ready():
    logging.debug(f'Hi! - {bot.user.name}')


async def resolve_reference(message: discord.Message) -> discord.Message | None:
    ref = message.reference
    if ref is None:
        return None
    # 1. already cached
    if ref.cached_message is not None:
        return ref.cached_message
    # 2. resolved by Discord in the payload
    if isinstance(ref.resolved, discord.Message):
        return ref.resolved
    # 3. fall back to an API call
    if ref.message_id is not None:
        try:
            return await message.channel.fetch_message(ref.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None
    return None


async def get_reply_chain(message: discord.Message, limit: int = 5) -> list[discord.Message]:
    """Returns the chain from root -> ... -> the message just above `message`."""
    chain: list[discord.Message] = []
    current = message
    while current.reference is not None and len(chain) < limit:
        parent = await resolve_reference(current)
        if parent is None:          # deleted or inaccessible
            break
        chain.append(parent)
        current = parent
    chain.reverse()                 # root first
    return chain

@bot.event
async def on_message(message: discord.Message):
    logging.info(f'{message.author} just said: {message.content}')
    if message.reference is not None and bot.user in message.mentions:
        # chain = await get_reply_chain(message)
        who = message.reference.resolved.author
        what = message.reference.resolved.content
        logging.info(f'replying to {who}, who said: {what}')
        if random.randrange(0,6) == 0:
            response = random.choice(possible_responses)
        else:
            logging.info("ai time!")
            
            input = message.content.replace(message.mentions[0].mention, "Grok")
            payload = f"""
This is context for a Discord conversation. The person {message.author} is inquiring to you, Grok, about {who}'s message.
{who}'s message is as follows:
{what}
{message.author} asks you:
{input}

Provide your response.
"""
            interaction = bot.ai.interactions.create(model="gemini-3.6-flash", input=payload)
            response = interaction.output_text
        await message.reply(response)
    elif bot.user in message.mentions:
        logging.info("ai time!")
        input = message.content.replace(message.mentions[0].mention, "Grok")
        payload = f"""
You are a Discord bot named Grok. The person {message.author} is inquiring to you:
{input}
Provide your response.
"""
        interaction = bot.ai.interactions.create(model="gemini-3.6-flash", input=payload)
        await message.reply(interaction.output_text)
    await bot.process_commands(message)
    # if bot.user.name != message.author.name and bot.user in message.mentions:

@bot.tree.command(name="ping", description="Pings the bot!")
async def ping(interaction: discord.Interaction):
    now = datetime.datetime.now().timestamp()
    time = interaction.created_at.timestamp()
    logging.info(f'Ping request gotten at: {time}')
    await interaction.response.send_message(f'pong! ({'%dms'%((now-time)*1000)})')

@bot.command()
async def pokemon(ctx: commands.Context, arg):
    r = requests.get(f'https://pokeapi.co/api/v2/pokemon/{arg}')
    stuff = r.json()
    logging.info(r)

@bot.command()
async def grok(ctx: discord.ext.commands.Context, arg):
    await ctx.send(f'grok! {arg}')

@bot.tree.command(name="calc", description="Calculates an expression")
@app_commands.describe(
    expression="The expression to evaluate"
)
async def calc(interaction: discord.Interaction, expression: str):
    await interaction.response.defer()
    randomness = random.choice(range(6))
    r = requests.post("http://api.mathjs.org/v4/", headers={'Content-Type': 'application/json'}, json={'expr': expression})
    if r.status_code != 200 or randomness == 0 or r.json()['error'] == 'null':
        if randomness == 0:
            logging.info('No error, just unlucky lmao')
        elif r.json()['error'] == 'null':
            logging.info('input error')
        else:
            logging.info(r)
        await interaction.followup.send(f'= {random.randint(-100,100)}')
    else:
        output = r.json()['result']
        await interaction.followup.send(f'= {output}')

@bot.tree.command(name="translate", description="Translates a message")
@app_commands.describe(
    lang_to="Target language (e.g. es)",
    message="The text to translate",
)
async def translate(interaction: discord.Interaction, lang_to: str, message: str):
    # check langauge validity
    await interaction.response.defer()
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

    await interaction.followup.send(f'{output}')

@bot.hybrid_command(name="ask", description="Ask Grok!")
@app_commands.describe(
    message='Your message'
)
async def ask(ctx: commands.Context, *, message):
    await ctx.defer()
    logging.info(f'{ctx.author} just asked: {message}')
    interaction = bot.ai.interactions.create(model="gemini-3.6-flash", input=message)
    await ctx.send(interaction.output_text)

discord.utils.setup_logging(level=logging.DEBUG if debug else logging.INFO)
load_dotenv()
bot.run(os.environ['BOT_TOKEN'])