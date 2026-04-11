import re
import discord
import json

with open("./assets/repl.json", "r", encoding="utf-8") as f:
    acronyms = json.load(f)

ACRONYM_REGEX = re.compile(r'\b(' + '|'.join(map(re.escape, acronyms.keys())) + r')\b', re.IGNORECASE)

URL_REGEX = re.compile(r"https?://\S+")
TENOR_REGEX = re.compile(r"https?://(www\.)?tenor\.com/\S+")

def expand_acronyms(text: str) -> str:
    def replacer(match):
        key = match.group(0).lower()
        return acronyms.get(key, key)

    return ACRONYM_REGEX.sub(replacer, text)

def replace_user(match: re.Match, message: discord.Message):
    user_id = int(match.group(1))
    user = message.guild.get_member(user_id) if message.guild else None

    if user:
        return f"@{user.display_name}"
    return "@user"

def replace_channel(match: re.Match, message: discord.Message):
    channel_id = int(match.group(1))
    channel = message.guild.get_channel(channel_id) if message.guild else None

    if channel:
        return f"channel {channel.name}"
    return "unknown channel"


def clean_text(message: discord.Message) -> str:
    content = message.content
    content = TENOR_REGEX.sub("a gif", content)
    content = URL_REGEX.sub("a link", content)
    content = re.sub(
        r"<@!?(\d+)>",
        lambda m: replace_user(m, message),
        content
    )

    content = re.sub(
        r"<#(\d+)>",
        lambda m: replace_channel(m, message),
        content
    )
    content = re.sub(r"<a?:\w+:(\d+)>", "an emoji", content)
    content = expand_acronyms(content)
    return content.strip()


def map_speed_to_rate(speed: int) -> str:
    percent = int((speed - 160) / 160 * 100)
    percent = max(-50, min(100, percent))
    return f"{percent:+d}%"


def map_pitch_to_edge(pitch: int) -> str:
    hz = int((pitch - 50))
    hz = max(-50, min(50, hz))
    return f"{hz:+d}Hz"