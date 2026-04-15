def up(conn, *_):
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(user_settings)")
    cols = {r[1] for r in cur.fetchall()}

    def add_column(name, coltype, default):
        if name not in cols:
            cur.execute(
                f"ALTER TABLE user_settings ADD COLUMN {name} {coltype} DEFAULT {default}"
            )

    add_column("voice_lang", "TEXT", "'en'")
    add_column("voice_region", "TEXT", "'US'")
    add_column("voice_name", "TEXT", "'AriaNeural'")
    add_column("engine", "TEXT", "'edge'")
    add_column("nick", "TEXT", "NULL")
    add_column("custom_repl", "TEXT", "'[]'")

    conn.commit()

    cur.execute("SELECT guild_id, user_id, voice, type, nickname FROM user_settings")
    rows = cur.fetchall()

    for r in rows:
        voice = r["voice"] or "en-US-AriaNeural"
        parts = voice.split("-")

        if len(parts) >= 3:
            lang = parts[0]
            region = parts[1]
            name = "-".join(parts[2:])
        else:
            lang, region, name = "en", "US", voice

        cur.execute("""
            UPDATE user_settings
            SET voice_lang = ?,
                voice_region = ?,
                voice_name = ?,
                engine = COALESCE(engine, type),
                nick = nickname,
                custom_repl = COALESCE(custom_repl, '[]')
            WHERE guild_id = ? AND user_id = ?
        """, (
            lang,
            region,
            name,
            r["guild_id"],
            r["user_id"]
        ))