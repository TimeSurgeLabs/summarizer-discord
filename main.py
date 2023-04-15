import os

import nextcord
from nextcord.ext import commands
from nextcord import Message
from dotenv import load_dotenv
from loguru import logger

from utils import get_youtube_video_id
from db import DB

load_dotenv()

TESTING_GUILD_ID = os.getenv('TESTING_GUILD_ID')

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(intents=intents)

db = DB()
db.login(os.getenv('DB_USERNAME'), os.getenv('DB_PASSWORD'))


@bot.event
async def on_ready():
    logger.info(f'We have logged in as {bot.user}')


@bot.event
async def on_message(message: Message):
    if not ('youtube.com' in message.content or 'youtu.be' in message.content):
        return
    if message.author.bot or message.author.id == bot.user.id:
        return
    videoId = get_youtube_video_id(message.content)
    if not videoId:
        return
    logger.info(f'Getting transcript for {videoId}...')
    m = await message.channel.send('Generating summary...')
    try:
        # send a loading message first
        resp = db.get_transcript(videoId)
        title = resp.get('title')
        error = resp.get('error')
        if error:
            raise Exception(error)
        resp = db.get_summary(videoId, str(message.channel.id))
        error = resp.get('error')
        summary = resp.get('summary')
        if error:
            raise Exception(error)
        if summary:
            logger.info('Got Summary. Posting...')
            # edit the loading message
            await m.edit(content=f'Summary for "{title}"\n\n{summary}')
            return
        else:
            raise Exception('Summary does not exist.')
    except Exception as e:
        logger.error(e)
        await m.edit(content='Error generating summary. If this is a valid video, please try again later.')


bot.run(os.getenv('DISCORD_BOT_TOKEN'))
