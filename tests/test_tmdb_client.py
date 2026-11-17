from ingestion.tmdb_client import normalize_title, poster_url


def test_normalize_title_ignores_punctuation_and_case():
    assert normalize_title("Spider-Man: No Way Home") == "spider man no way home"


def test_poster_url_handles_missing_path():
    assert poster_url("/abc.jpg") == "https://image.tmdb.org/t/p/w500/abc.jpg"
    assert poster_url(None) is None
