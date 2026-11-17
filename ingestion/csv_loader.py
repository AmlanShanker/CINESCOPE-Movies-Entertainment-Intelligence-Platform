"""Reusable ingestion for CineScope's three Letterboxd CSV lists."""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATASETS = [
    {"name": "Top 500 with Narrative Features", "filename": "top_500.csv"},
    {"name": "Top 250 with Most Fans", "filename": "top_250.csv"},
    {"name": "2026 Movies Released", "filename": "2026_mov.csv"},
]
REQUIRED = ["Rank", "Title", "LetterboxdURI"]


def load_dataset(path, list_name):
    path = Path(path)
    report = {"name": list_name, "filename": path.name, "rows_read": 0,
              "valid_rows": 0, "rejected_rows": 0, "errors": []}
    empty_movies = pd.DataFrame(columns=["title", "letterboxd_uri"])
    empty_members = pd.DataFrame(columns=["list_name", "rank", "title", "letterboxd_uri"])
    if not path.exists():
        report["errors"].append(f"{path.name}: file not found")
        return empty_movies, empty_members, report
    try:
        frame = pd.read_csv(path, encoding="utf-8-sig")
    except Exception as exc:
        report["errors"].append(f"{path.name}: could not read CSV: {exc}")
        return empty_movies, empty_members, report
    frame.columns = [str(c).strip() for c in frame.columns]
    report["rows_read"] = len(frame)
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        report["errors"].append("Missing required columns: " + ", ".join(missing))
        report["rejected_rows"] = len(frame)
        return empty_movies, empty_members, report

    work = frame[REQUIRED].copy()
    work["Title"] = work["Title"].astype("string").str.strip()
    work["LetterboxdURI"] = work["LetterboxdURI"].astype("string").str.strip()
    work["Rank"] = pd.to_numeric(work["Rank"], errors="coerce")
    valid = (
        work["Title"].notna() & work["Title"].ne("")
        & work["LetterboxdURI"].str.match(
            r"^https?://(?:www\.)?letterboxd\.com/film/[^\s]+/?$",
            case=False, na=False
        )
        & work["Rank"].notna() & work["Rank"].gt(0)
        & work["Rank"].mod(1).eq(0)
    )
    clean = work.loc[valid].copy()
    duplicate_count = int(clean["LetterboxdURI"].duplicated().sum())
    if duplicate_count:
        report["errors"].append(
            f"{duplicate_count} duplicate URL row(s) removed within this list."
        )
    clean = clean.drop_duplicates("LetterboxdURI", keep="first")
    clean["Rank"] = clean["Rank"].astype("int64")
    movies = clean[["Title", "LetterboxdURI"]].rename(
        columns={"Title": "title", "LetterboxdURI": "letterboxd_uri"}
    ).drop_duplicates("letterboxd_uri").reset_index(drop=True)
    members = clean[["Rank", "Title", "LetterboxdURI"]].rename(
        columns={"Rank": "rank", "Title": "title", "LetterboxdURI": "letterboxd_uri"}
    )
    members.insert(0, "list_name", list_name)
    report["valid_rows"] = len(members)
    report["rejected_rows"] = report["rows_read"] - int(valid.sum())
    if report["rejected_rows"]:
        report["errors"].append(f"{report['rejected_rows']} invalid row(s) excluded.")
    return movies, members.reset_index(drop=True), report


def load_all_datasets(data_dir=RAW_DATA_DIR):
    movie_frames, member_frames, reports = [], [], []
    for item in DATASETS:
        movies, members, report = load_dataset(
            Path(data_dir) / item["filename"], item["name"]
        )
        reports.append(report)
        if not movies.empty:
            movie_frames.append(movies)
        if not members.empty:
            member_frames.append(members)
    movies = (pd.concat(movie_frames, ignore_index=True)
              .drop_duplicates("letterboxd_uri").reset_index(drop=True)
              if movie_frames else pd.DataFrame(columns=["title", "letterboxd_uri"]))
    members = (pd.concat(member_frames, ignore_index=True)
               if member_frames else pd.DataFrame(
                   columns=["list_name", "rank", "title", "letterboxd_uri"]))
    return movies, members, {
        "loaded": [r for r in reports if r["valid_rows"] > 0],
        "reports": reports,
        "errors": [message for r in reports for message in r["errors"]],
    }
