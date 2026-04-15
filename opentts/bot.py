import time

start_time = time.time()

import discord
from discord.ext import commands

from .utils.settings import get_user_settings, init_db
from .utils.tts import generate_tts
from .utils.queue_manager import get_queue, play_next
from .utils.misc import clean_text
from .commands import register_commands

BLOCK_PREFIXES = ("-", "t.", "!", "?")
MAX_LENGTH = 250

BOT_LOADED = False # Sometimes, on_ready is called multiple times, instead of just once on initial startup. (at least, from personal experience.) This var fixes this.

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

init_db()

bot = commands.Bot(command_prefix="t.", intents=intents, help_command=None)

active_channels: set[int] = set()
last_message_cache: dict[int, dict] = {}  # channel_id -> {author_id, content}

register_commands(bot, active_channels)

@bot.event
async def on_ready():
    global BOT_LOADED
    if BOT_LOADED:
        print('Bot is already loaded, skipping on_ready event!')
        return
    BOT_LOADED = True

    print(f'Logged in as {bot.user}')

    print(f'Add the bot to your server: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot')

    await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(name="Type 't.help' for help!", type=discord.ActivityType.playing))

    elapsed_ms = (time.time() - start_time) * 1000
    print(f"Done! (took {elapsed_ms:.0f}ms)")

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

    name = settings.get("nickname") or message.author.display_name
    text = clean if (cache and cache["author_id"] == message.author.id) else f"{name} says {clean}"

    last_message_cache[message.channel.id] = {
        "author_id": message.author.id,
        "content": clean
    }

    ext = "mp3" if settings["type"] == "edge" else "wav"
    filename = f"/tmp/tts_{message.id}.{ext}"

    await generate_tts(text, settings, filename)

    queue = get_queue(message.guild.id)
    await queue.put((vc, filename))

    if not vc.is_playing():
        await play_next(message.guild.id)