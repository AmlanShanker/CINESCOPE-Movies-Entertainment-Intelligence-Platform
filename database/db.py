"""SQLite persistence for CineScope's movie catalogue and list memberships."""
import sqlite3
from pathlib import Path

import pandas as pd

DEFAULT_DB = Path(__file__).resolve().parent / "cinescope.db"


def _connect(db_path=DEFAULT_DB):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def initialise_database(db_path=DEFAULT_DB):
    """Create the normalized schema if it does not already exist."""
    with _connect(db_path) as con:
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


def refresh_database(movies, memberships, db_path=DEFAULT_DB):
    """Synchronize SQLite with the validated DataFrames; safe to run repeatedly.

    A movie is stored once by Letterboxd URL. Its rank is stored per list.
    The refresh runs in one transaction so an error cannot leave a partial import.
    """
    initialise_database(db_path)
    movie_columns = {"title", "letterboxd_uri"}
    member_columns = {"list_name", "rank", "title", "letterboxd_uri"}
    if not movie_columns.issubset(movies.columns):
        raise ValueError(f"movies must contain columns: {sorted(movie_columns)}")
    if not member_columns.issubset(memberships.columns):
        raise ValueError(f"memberships must contain columns: {sorted(member_columns)}")

    with _connect(db_path) as con:
        # Upsert master movie rows before memberships are written.
        for row in movies[["title", "letterboxd_uri"]].itertuples(index=False, name=None):
            title, uri = map(str, row)
            con.execute(
                """INSERT INTO movies(title, letterboxd_uri) VALUES (?, ?)
                   ON CONFLICT(letterboxd_uri) DO UPDATE SET title=excluded.title""",
                (title, uri),
            )

        # Memberships are a snapshot of the supplied source lists.
        con.execute("DELETE FROM movie_list_membership")
        con.execute("DELETE FROM movie_lists")
        for list_name in memberships["list_name"].dropna().astype(str).unique():
            con.execute("INSERT INTO movie_lists(list_name) VALUES (?)", (list_name,))

        for row in memberships[
            ["list_name", "rank", "letterboxd_uri"]
        ].itertuples(index=False, name=None):
            list_name, rank, uri = row
            con.execute(
                """INSERT INTO movie_list_membership(movie_id, list_id, rank)
                   SELECT m.movie_id, l.list_id, ?
                   FROM movies AS m CROSS JOIN movie_lists AS l
                   WHERE m.letterboxd_uri = ? AND l.list_name = ?""",
                (int(rank), str(uri), str(list_name)),
            )

        # Remove catalogue rows no longer present in any current source list.
        con.execute("""
            DELETE FROM movies
            WHERE NOT EXISTS (
                SELECT 1 FROM movie_list_membership mm
                WHERE mm.movie_id = movies.movie_id
            )
        """)


def get_movies(db_path=DEFAULT_DB):
    """Return one row per movie."""
    initialise_database(db_path)
    with _connect(db_path) as con:
        return pd.read_sql_query(
            "SELECT movie_id, title, letterboxd_uri FROM movies ORDER BY title",
            con,
        )


def get_memberships(db_path=DEFAULT_DB):
    """Return one row per movie/list pair, including that list's rank."""
    initialise_database(db_path)
    with _connect(db_path) as con:
        return pd.read_sql_query("""
            SELECT l.list_name, mm.rank, m.title, m.letterboxd_uri
            FROM movie_list_membership AS mm
            JOIN movies AS m ON m.movie_id = mm.movie_id
            JOIN movie_lists AS l ON l.list_id = mm.list_id
            ORDER BY l.list_name, mm.rank
        """, con)
