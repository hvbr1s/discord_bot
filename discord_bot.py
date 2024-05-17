import discord
import os
import re
import nltk
if not nltk.data.find('tokenizers/punkt'):
    nltk.download('punkt')
from nltk.tokenize import word_tokenize
from discord.ext import commands
from discord import Thread
from dotenv import main
import aiohttp
import asyncio

main.load_dotenv()
bot_token=os.getenv("BOT_TOKEN")

ETHEREUM_ADDRESS_PATTERN = r'\b0x[a-fA-F0-9]{40}\b'
BITCOIN_ADDRESS_PATTERN = r'\b(1|3)[1-9A-HJ-NP-Za-km-z]{25,34}\b|bc1[a-zA-Z0-9]{25,90}\b'
LITECOIN_ADDRESS_PATTERN = r'\b(L|M)[a-km-zA-HJ-NP-Z1-9]{26,34}\b'
DOGECOIN_ADDRESS_PATTERN = r'\bD{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}\b'
XRP_ADDRESS_PATTERN = r'\br[a-zA-Z0-9]{24,34}\b'
COSMOS_ADDRESS_PATTERN = r'\bcosmos[0-9a-z]{38,45}\b'
SOLANA_ADDRESS_PATTERN= r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
thread_counter = 0

async def answer_question(ctx, question):
   global thread_counter
   #url = 'http://127.0.0.1:8800/chat'
   url = 'https://retailbot.staging.aws.ledger.fr/agent'
# Append thread id to user id if the context is a thread
   user_id = str(ctx.author.id)
   if isinstance(ctx.channel, Thread):
       user_id += f"-{ctx.channel.id}"
   data = {'user_input': question, 'user_id': user_id, 'user_locale':'eng'}
   headers = {'Content-Type': 'application/json', "Authorization": f"Bearer {os.getenv('BACKEND_API_KEY')}"}

   async with aiohttp.ClientSession() as session:
       try:
           async with session.post(url, json=data, headers=headers) as response:
               if response.status == 200:
                  response_json = await response.json()
                  if 'output' in response_json:
                      if not isinstance(ctx.channel, Thread):  # Check if the message is not in a thread
                          thread_counter += 1
                          thread = await ctx.create_thread(name=f"SamanthaBot#{thread_counter}")
                          await thread.send(f"{response_json['output']}")
                      else:  # If the message is in a thread, reply to the message instead
                          await ctx.reply(f"{response_json['output']}")
                  else:
                      if not isinstance(ctx.channel, Thread):
                          thread_counter += 1
                          thread = await ctx.create_thread(name=f"SamanthaBot#{thread_counter}")
                          await thread.send(f"The 'output' key was not found in the API response.")
                      else:
                          await ctx.reply(f"The 'output' key was not found in the API response.")
               else:
                  if not isinstance(ctx.channel, Thread):
                      thread_counter += 1
                      thread = await ctx.create_thread(name=f"SamanthaBot#{thread_counter}")
                      await thread.send(f"*Sad beep* - I'm sorry I couldn't reach my knowledge base. Please try again later.")
                  else:
                      await ctx.reply(f"*Sad beep* - I'm sorry I couldn't reach my knowledge base. Please try again later.")
       except Exception as e:
           print(f"Error occurred while sending request: {e}")
           if not isinstance(ctx.channel, Thread):
               thread_counter += 1
               thread = await ctx.create_thread(name=f"SamanthaBot#{thread_counter}")
               await thread.send(f"*Sad beep* - I'm sorry I couldn't reach my knowledge base. Please try again later.")
           else:
               await ctx.reply(f"*Sad beep* - I'm sorry I couldn't reach my knowledge base. Please try again later.")
@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        question = message.content.replace(f'<@!{bot.user.id}>', '').strip()  # extract question

        # Check for crypto addresses
        if re.search(ETHEREUM_ADDRESS_PATTERN, question, re.IGNORECASE) or \
           re.search(BITCOIN_ADDRESS_PATTERN, question, re.IGNORECASE) or \
           re.search(LITECOIN_ADDRESS_PATTERN, question, re.IGNORECASE) or \
           re.search(DOGECOIN_ADDRESS_PATTERN, question, re.IGNORECASE) or \
           re.search(COSMOS_ADDRESS_PATTERN, question, re.IGNORECASE) or \
           re.search(SOLANA_ADDRESS_PATTERN, question, re.IGNORECASE) or \
           re.search(XRP_ADDRESS_PATTERN, question, re.IGNORECASE):
            await message.reply("I'm sorry, but I can't assist with questions that include crypto addresses. Please remove the address and ask again.")
        else:
            # Create a task for answer_question
            task = asyncio.create_task(answer_question(message, question))

            # Wait for 5 seconds to see if the task completes
            done, pending = await asyncio.wait({task}, timeout=15)

            # If the task is still pending after 5 seconds, send an interim response
            if task in pending:
                await message.reply("Thanks, I am checking my knowledge base, it usually takes me about 20 seconds.")

            # Wait for the task to complete and get the result
            await task

    await bot.process_commands(message)

@bot.command()
@commands.cooldown(1, 20, commands.BucketType.user)
async def ask(ctx, *, question):
    if re.search(ETHEREUM_ADDRESS_PATTERN, question, re.IGNORECASE) or re.search(BITCOIN_ADDRESS_PATTERN, question, re.IGNORECASE):
        await ctx.reply("I'm sorry, but I can't assist with questions that include Ethereum or Bitcoin addresses. Please remove the address and ask again.")
    else:
        try:
            await answer_question(ctx, question)
        except discord.errors.Forbidden as e:
            print(f"Missing permissions to create a thread or reply: {e}")
            # Optionally, log this error to a file or external logging service
            await ctx.send("I don't have the permissions to create threads or reply in this channel.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # Handle other unexpected errors gracefully
            await ctx.send("An error occurred, please try again later.")
@ask.error
async def ask_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = 'Not too fast! Please ask me again in {:.0f}s.'.format(error.retry_after)
        await ctx.reply(msg)
    else:
        raise error

bot.run(bot_token)

# start command: pm2 start discord_bot.py --interpreter=python3
# stop command: pm2 stop discord_bot
