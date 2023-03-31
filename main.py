import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

TESTING_GUILD_ID = os.getenv('TESTING_GUILD_ID')

bot = commands.Bot()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    print(f'Message from {message.author}: {message.content}')
    print(message.content)
    print(message)

@bot.slash_command(description="My first slash command", guild_ids=[TESTING_GUILD_ID])
async def hello(interaction: nextcord.Interaction):
    await interaction.send("Hello!")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
