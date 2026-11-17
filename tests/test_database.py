import pandas as pd

from database.db import get_memberships, get_movies, refresh_database


def test_refresh_database_is_idempotent_and_preserves_list_ranks(tmp_path):
    db_path = tmp_path / "test.sqlite"
    movies = pd.DataFrame([
        {"title": "Film A", "letterboxd_uri": "https://letterboxd.com/film/film-a/"},
        {"title": "Film B", "letterboxd_uri": "https://letterboxd.com/film/film-b/"},
    ])
    memberships = pd.DataFrame([
        {"list_name": "List One", "rank": 1, "title": "Film A",
         "letterboxd_uri": "https://letterboxd.com/film/film-a/"},
        {"list_name": "List One", "rank": 2, "title": "Film B",
         "letterboxd_uri": "https://letterboxd.com/film/film-b/"},
        {"list_name": "List Two", "rank": 1, "title": "Film A",
         "letterboxd_uri": "https://letterboxd.com/film/film-a/"},
    ])

    refresh_database(movies, memberships, db_path)
    refresh_database(movies, memberships, db_path)

    stored_movies = get_movies(db_path)
    stored_memberships = get_memberships(db_path)

    assert len(stored_movies) == 2
    assert len(stored_memberships) == 3
    film_a = stored_memberships[stored_memberships["title"] == "Film A"]
    assert set(film_a["list_name"]) == {"List One", "List Two"}
    assert dict(zip(film_a["list_name"], film_a["rank"])) == {
        "List One": 1, "List Two": 1
    }


def test_refresh_database_replaces_old_memberships_and_movies(tmp_path):
    db_path = tmp_path / "refresh.sqlite"
    first_movies = pd.DataFrame([
        {"title": "Old Film", "letterboxd_uri": "https://letterboxd.com/film/old-film/"}
    ])
    first_memberships = pd.DataFrame([
        {"list_name": "Old List", "rank": 1, "title": "Old Film",
         "letterboxd_uri": "https://letterboxd.com/film/old-film/"}
    ])
    refresh_database(first_movies, first_memberships, db_path)

    new_movies = pd.DataFrame([
        {"title": "New Film", "letterboxd_uri": "https://letterboxd.com/film/new-film/"}
    ])
    new_memberships = pd.DataFrame([
        {"list_name": "New List", "rank": 3, "title": "New Film",
         "letterboxd_uri": "https://letterboxd.com/film/new-film/"}
    ])
    refresh_database(new_movies, new_memberships, db_path)

    assert list(get_movies(db_path)["title"]) == ["New Film"]
    assert list(get_memberships(db_path)["list_name"]) == ["New List"]
    assert list(get_memberships(db_path)["rank"]) == [3]
