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
