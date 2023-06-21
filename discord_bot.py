import discord
import os
import requests
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
bot_token=os.getenv("BOT_TOKEN")


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

@bot.command()
async def ask(ctx, *, question):
    #url = 'http://127.0.0.1:8000/gpt'
    url = ''
    data = {'user_input': question}
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        response_json = response.json()

        if 'output' in response_json:
            await ctx.send(f"{ctx.author.mention}, {response_json['output']}")
        else:
            await ctx.send(f"{ctx.author.mention}, The 'output' key was not found in the API response.")
    else:
        await ctx.send(f"{ctx.author.mention}, *Sad beep* - I'm sorry I couldn't understand your question, please ask me again.")

bot.run(bot_token)
