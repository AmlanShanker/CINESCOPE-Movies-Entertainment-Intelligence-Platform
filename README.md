# 🎬 CineScope — Movies & Entertainment Intelligence Platform

<p align="center">
  <strong>Discover the stories behind the screen.</strong><br/>
  An interactive movie catalogue and intelligence dashboard built with Python, Streamlit, SQLite, Plotly and TMDB.
</p>

<p align="center">
  <a href="https://cinescope-amlanshanker.streamlit.app/">🚀 Live Demo</a> ·
  <a href="https://github.com/AmlanShanker/CINESCOPE-Movies-Entertainment-Intelligence-Platform">💻 Source Code</a>
</p>

---

## Overview

**CineScope** brings curated movie collections together in one place. It transforms Letterboxd CSV lists into a searchable, poster-led movie catalogue, then enriches eligible records with metadata and artwork from [The Movie Database (TMDB)](https://www.themoviedb.org/).

Explore collection-level insights, find films by title or release year, open detailed movie pages, and compare two movies side by side with **Movie Face-Off**.

> CineScope is an exploration and collection-intelligence project. It distinguishes curated-list rankings from TMDB user ratings.

## ✨ Features

### 📊 Collection dashboard
- Overview metrics for loaded lists, list entries, unique movies and movies appearing in multiple lists.
- Data-quality report showing rows read, valid rows and rejected rows for each source CSV.
- Interactive Plotly charts for entries by list and collection overlap.
- SQLite-backed dashboard data, refreshed from the source CSVs when the app runs.

### 🎞️ Movie catalogue
- Poster-first catalogue using TMDB poster artwork.
- Search movie titles and filter by release year, including an unknown-year option.
- Paginated poster grid (40 movies per page).
- Select a poster to open a dedicated movie detail view in the same browser tab.

### 🔎 Movie details
Where TMDB provides the information, a movie detail view can show:
- Release year and release date
- Runtime and original language
- Genres and synopsis
- TMDB user score and vote count
- Links to the movie's Letterboxd and TMDB pages
- The curated lists in which the movie appears, with its rank in each list

### ⚔️ Movie Face-Off
Choose two different movies and compare their available:
- TMDB user scores and vote counts
- Runtime, genres and original language
- Curated-list appearances
- Shared genres and shared source lists
- Synopses and score visualisation

The comparison uses available catalogue metadata; it is not a prediction of which movie is better.

### 🔄 Data ingestion and TMDB enrichment
- Loads three curated Letterboxd CSV datasets.
- Handles UTF-8 and UTF-8-with-BOM input.
- Validates required columns and records before import.
- Stores one canonical movie record per Letterboxd URL and keeps list memberships/ranks separately.
- Automatically checks unchecked movie records against TMDB when a token is configured.
- Caches matched, ambiguous and unmatched lookup outcomes in SQLite and retries records left pending after temporary API failures.
- Uses conservative title matching: ambiguous or non-exact matches are not guessed.

## 🧰 Tech stack

| Technology | Purpose |
|---|---|
| Python | Application logic and data processing |
| Streamlit | Interactive web application |
| Pandas | CSV ingestion and data manipulation |
| SQLite | Persistent movie catalogue, list memberships and TMDB metadata |
| Plotly Express | Interactive charts and visual comparisons |
| TMDB API | Movie metadata and poster artwork |
| Pytest | Automated tests |

## 🗂️ Source datasets

Place the following source files in `data/raw/`:

| Curated collection | Filename |
|---|---|
| Top 500 with Narrative Features | `top_500.csv` |
| Top 250 with Most Fans | `top_250.csv` |
| 2026 Movies Released | `2026_mov.csv` |

Each CSV must contain these columns:

- `Rank` — position of the movie in that source list
- `Title` — movie title
- `LetterboxdURI` — Letterboxd movie URL used to identify the movie

**Important:** A source-list rank is not a movie rating. TMDB ratings and metadata are separate data sourced from TMDB.

## 🚀 Getting started

### 1. Clone the repository

```bash
git clone https://github.com/AmlanShanker/CINESCOPE-Movies-Entertainment-Intelligence-Platform.git
cd CINESCOPE-Movies-Entertainment-Intelligence-Platform
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add the source CSV files

Create `data/raw/` if it does not exist, then add the three CSV files listed above.

### 5. Configure TMDB (recommended)

Create `.streamlit/secrets.toml` in the project root:

```toml
TMDB_READ_ACCESS_TOKEN = "your-tmdb-read-access-token"
```

Alternatively, set the `TMDB_READ_ACCESS_TOKEN` environment variable.

The application uses the TMDB API Read Access Token as a Bearer token. A v3 API key is not required for this integration. Keep your token private: do not commit it, hard-code it or include it in screenshots.

Without a token, the source catalogue and collection dashboard can still load, but TMDB-powered poster artwork and metadata enrichment will not be available.

### 6. Run the tests

```bash
pytest -q
```

### 7. Launch CineScope

```bash
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) where you can open the application.

## 🗄️ Data and enrichment workflow

1. CineScope reads and validates the configured source CSV files.
2. Valid movie records and their separate list memberships are synchronised to SQLite.
3. The dashboard and catalogue query the SQLite database.
4. When a TMDB token is configured, unchecked records are searched against TMDB.
5. Lookup outcomes and available metadata are cached in the database.
6. Full movie details are fetched and cached when a user opens a movie detail page.

The generated database is stored at `database/cinescope.db`. It is created and refreshed by the application and is not intended to be committed. If a TMDB request is temporarily unavailable or rate-limited, unfinished records remain pending for a later run.

**Matching limitation:** The source CSVs do not include release years. Same-title remakes can therefore be difficult to distinguish. CineScope uses conservative title matching and leaves ambiguous results unmatched rather than silently selecting a potentially incorrect movie.

**Poster visibility:** The public poster catalogue displays movies for which a TMDB poster path is available. Movies without poster artwork remain preserved in SQLite and the original source files, even though they are not shown in the poster grid.

## ☁️ Streamlit Community Cloud deployment

1. Push the project to GitHub.
2. Create a new app in [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select this repository, the deployment branch and `app.py` as the main file.
4. Open the app's **Settings → Secrets** section.
5. Add your TMDB token in TOML format:

   ```toml
   TMDB_READ_ACCESS_TOKEN = "your-tmdb-read-access-token"
   ```

6. Deploy the app.

Do not put secrets in the repository. The SQLite database is generated by the application; for deployments that need data to survive environment resets, use an appropriate persistent storage strategy.

## 🧪 Tests

Run the automated test suite with:

```bash
pytest -q
```

The project includes tests for CSV validation, UTF-8 BOM handling and database synchronisation.

## 📁 Project structure

```text
.
├── app.py
├── requirements.txt
├── data/
│   └── raw/                 # Source Letterboxd CSV files
├── database/
│   └── cinescope.db         # Generated SQLite database
├── ingestion/
│   ├── csv_loader.py        # CSV loading and validation
│   └── tmdb_client.py       # TMDB API integration
├── .streamlit/
│   └── secrets.toml         # Local secrets (do not commit)
└── tests/                   # Automated tests
```

The database and secrets files are generated or configured locally and should remain untracked. Refer to the repository's ignore rules for the exact exclusions.

## ⚠️ Data notes and attribution

- Letterboxd list positions represent **curated-list ranks**, not ratings.
- TMDB scores represent TMDB user ratings and may change as votes are updated.
- Metadata availability depends on TMDB matching and the fields returned by the API.
- Review [TMDB's terms, attribution and branding requirements](https://www.themoviedb.org/documentation/api/terms-of-use) before deploying or redistributing TMDB-powered content.

## 🛣️ Project scope

The current application focuses on curated-list ingestion, collection analytics, TMDB-enriched movie discovery, movie details and side-by-side comparison.

## 🤝 Contributing

Ideas, bug reports and improvements are welcome. Feel free to open an issue or submit a pull request.

## 📄 License

No license is specified in this README. Add a `LICENSE` file if you intend to grant others explicit permission to use, modify or distribute this project.

---

<p align="center">
  Built with 🎬 and data by <a href="https://github.com/AmlanShanker">Amlan Shanker</a>
</p>
