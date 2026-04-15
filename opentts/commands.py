import os
import discord
from discord.ext import commands

from .ui.voice_picker import VoicePickerView
from .core.settings import get_user_settings, update_user_setting, reset_user_settings, DEFAULT_SETTINGS
from .core.tts import get_edge_voices
from .core.queue import get_queue


def register_commands(bot: commands.Bot, active_channels: set):

    @bot.command()
    async def help(ctx):
        embed = discord.Embed()
        embed.set_author(
            name="-- OpenTTS • Help --",
        )
        embed.set_thumbnail(url="https://raw.githubusercontent.com/turtledevv/OpenTTS/refs/heads/main/assets/profile.png")
        embed.add_field(
            name="🎙️ Basic Commands",
            value="**`t.tts`** **|** Join the VC and enable TTS!\n**`t.clear`** **|** Stop and clear message queue.\n**`t.reset`** **|** Reset your user settings.",
            inline=False,
        )
        embed.add_field(
            name="🔧 Voice Settings",
            value="**`t.voice`** **|** Set your TTS voice\n**`t.speed`** **|** Change the voice's speed *(80-300)*\n**`t.pitch`** **|** Change the voice's pitch *(0-99)*\n**`t.engine`** **|** Set the TTS engine *(espeak-ng/edge)*\n**`t.engines`** **|** List TTS engines\n-# *:warning: Speed and pitch may not be consistent between TTS engines!*",
            inline=False,
        )
        embed.add_field(
            name="For support, join our Discord server!",
            value="-# https://discord.gg/vaTHzrjFgZ\n\n",
            inline=False,\
        )
        await ctx.reply(embed=embed)

    @bot.command()
    async def tts(ctx):
        if not ctx.author.voice:
            await ctx.reply("Join a VC first.")
            return
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        active_channels.add(ctx.channel.id)
        await ctx.reply("TTS enabled.")

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
        await ctx.reply("Queue cleared.")

    @bot.command()
    async def engines(ctx):
        await ctx.reply("```\nespeak-ng\nedge\n```")

    # Keep old alias so nobody is surprised
    @bot.command(name="types")
    async def types(ctx):
        await ctx.invoke(engines)

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
            await ctx.reply("Pick your voice:", view=view)
            return

        # Direct set by ShortName, e.g. "en-US-AriaNeural"
        voices = await get_edge_voices()
        match = next((v for v in voices if v["ShortName"].lower() == value.lower()), None)

        if not match:
            matches = [v for v in voices if value.lower() in v["ShortName"].lower()]
            if len(matches) == 1:
                match = matches[0]
            elif len(matches) > 1:
                names = "\n".join(v["ShortName"] for v in matches[:10])
                await ctx.reply(f"Multiple matches:\n```\n{names}\n```")
                return
            else:
                await ctx.reply("Voice not found.")
                return

        # Split ShortName into parts, e.g. "en-US-AriaNeural" -> lang=en, region=US, name=AriaNeural
        parts = match["ShortName"].split("-", 2)
        if len(parts) == 3:
            update_user_setting(ctx.guild.id, ctx.author.id, "voice.lang",   parts[0])
            update_user_setting(ctx.guild.id, ctx.author.id, "voice.region", parts[1])
            update_user_setting(ctx.guild.id, ctx.author.id, "voice.name",   parts[2])
        await ctx.reply(f"Voice set to {match['ShortName']}")

    @bot.command()
    async def speed(ctx, value: int):
        clamped = max(80, min(300, value))
        update_user_setting(ctx.guild.id, ctx.author.id, "voice.settings.speed", clamped)
        await ctx.reply(f"Speed set to {clamped}")

    @bot.command()
    async def pitch(ctx, value: int):
        clamped = max(0, min(99, value))
        update_user_setting(ctx.guild.id, ctx.author.id, "voice.settings.pitch", clamped)
        await ctx.reply(f"Pitch set to {clamped}")

    @bot.command(name="engine")
    async def tts_engine(ctx, value: str):
        if value not in ("espeak-ng", "edge"):
            await ctx.reply("Valid engines: `espeak-ng`, `edge`")
            return
        update_user_setting(ctx.guild.id, ctx.author.id, "engine", value)
        await ctx.reply(f"TTS engine set to {value}")

    # Old alias
    @bot.command(name="type")
    async def tts_type(ctx, value: str):
        # Accept old names and map them
        _alias = {"espeak": "espeak-ng", "edge": "edge"}
        mapped = _alias.get(value)
        if mapped is None:
            await ctx.reply("Valid engines: `espeak-ng`, `edge`")
            return
        await ctx.invoke(tts_engine, value=mapped)

    @bot.command()
    async def nick(ctx, *, name: str = None):
        update_user_setting(ctx.guild.id, ctx.author.id, "nick", name)
        await ctx.reply(f"Nickname set to {name}")

    # Keep old alias
    @bot.command()
    async def nickname(ctx, *, name: str = None):
        await ctx.invoke(nick, name=name)

    @bot.command()
    async def join(ctx):
        if not ctx.author.voice:
            await ctx.reply("Join a VC first.")
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
            await ctx.reply("Use t.join first.")
            return
        active_channels.add(ctx.channel.id)
        await ctx.reply("TTS enabled.")

    @bot.command()
    async def reset(ctx):
        reset_user_settings(ctx.guild.id, ctx.author.id)
        await ctx.reply("Settings reset.")