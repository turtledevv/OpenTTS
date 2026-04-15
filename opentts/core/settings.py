import sqlite3
import os
import json
import copy
from contextlib import contextmanager

DB_PATH = os.path.join(os.getenv("RUNTIME_DIR", "."), "data", "settings.db")

DEFAULT_SETTINGS = {
    "voice": {
        "lang": "en",
        "region": "US",
        "name": "AriaNeural",
        "settings": {
            "speed": 160,
            "pitch": 40,
        },
    },
    "engine": "edge",
    "nick": None,
    "custom_repl": [],
}


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _row_to_settings(row) -> dict:
    """Convert a flat DB row into the nested settings dict."""
    return {
        "voice": {
            "lang": row["voice_lang"],
            "region": row["voice_region"],
            "name": row["voice_name"],
            "settings": {
                "speed": row["speed"],
                "pitch": row["pitch"],
            },
        },
        "engine": row["engine"],
        "nick": row["nick"],
        "custom_repl": json.loads(row["custom_repl"]) if row["custom_repl"] else [],
    }


def _default_row_values(guild_id: int, user_id: int) -> tuple:
    d = DEFAULT_SETTINGS
    return (
        str(guild_id),
        str(user_id),
        d["voice"]["lang"],
        d["voice"]["region"],
        d["voice"]["name"],
        d["voice"]["settings"]["speed"],
        d["voice"]["settings"]["pitch"],
        d["engine"],
        d["nick"],
        json.dumps(d["custom_repl"]),
    )


def init_db():
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                guild_id     TEXT    NOT NULL,
                user_id      TEXT    NOT NULL,
                voice_lang   TEXT    NOT NULL DEFAULT 'en',
                voice_region TEXT    NOT NULL DEFAULT 'US',
                voice_name   TEXT    NOT NULL DEFAULT 'AriaNeural',
                speed        INTEGER NOT NULL DEFAULT 160,
                pitch        INTEGER NOT NULL DEFAULT 40,
                engine       TEXT    NOT NULL DEFAULT 'edge',
                nick         TEXT,
                custom_repl  TEXT    NOT NULL DEFAULT '[]',
                PRIMARY KEY (guild_id, user_id)
            )
        """)


def get_user_settings(guild_id: int, user_id: int) -> dict:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM user_settings WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        ).fetchone()

        if row is None:
            conn.execute(
                """
                INSERT INTO user_settings
                    (guild_id, user_id, voice_lang, voice_region, voice_name, speed, pitch, engine, nick, custom_repl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _default_row_values(guild_id, user_id)
            )
            return copy.deepcopy(DEFAULT_SETTINGS)

        return _row_to_settings(row)


def update_user_setting(guild_id: int, user_id: int, key: str, value):
    """
    Key is a dotted path into the nested settings structure.
    Valid keys:
        voice.lang, voice.region, voice.name
        voice.settings.speed, voice.settings.pitch
        engine, nick, custom_repl
    """
    _COLUMN_MAP = {
        "voice.lang":           "voice_lang",
        "voice.region":         "voice_region",
        "voice.name":           "voice_name",
        "voice.settings.speed": "speed",
        "voice.settings.pitch": "pitch",
        "engine":               "engine",
        "nick":                 "nick",
        "custom_repl":          "custom_repl",
    }

    col = _COLUMN_MAP.get(key)
    if col is None:
        raise ValueError(f"Unknown setting key: {key!r}. Valid keys: {list(_COLUMN_MAP)}")

    if col == "custom_repl":
        value = json.dumps(value)

    with _db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO user_settings
                (guild_id, user_id, voice_lang, voice_region, voice_name, speed, pitch, engine, nick, custom_repl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _default_row_values(guild_id, user_id)
        )
        conn.execute(
            f"UPDATE user_settings SET {col} = ? WHERE guild_id = ? AND user_id = ?",
            (value, str(guild_id), str(user_id))
        )


def reset_user_settings(guild_id: int, user_id: int):
    with _db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO user_settings
                (guild_id, user_id, voice_lang, voice_region, voice_name, speed, pitch, engine, nick, custom_repl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _default_row_values(guild_id, user_id)
        )