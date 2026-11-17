"""SQLite schema for movies and their curated-list memberships."""
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent / "cinescope.db"


def initialise_database(db_path=DEFAULT_DB):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript("""
        CREATE TABLE IF NOT EXISTS movies (
            movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            letterboxd_uri TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS movie_lists (
            list_id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS movie_list_membership (
            movie_id INTEGER NOT NULL REFERENCES movies(movie_id),
            list_id INTEGER NOT NULL REFERENCES movie_lists(list_id),
            rank INTEGER NOT NULL CHECK(rank > 0),
            PRIMARY KEY(movie_id, list_id)
        );
        """)
