from ingestion.tmdb_client import normalize_title, poster_url


def test_normalize_title_ignores_punctuation_and_case():
    assert normalize_title("Spider-Man: No Way Home") == "spider man no way home"


def test_poster_url_handles_missing_path():
    assert poster_url("/abc.jpg") == "https://image.tmdb.org/t/p/w500/abc.jpg"
    assert poster_url(None) is None


def test_enrich_title_uses_single_search_request(monkeypatch):
    from ingestion.tmdb_client import TMDBClient

    calls = []

    def fake_get(self, endpoint, params=None):
        calls.append(endpoint)
        return {
            "results": [{
                "id": 123,
                "title": "Example Movie",
                "original_title": "Example Movie",
                "poster_path": "/example.jpg",
                "release_date": "2020-01-01",
                "overview": "An example synopsis.",
                "vote_average": 7.5,
                "vote_count": 100,
            }]
        }

    monkeypatch.setattr(TMDBClient, "_get", fake_get)
    metadata = TMDBClient("test-token").enrich_title("Example Movie")

    assert calls == ["search/movie"]
    assert metadata["tmdb_id"] == 123
    assert metadata["poster_path"] == "/example.jpg"
    assert metadata["match_status"] == "matched"
