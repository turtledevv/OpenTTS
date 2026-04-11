import subprocess
import edge_tts
from .misc import map_speed_to_rate, map_pitch_to_edge


async def get_edge_voices():
    return await edge_tts.list_voices()


def espeak_tts(text: str, settings: dict, filename: str):
    voice = settings["voice"] or "en-us"
    try:
        subprocess.run([
            "espeak-ng",
            "-v", voice,
            "-s", str(settings["speed"]),
            "-p", str(settings["pitch"]),
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
    rate = map_speed_to_rate(settings["speed"])
    pitch = map_pitch_to_edge(settings["pitch"])
    voice = settings["voice"] or "en-US-AriaNeural"
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(filename)
    except Exception:
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        await communicate.save(filename)


async def generate_tts(text: str, settings: dict, filename: str):
    if settings["type"] == "edge":
        await edge_tts_gen(text, settings, filename)
    else:
        espeak_tts(text, settings, filename)