import discord
import os
import requests
import re
import nltk
if not nltk.data.find('tokenizers/punkt'):
    nltk.download('punkt')
from nltk.tokenize import word_tokenize
from discord.ext import commands
from dotenv import main

main.load_dotenv()
bot_token=os.getenv("BOT_TOKEN")

ETHEREUM_ADDRESS_PATTERN = r'\b0x[a-fA-F0-9]{40}\b'
BITCOIN_ADDRESS_PATTERN = r'\b(1|3)[1-9A-HJ-NP-Za-km-z]{25,34}\b|bc1[a-zA-Z0-9]{25,90}\b'
LITECOIN_ADDRESS_PATTERN = r'\b(L|M)[a-km-zA-HJ-NP-Z1-9]{26,34}\b'
DOGECOIN_ADDRESS_PATTERN = r'\bD{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32}\b'
XRP_ADDRESS_PATTERN = r'\br[a-zA-Z0-9]{24,34}\b'

# BIP39 Filter

def contains_bip39_phrase(message):
    words = word_tokenize(message.lower())
    bip39_words = [word for word in words if word in BIP39_WORDS]
    return len(bip39_words) >= 23

with open('bip39_words.txt', 'r') as file:
    BIP39_WORDS = set(word.strip() for word in file)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def answer_question(ctx, question):
    url = 'http://127.0.0.1:8008/gpt'
    data = {'user_input': question}
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # raise an HTTPError if the response contains an HTTP error status code

        response_json = response.json()

        if 'output' in response_json:
            await ctx.reply(f"{response_json['output']}")
        else:
            await ctx.reply(f"The 'output' key was not found in the API response.")
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while sending request: {e}")
        await ctx.reply(f"*Sad beep* - I'm sorry I couldn't reach my knowledge base. Please try again later.")

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        question = message.content.replace(f'<@!{bot.user.id}>', '').strip()  # extract question
        if re.search(ETHEREUM_ADDRESS_PATTERN, question, re.IGNORECASE) or re.search(BITCOIN_ADDRESS_PATTERN, question, re.IGNORECASE) or re.search(LITECOIN_ADDRESS_PATTERN, question, re.IGNORECASE) or re.search(DOGECOIN_ADDRESS_PATTERN, question, re.IGNORECASE) or re.search(XRP_ADDRESS_PATTERN, question, re.IGNORECASE) :
            await message.reply("I'm sorry, but I can't assist with questions that crypto addresses. Please remove the address and ask again.")
        elif contains_bip39_phrase(question):
            await message.reply("It looks like you've included a recovery phrase in your message. Please never share your recovery phrase. It is the master key to your wallet and should be kept private.")
        else:
            await answer_question(message, question)
    await bot.process_commands(message)

@bot.command()
@commands.cooldown(1, 20, commands.BucketType.user)
async def ask(ctx, *, question):
    if re.search(ETHEREUM_ADDRESS_PATTERN, question, re.IGNORECASE) or re.search(BITCOIN_ADDRESS_PATTERN, question, re.IGNORECASE):
        await ctx.reply("I'm sorry, but I can't assist with questions that include Ethereum or Bitcoin addresses. Please remove the address and ask again.")
    else:
        await answer_question(ctx, question)

@ask.error
async def ask_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = 'Not too fast! Please ask me again in {:.0f}s.'.format(error.retry_after)
        await ctx.reply(msg)
    else:
        raise error

bot.run(bot_token)
