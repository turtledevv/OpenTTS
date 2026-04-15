def up(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            guild_id     TEXT    NOT NULL,
            user_id      TEXT    NOT NULL,

            speed        INTEGER NOT NULL DEFAULT 160,
            pitch        INTEGER NOT NULL DEFAULT 40,

            voice        TEXT    NOT NULL DEFAULT 'en-US-AriaNeural',
            type         TEXT    NOT NULL DEFAULT 'edge',
            nickname     TEXT,

            PRIMARY KEY (guild_id, user_id)
        )
    """)