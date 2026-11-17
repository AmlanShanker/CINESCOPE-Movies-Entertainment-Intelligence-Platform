# CineScope — Movies & Entertainment Intelligence Platform

CineScope is a Python + Streamlit Smart Dashboard Application for PYTHON Programming (MCA411-2), Component 3, at CHRIST University.

## Implemented

- Streamlit dashboard with dataset health and movie exploration.
- CSV ingestion for three curated Letterboxd lists, including UTF-8 BOM handling.
- Validation of Rank, Title and LetterboxdURI.
- Normalized SQLite storage: one master movie record per Letterboxd URL and separate list memberships/ranks.
- Repeatable database refresh and query functions.
- Dashboard reads its catalogue and memberships from SQLite.
- Automated tests for CSV validation, BOM handling and database synchronization.

## Source CSV files

Place these files in `data/raw/`:

| List name | Filename |
|---|---|
| Top 500 with Narrative Features | `top_500.csv` |
| Top 250 with Most Fans | `top_250.csv` |
| 2026 Movies Released | `2026_mov.csv` |

Each CSV must contain `Rank`, `Title`, and `LetterboxdURI`. The loader reads UTF-8 and UTF-8-with-BOM files. Keep the original source files in `data/raw/`; the SQLite database is generated automatically at `database/cinescope.db` and is not intended to be committed.

**Data interpretation:** Rank is a position in a curated list, not a movie rating. The CSVs do not establish IMDb ratings, genres, revenue, OTT availability, sentiment or verified release status. Enrich these fields from separately verified sources before analysis.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

On startup, CineScope validates the source CSV files, synchronizes the SQLite database, and then reads the dashboard data from SQLite. The refresh is repeatable and preserves a movie's separate rank in each source list.

## TMDB poster and metadata enrichment

CineScope can enrich its catalogue using the TMDB API. Add your TMDB API Read Access Token to a local Streamlit secrets file:

```toml
TMDB_READ_ACCESS_TOKEN = "your-read-access-token"
```

Create the file at `.streamlit/secrets.toml` in the project root. This path is ignored by Git. Never commit the token, paste it into source code, or share it in screenshots. The Read Access Token is used as a Bearer token; the v3 API key is not required by this integration.

When the app opens, CineScope automatically checks **every movie record that has not already been checked**. It uses one TMDB search request per title and stores matched, ambiguous and unmatched results in SQLite. If TMDB temporarily rate-limits or cannot be reached, the remaining records stay pending and are retried the next time the app runs. Matching is deliberately conservative: a normalized exact title match is required; ambiguous titles are left unmatched rather than guessed. The current Letterboxd CSVs do not include release years, so some same-title remakes may need manual review. The catalogue displays every source movie, provides a release-year filter, and makes each poster (or clearly labelled placeholder artwork) clickable to open a dedicated details view. Full TMDB details are fetched and cached when a movie's detail view is opened.

Poster image URLs are built from TMDB's poster paths at display time. TMDB metadata and ratings are distinct from Letterboxd list ranks. Review TMDB's attribution and usage requirements before public deployment.

## Planned modules

1. Executive Overview
2. Movie Analytics
3. Box Office Intelligence
4. OTT Analytics
5. Indian Cinema
6. Recommendations
7. Sentiment Analysis
8. Movie Success Prediction
9. Celebrity & Awards Analytics

Box Office, OTT, Indian Cinema, recommendations, sentiment, prediction and celebrity/awards features remain planned. API enrichment, model evaluation, expanded testing and deployment are future work.
