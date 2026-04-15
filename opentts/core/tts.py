import subprocess
import edge_tts
from ..infra.misc import map_speed_to_rate, map_pitch_to_edge


async def get_edge_voices():
    return await edge_tts.list_voices()


def espeak_tts(text: str, settings: dict, filename: str):
    voice_cfg = settings["voice"]
    # espeak expects a locale-style tag, e.g. "en-us"
    voice = f"{voice_cfg['lang']}-{voice_cfg['region'].lower()}" if voice_cfg.get("lang") else "en-us"
    speed = voice_cfg["settings"]["speed"]
    pitch = voice_cfg["settings"]["pitch"]
    try:
        subprocess.run([
            "espeak-ng",
            "-v", voice,
            "-s", str(speed),
            "-p", str(pitch),
            "-w", filename,
            text
        ], check=True)
    except Exception:
        subprocess.run([
            "espeak-ng",
            "-v", "en-us",
            "-w", filename,
            text
        ])


async def edge_tts_gen(text: str, settings: dict, filename: str):
    voice_cfg = settings["voice"]
    speed = voice_cfg["settings"]["speed"]
    pitch = voice_cfg["settings"]["pitch"]
    # Reconstruct full ShortName, e.g. "en-US-AriaNeural"
    full_voice = f"{voice_cfg['lang']}-{voice_cfg['region']}-{voice_cfg['name']}"

    rate = map_speed_to_rate(speed)
    pitch_str = map_pitch_to_edge(pitch)
    try:
        communicate = edge_tts.Communicate(text, full_voice, rate=rate, pitch=pitch_str)
        await communicate.save(filename)
    except Exception:
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        await communicate.save(filename)


async def generate_tts(text: str, settings: dict, filename: str):
    if settings["engine"] == "edge":
        await edge_tts_gen(text, settings, filename)
    else:
        espeak_tts(text, settings, filename)