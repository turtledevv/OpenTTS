import time
start_time = time.time()

import discord
from discord.ext import commands
import logging
import signal
import asyncio

from .core.settings import get_user_settings, init_db
from .core.tts import generate_tts
from .core.queue import get_queue, play_next

from .infra.misc import clean_text
from .infra.logger import setup_logger

from .commands import register_commands

BLOCK_PREFIXES = ("-", "t.", "!", "?")
MAX_LENGTH = 250

logger = setup_logger("bot")

# Configure discord.py to use the same logging system
discord_logger = setup_logger("discord")
logging.getLogger("discord").parent = None
logging.getLogger("discord").setLevel(logging.INFO)

BOT_LOADED = False # Sometimes, on_ready is called multiple times, instead of just once on initial startup. (at least, from personal experience.) This var fixes this.

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

init_db()

bot = commands.Bot(command_prefix="t.", intents=intents, help_command=None)

active_channels: set[int] = set()
last_message_cache: dict[int, dict] = {}  # channel_id -> {author_id, content}

register_commands(bot, active_channels)

async def notify_and_shutdown():
    logger.info("Shutting down, notifying voice channels...")
    message = "**The bot is shutting down temporarily, and will leave the VC. Sorry for the inconvinence. The bot will most likely be up soon again.**"
    sent = 0
    tasks = []
    for vc in bot.voice_clients:
        channel = vc.channel
        if hasattr(channel, 'send'):
            sent += 1
            tasks.append(channel.send(message))
        else:
            # fallback to a matching non-vc channel
            text_channel = discord.utils.find(
                lambda c: isinstance(c, discord.TextChannel) and c.name == channel.name,
                channel.guild.channels
            )
            if not text_channel:
                text_channel = channel.guild.system_channel or next(
                    (c for c in channel.guild.text_channels
                     if c.permissions_for(channel.guild.me).send_messages),
                    None
                )
            if text_channel:
                tasks.append(text_channel.send(message))
                sent += 1
        tasks.append(vc.disconnect())
    logger.info(f"Notified {sent} channel(s) successfully. Shutting down!")

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    await bot.close()

def handle_signal():
    asyncio.create_task(notify_and_shutdown())

@bot.event
async def on_ready():
    global BOT_LOADED
    if BOT_LOADED:
        logger.info('Bot is already loaded, skipping on_ready event!')
        return
    BOT_LOADED = True

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    logger.info(f'Logged in as {bot.user}')

    logger.info(f'Add the bot to your server: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot')

    await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(name="Type 't.help' for help!", type=discord.ActivityType.playing))

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info(f"Done! (took {elapsed_ms:.0f}ms)")

@bot.event
async def on_voice_state_update(member, before, after):
    # ignore if no guild context
    if not member.guild:
        return

    vc = member.guild.voice_client
    if not vc or not vc.is_connected():
        return

    channel = vc.channel
    if not channel:
        return

    # if someone joins/leaves, re-evaluate the channel
    humans = [m for m in channel.members if not m.bot]

    if len(humans) == 0:
        logger.info(f"VC {channel.name} is empty. Leaving like it was never wanted.")
        await vc.disconnect()

        queue = get_queue(member.guild.id)
        while not queue.empty():
            try:
                queue.get_nowait()
                queue.task_done()
            except Exception:
                break

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return
    if message.channel.id not in active_channels:
        return

    vc = message.guild.voice_client
    if not vc or not vc.is_connected():
        return

    content = message.content

    if len(content) > MAX_LENGTH:
        try:
            await message.add_reaction("⚠️")
        except Exception:
            pass
        return

    for p in BLOCK_PREFIXES:
        if content.startswith(p) and len(content) > len(p):
            return

    settings = get_user_settings(message.guild.id, message.author.id)
    clean = clean_text(message)
    cache = last_message_cache.get(message.channel.id)

    if cache and cache["author_id"] == message.author.id and cache["content"] == clean:
        return

    name = settings.get("nick") or message.author.display_name
    text = clean if (cache and cache["author_id"] == message.author.id) else f"{name} says {clean}"

    last_message_cache[message.channel.id] = {
        "author_id": message.author.id,
        "content": clean
    }

    ext = "mp3" if settings["engine"] == "edge" else "wav"
    filename = f"/tmp/tts_{message.id}.{ext}"

    await generate_tts(text, settings, filename)

    queue = get_queue(message.guild.id)
    await queue.put((vc, filename))

    if not vc.is_playing():
        await play_next(message.guild.id)