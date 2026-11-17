"""SQLite persistence for CineScope's movie catalogue and list memberships."""
import json
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
        CREATE TABLE IF NOT EXISTS tmdb_metadata (
            movie_id INTEGER PRIMARY KEY REFERENCES movies(movie_id) ON DELETE CASCADE,
            tmdb_id INTEGER UNIQUE,
            poster_path TEXT,
            backdrop_path TEXT,
            overview TEXT,
            release_date TEXT,
            original_language TEXT,
            vote_average REAL,
            vote_count INTEGER,
            runtime INTEGER,
            genres_json TEXT NOT NULL DEFAULT '[]',
            match_status TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)


def refresh_database(movies, memberships, db_path=DEFAULT_DB):
    """Synchronize SQLite with validated DataFrames; safe to run repeatedly."""
    initialise_database(db_path)
    movie_columns = {"title", "letterboxd_uri"}
    member_columns = {"list_name", "rank", "title", "letterboxd_uri"}
    if not movie_columns.issubset(movies.columns):
        raise ValueError(f"movies must contain columns: {sorted(movie_columns)}")
    if not member_columns.issubset(memberships.columns):
        raise ValueError(f"memberships must contain columns: {sorted(member_columns)}")

    with _connect(db_path) as con:
        for row in movies[["title", "letterboxd_uri"]].itertuples(index=False, name=None):
            title, uri = map(str, row)
            con.execute(
                """INSERT INTO movies(title, letterboxd_uri) VALUES (?, ?)
                   ON CONFLICT(letterboxd_uri) DO UPDATE SET title=excluded.title""",
                (title, uri),
            )

        con.execute("DELETE FROM movie_list_membership")
        con.execute("DELETE FROM movie_lists")
        for list_name in memberships["list_name"].dropna().astype(str).unique():
            con.execute("INSERT INTO movie_lists(list_name) VALUES (?)", (list_name,))

        for row in memberships[["list_name", "rank", "letterboxd_uri"]].itertuples(index=False, name=None):
            list_name, rank, uri = row
            con.execute(
                """INSERT INTO movie_list_membership(movie_id, list_id, rank)
                   SELECT m.movie_id, l.list_id, ?
                   FROM movies AS m CROSS JOIN movie_lists AS l
                   WHERE m.letterboxd_uri = ? AND l.list_name = ?""",
                (int(rank), str(uri), str(list_name)),
            )

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
            "SELECT movie_id, title, letterboxd_uri FROM movies ORDER BY title", con
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


def get_movie_catalogue(db_path=DEFAULT_DB):
    """Return movies with any cached TMDB enrichment."""
    initialise_database(db_path)
    with _connect(db_path) as con:
        return pd.read_sql_query("""
            SELECT m.movie_id, m.title, m.letterboxd_uri,
                   t.tmdb_id, t.poster_path, t.backdrop_path, t.overview,
                   t.release_date, t.original_language, t.vote_average,
                   t.vote_count, t.runtime, t.genres_json, t.match_status
            FROM movies m
            LEFT JOIN tmdb_metadata t ON t.movie_id = m.movie_id
            ORDER BY m.title
        """, con)


def get_pending_tmdb_movies(limit=40, db_path=DEFAULT_DB):
    """Return movies that have not yet had a TMDB match attempt."""
    initialise_database(db_path)
    with _connect(db_path) as con:
        return pd.read_sql_query("""
            SELECT m.movie_id, m.title
            FROM movies m
            LEFT JOIN tmdb_metadata t ON t.movie_id = m.movie_id
            WHERE t.movie_id IS NULL
            ORDER BY m.title
            LIMIT ?
        """, con, params=(int(limit),))


def save_tmdb_metadata(movie_id, metadata, db_path=DEFAULT_DB):
    """Persist a successful, ambiguous, or unmatched TMDB lookup."""
    initialise_database(db_path)
    with _connect(db_path) as con:
        con.execute("""
            INSERT INTO tmdb_metadata (
                movie_id, tmdb_id, poster_path, backdrop_path, overview,
                release_date, original_language, vote_average, vote_count,
                runtime, genres_json, match_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(movie_id) DO UPDATE SET
                tmdb_id=excluded.tmdb_id,
                poster_path=excluded.poster_path,
                backdrop_path=excluded.backdrop_path,
                overview=excluded.overview,
                release_date=excluded.release_date,
                original_language=excluded.original_language,
                vote_average=excluded.vote_average,
                vote_count=excluded.vote_count,
                runtime=excluded.runtime,
                genres_json=excluded.genres_json,
                match_status=excluded.match_status,
                updated_at=CURRENT_TIMESTAMP
        """, (
            int(movie_id), metadata.get("tmdb_id"), metadata.get("poster_path"),
            metadata.get("backdrop_path"), metadata.get("overview"),
            metadata.get("release_date"), metadata.get("original_language"),
            metadata.get("vote_average"), metadata.get("vote_count"),
            metadata.get("runtime"), json.dumps(metadata.get("genres", [])),
            metadata.get("match_status", "unmatched"),
        ))
