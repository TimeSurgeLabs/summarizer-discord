import os
import time

import nextcord
from nextcord import SlashOption, Interaction
from nextcord.ext import commands
from nextcord import Message
from dotenv import load_dotenv
from loguru import logger

from utils import get_youtube_video_id
from db import DB
from ai import chat_gpt_request

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
        transcript = resp['transcript']
        title = resp['title']
        summary = None
        try:
            logger.info('Checking if summary already exists...')
            summary = db.get_summary(videoId)
        except:
            pass
        if summary:
            logger.info('Summary already exists. Posting...')
            # edit the loading message
            await m.edit(content=f'Summary for "{title}"\n\n{summary.summary}')
            return
        logger.info('Generating summary...')
        start = time.time()
        summary = await chat_gpt_request(transcript)
        end = time.time()
        logger.info(f'Took {round(end-start, 2)}s to generate summary.')
        await m.edit(content=f'Summary for "{title}"\n\n{summary}')
        logger.info(f'Posting summary to db...')
        db.post_summary(videoId, summary)
    except Exception as e:
        logger.error(e)
        await m.edit(content='Error generating summary. If this is a valid video, please try again later.')

@bot.slash_command(name="yt", description="Get a summary of a YouTube video.", guild_ids=[int(TESTING_GUILD_ID)])
async def summary_command(
    interaction: Interaction,
    video: str = SlashOption(description="The URL of a YouTube video.", required=True)
):
    videoId = get_youtube_video_id(video)
    if not videoId:
        await interaction.send('Invalid YouTube video URL.')
        return
    # defer the message
    await interaction.response.defer()
    logger.info(f'Getting transcript for {videoId}...')
    try:
        resp = db.get_transcript(videoId)
        transcript = resp['transcript']
        title = resp['title']
        summary = None
        try:
            logger.info('Checking if summary already exists...')
            summary = db.get_summary(videoId)
        except:
            pass
        if summary:
            logger.info('Summary already exists. Posting...')
            await interaction.send(f'Summary for "{title}"\n\n{summary.summary}')
            return
        logger.info('Generating summary...')
        start = time.time()
        summary = await chat_gpt_request(transcript)
        end = time.time()
        logger.info(f'Took {round(end-start, 2)}s to generate summary.')
        await interaction.send(f'Summary for "{title}"\n\n{summary}')
        logger.info(f'Posting summary to db...')
        db.post_summary(videoId, summary)
    except Exception as e:
        logger.error(e)
        await interaction.send('Error generating summary. If this is a valid video, please try again later.')


bot.run(os.getenv('DISCORD_BOT_TOKEN'))
