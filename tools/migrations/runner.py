import os
import sqlite3
import importlib.util
from pathlib import Path

DB_PATH = os.path.join(os.getenv("RUNTIME_DIR", "."), "data", "settings.db")

BASE_DIR = Path(__file__).resolve().parent

MIGRATIONS = [
    ("001_init", BASE_DIR / "001_init.py"),
    ("002_json_import", BASE_DIR / "002_json-import.py"),
    ("003_voice_refactor", BASE_DIR / "003_voice-refactor.py"),
]


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name TEXT PRIMARY KEY
        )
    """)


def get_applied(conn):
    rows = conn.execute("SELECT name FROM schema_migrations").fetchall()
    return {r["name"] for r in rows}


def load_module(path: str):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_migrations(*, json_path=None, fallback_guild_id=None):
    conn = get_conn()
    ensure_table(conn)

    applied = get_applied(conn)

    for name, file in MIGRATIONS:
        if name in applied:
            continue

        if args.only and name != args.only:
            continue

        print(f"[migrate] running {name}")

        mod = load_module(file)

        # build context once, pass only if needed
        context = {}

        if name == "002_json_import":
            context["json_path"] = json_path
            context["fallback_guild_id"] = fallback_guild_id

            if not fallback_guild_id:
                raise ValueError("002_json_import requires fallback_guild_id")

        mod.up(conn, **context)

        conn.execute(
            "INSERT INTO schema_migrations (name) VALUES (?)",
            (name,)
        )
        conn.commit()

    conn.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=None)
    parser.add_argument("--guild", default=None)
    parser.add_argument("--only", default=None)

    args = parser.parse_args()

    run_migrations(
        json_path=args.json,
        fallback_guild_id=args.guild
    )