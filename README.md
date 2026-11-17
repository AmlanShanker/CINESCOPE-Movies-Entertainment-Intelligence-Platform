# CineScope — Movies & Entertainment Intelligence Platform

CineScope is a Python + Streamlit Smart Dashboard Application for PYTHON Programming (MCA411-2), Component 3, at CHRIST University.

## Current implementation

- Streamlit dashboard shell and dataset health overview.
- Reusable CSV ingestion for three curated Letterboxd lists.
- Validation of Rank, Title and LetterboxdURI.
- Unique movie master records keyed by Letterboxd URL, with separate list memberships.
- SQLite schema and basic ingestion tests.

## Source CSV files

Place these files in `data/raw/`:

| List name | Filename |
|---|---|
| Top 500 with Narrative Features | `top_500.csv` |
| Top 250 with Most Fans | `top_250.csv` |
| 2026 Movies Released | `2026_mov.csv` |

Each CSV must contain `Rank`, `Title`, and `LetterboxdURI`. The CSVs are not included in this repository; add them locally. The data directory is git-ignored to avoid publishing source data unintentionally.

**Data interpretation:** Rank is a position in a curated list, not a movie rating. The CSVs do not establish IMDb ratings, genres, revenue, OTT availability, sentiment or verified release status. Enrich these fields from separately verified sources before analysis.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run tests with `pytest -q`.

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

These are planned modules, not claims of completed functionality. API enrichment, model evaluation, expanded testing, documentation and deployment remain future work.
