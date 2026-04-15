import json
import os

DEFAULT_SETTINGS = {
    "speed": 160,
    "pitch": 40,
    "voice": "en-US-AriaNeural",
    "type": "edge",
    "nickname": None,
}


def up(conn, json_path=None, fallback_guild_id=None):
    if not json_path or not os.path.exists(json_path):
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    if not data:
        return

    cur = conn.cursor()

    for user_id, settings in data.items():
        merged = {**DEFAULT_SETTINGS, **settings}

        speed = max(80, min(300, int(merged["speed"])))
        pitch = max(0, min(99, int(merged["pitch"])))

        voice = merged["voice"] or DEFAULT_SETTINGS["voice"]
        ttype = merged["type"] or DEFAULT_SETTINGS["type"]
        nickname = merged["nickname"]

        if ttype not in ("edge", "espeak"):
            ttype = "edge"

        cur.execute("""
            INSERT OR REPLACE INTO user_settings
            (guild_id, user_id, speed, pitch, voice, type, nickname)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(fallback_guild_id),
            str(user_id),
            speed,
            pitch,
            voice,
            ttype,
            nickname
        ))