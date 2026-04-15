import os
import discord
from discord.ext import commands

from .ui.voice_picker import VoicePickerView
from .utils.settings import get_user_settings, update_user_setting, reset_user_settings, DEFAULT_SETTINGS
from .utils.tts import get_edge_voices
from .utils.queue_manager import get_queue


def register_commands(bot: commands.Bot, active_channels: set):

    @bot.command()
    async def help(ctx):
        msg = """
## TTS Commands

    t.tts → Join VC + enable TTS
    t.clear → Stop and clear queue
    t.join → Join VC
    t.leave → Leave VC
    t.start → Enable TTS

### Settings

    t.voice [v] → Set voice / list voices
    t.speed [n] → Set speed (80–300)
    t.pitch [n] → Set pitch (0–99)
    t.type [t] → espeak / edge
    t.types → List TTS engines
    t.nickname → Set nickname

### Other

    t.reset → Reset settings
        """
        await ctx.send(msg)

    @bot.command()
    async def tts(ctx):
        if not ctx.author.voice:
            await ctx.send("Join a VC first.")
            return
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        active_channels.add(ctx.channel.id)
        await ctx.send("TTS enabled.")

    @bot.command()
    async def clear(ctx):
        vc = ctx.voice_client
        if not vc:
            return
        if vc.is_playing():
            vc.stop()
        queue = get_queue(ctx.guild.id)
        while not queue.empty():
            try:
                _, file = queue.get_nowait()
                os.remove(file)
            except Exception:
                pass
        await ctx.send("Queue cleared.")

    @bot.command()
    async def types(ctx):
        await ctx.send("```\nespeak\nedge\n```")

    @bot.command()
    async def voice(ctx, *, value: str = None):
        if value is None:
            voices = await get_edge_voices()

            seen = set()
            locales = []
            for v in voices:
                loc = v["Locale"]
                if loc not in seen:
                    seen.add(loc)
                    locales.append(loc)
            locales.sort()

            view = VoicePickerView(voices, ctx.guild.id, ctx.author.id)
            await ctx.send("Pick your voice:", view=view)
            return

        # Direct set by name
        voices = await get_edge_voices()
        match = next((v for v in voices if v["ShortName"].lower() == value.lower()), None)

        if not match:
            matches = [v for v in voices if value.lower() in v["ShortName"].lower()]
            if len(matches) == 1:
                match = matches[0]
            elif len(matches) > 1:
                names = "\n".join(v["ShortName"] for v in matches[:10])
                await ctx.send(f"Multiple matches:\n```\n{names}\n```")
                return
            else:
                await ctx.send("Voice not found.")
                return

        update_user_setting(ctx.guild.id, ctx.author.id, "voice", match["ShortName"])
        await ctx.send(f"Voice set to {match['ShortName']}")

    @bot.command()
    async def speed(ctx, value: int):
        clamped = max(80, min(300, value))
        update_user_setting(ctx.guild.id, ctx.author.id, "speed", clamped)
        await ctx.send(f"Speed set to {clamped}")

    @bot.command()
    async def pitch(ctx, value: int):
        clamped = max(0, min(99, value))
        update_user_setting(ctx.guild.id, ctx.author.id, "pitch", clamped)
        await ctx.send(f"Pitch set to {clamped}")

    @bot.command(name="type")
    async def tts_type(ctx, value: str):
        if value not in ["espeak", "edge"]:
            await ctx.send("Valid types: espeak, edge")
            return
        update_user_setting(ctx.guild.id, ctx.author.id, "type", value)
        await ctx.send(f"TTS engine set to {value}")

    @bot.command()
    async def nickname(ctx, *, name: str = None):
        update_user_setting(ctx.guild.id, ctx.author.id, "nickname", name)
        await ctx.send(f"Nickname set to {name}")

    @bot.command()
    async def join(ctx):
        if not ctx.author.voice:
            await ctx.send("Join a VC first.")
            return
        await ctx.author.voice.channel.connect()

    @bot.command()
    async def leave(ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            active_channels.discard(ctx.channel.id)

    @bot.command()
    async def start(ctx):
        if not ctx.voice_client:
            await ctx.send("Use t.join first.")
            return
        active_channels.add(ctx.channel.id)
        await ctx.send("TTS enabled.")

    @bot.command()
    async def reset(ctx):
        reset_user_settings(ctx.guild.id, ctx.author.id)
        await ctx.send("Settings reset.")