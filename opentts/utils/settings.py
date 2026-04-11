import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.getenv("RUNTIME_DIR", "."), "data", "settings.db")

DEFAULT_SETTINGS = {
    "speed": 160,
    "pitch": 40,
    "voice": "en-US-AriaNeural",
    "type": "edge",
    "nickname": None,
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


def init_db():
    with _db() as conn:
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


def get_user_settings(guild_id: int, user_id: int) -> dict:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM user_settings WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        ).fetchone()

        if row is None:
            conn.execute(
                """
                INSERT INTO user_settings (guild_id, user_id, speed, pitch, voice, type, nickname)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(guild_id), str(user_id),
                    DEFAULT_SETTINGS["speed"],
                    DEFAULT_SETTINGS["pitch"],
                    DEFAULT_SETTINGS["voice"],
                    DEFAULT_SETTINGS["type"],
                    DEFAULT_SETTINGS["nickname"],
                )
            )
            return DEFAULT_SETTINGS.copy()

        return dict(row)


def update_user_setting(guild_id: int, user_id: int, key: str, value):
    allowed = {"speed", "pitch", "voice", "type", "nickname"}
    if key not in allowed:
        raise ValueError(f"Unknown setting: {key}")

    with _db() as conn:
        # Ensure row exists first
        conn.execute(
            """
            INSERT OR IGNORE INTO user_settings (guild_id, user_id, speed, pitch, voice, type, nickname)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(guild_id), str(user_id),
                DEFAULT_SETTINGS["speed"],
                DEFAULT_SETTINGS["pitch"],
                DEFAULT_SETTINGS["voice"],
                DEFAULT_SETTINGS["type"],
                DEFAULT_SETTINGS["nickname"],
            )
        )
        conn.execute(
            f"UPDATE user_settings SET {key} = ? WHERE guild_id = ? AND user_id = ?",
            (value, str(guild_id), str(user_id))
        )


def reset_user_settings(guild_id: int, user_id: int):
    with _db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO user_settings (guild_id, user_id, speed, pitch, voice, type, nickname)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(guild_id), str(user_id),
                DEFAULT_SETTINGS["speed"],
                DEFAULT_SETTINGS["pitch"],
                DEFAULT_SETTINGS["voice"],
                DEFAULT_SETTINGS["type"],
                DEFAULT_SETTINGS["nickname"],
            )
        )