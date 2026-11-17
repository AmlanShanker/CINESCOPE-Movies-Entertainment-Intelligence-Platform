import pandas as pd
from ingestion.csv_loader import load_dataset


def test_loader_keeps_valid_rows_and_rejects_invalid_rank(tmp_path):
    path = tmp_path / "sample.csv"
    pd.DataFrame([
        {"Rank": 1, "Title": "Film A", "LetterboxdURI": "https://letterboxd.com/film/film-a/"},
        {"Rank": 0, "Title": "Film B", "LetterboxdURI": "https://letterboxd.com/film/film-b/"},
    ]).to_csv(path, index=False)
    movies, members, report = load_dataset(path, "Example")
    assert len(movies) == 1
    assert len(members) == 1
    assert members.iloc[0]["rank"] == 1
    assert report["rejected_rows"] == 1


def test_loader_reports_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([{"Title": "Film A"}]).to_csv(path, index=False)
    movies, members, report = load_dataset(path, "Bad")
    assert movies.empty and members.empty
    assert report["rejected_rows"] == 1
    assert "Missing required columns" in report["errors"][0]
