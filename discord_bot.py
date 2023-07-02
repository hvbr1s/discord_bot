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
    await ctx.send('Hello, how can I help?')

@bot.command()
@commands.cooldown(1, 20, commands.BucketType.user)
async def ask(ctx, *, question):
    #url = 'http://127.0.0.1:8000/gpt'
    url = 'http://34.163.86.35:80/gpt'
    data = {'user_input': question}
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        response_json = response.json()

        if 'output' in response_json:
            await ctx.reply(f"{response_json['output']}")
        else:
            await ctx.reply(f"The 'output' key was not found in the API response.")
    else:
        await ctx.reply(f"*Sad beep* - I'm sorry I couldn't understand your question, please ask me again.")

@ask.error
async def ask_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = 'Not too fast! Please ask me again in {:.0f}s.'.format(error.retry_after)
        await ctx.reply(msg)
    else:
        raise error

bot.run(bot_token)

