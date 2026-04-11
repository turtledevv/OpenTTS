"""
migrate_json_to_db.py

Converts tts_settings.json to the new SQLite database.

Since the old format had no guild information, you must provide a fallback
guild ID to assign all existing settings to. You can find your server's ID
by enabling Developer Mode in Discord and right-clicking the server.

Usage:
    python migrate_json_to_db.py --guild <GUILD_ID> [--json tts_settings.json] [--db data/settings.db]
"""

import argparse
import json
import os
import sqlite3


DEFAULT_SETTINGS = {
    "speed": 160,
    "pitch": 40,
    "voice": "en-US-AriaNeural",
    "type": "edge",
    "nickname": None,
}


def migrate(json_path: str, db_path: str, fallback_guild_id: str):
    if not os.path.exists(json_path):
        print(f"ERROR: JSON file not found: {json_path}")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    if not data:
        print("JSON file is empty, nothing to migrate.")
        return

    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            guild_id  TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            speed     INTEGER NOT NULL DEFAULT 160,
            pitch     INTEGER NOT NULL DEFAULT 40,
            voice     TEXT    NOT NULL DEFAULT 'en-US-AriaNeural',
            type      TEXT    NOT NULL DEFAULT 'edge',
            nickname  TEXT,
            PRIMARY KEY (guild_id, user_id)
        )
    """)

    migrated = 0
    skipped = 0

    for user_id, settings in data.items():
        # Merge with defaults so missing keys don't cause issues
        merged = {**DEFAULT_SETTINGS, **settings}

        # Clamp values to valid ranges
        speed   = max(80,  min(300, int(merged.get("speed",  DEFAULT_SETTINGS["speed"]))))
        pitch   = max(0,   min(99,  int(merged.get("pitch",  DEFAULT_SETTINGS["pitch"]))))
        voice   = merged.get("voice",    DEFAULT_SETTINGS["voice"])   or DEFAULT_SETTINGS["voice"]
        ttype   = merged.get("type",     DEFAULT_SETTINGS["type"])    or DEFAULT_SETTINGS["type"]
        nickname = merged.get("nickname", None)

        if ttype not in ("espeak", "edge"):
            print(f"  WARN: user {user_id} has unknown type '{ttype}', defaulting to 'edge'")
            ttype = "edge"

        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_settings
                    (guild_id, user_id, speed, pitch, voice, type, nickname)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (fallback_guild_id, user_id, speed, pitch, voice, ttype, nickname)
            )
            migrated += 1
        except Exception as e:
            print(f"  ERROR inserting user {user_id}: {e}")
            skipped += 1

    conn.commit()
    conn.close()

    print(f"Done. Migrated {migrated} user(s) to guild {fallback_guild_id}, skipped {skipped}.")
    print(f"Database: {db_path}")
    print()
    print("NOTE: All settings have been assigned to a single guild. If your bot")
    print("was used across multiple servers, users will need to reconfigure their")
    print("settings in each other server — there is no way to recover that info")
    print("from a global JSON file.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate tts_settings.json to settings.db")
    parser.add_argument(
        "--guild", required=True,
        help="Discord guild (server) ID to assign all existing settings to"
    )
    parser.add_argument(
        "--json", default=os.path.join("data", "tts_settings.json"),
        help="Path to the source JSON file (default: data/tts_settings.json)"
    )
    parser.add_argument(
        "--db", default=os.path.join("data", "settings.db"),
        help="Path to the output SQLite database (default: data/settings.db)"
    )
    args = parser.parse_args()

    migrate(
        json_path=args.json,
        db_path=args.db,
        fallback_guild_id=str(args.guild),
    )