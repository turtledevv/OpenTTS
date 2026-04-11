import asyncio
import os
import discord

tts_queue: dict[int, asyncio.Queue] = {}


def get_queue(guild_id: int) -> asyncio.Queue:
    if guild_id not in tts_queue:
        tts_queue[guild_id] = asyncio.Queue()
    return tts_queue[guild_id]


async def play_next(guild_id: int):
    queue = get_queue(guild_id)

    if queue.empty():
        return

    vc, file = await queue.get()

    if not vc or not vc.is_connected():
        return

    vc.play(discord.FFmpegPCMAudio(file))

    while vc.is_playing():
        await asyncio.sleep(0.3)

    try:
        os.remove(file)
    except Exception:
        pass

    await play_next(guild_id)