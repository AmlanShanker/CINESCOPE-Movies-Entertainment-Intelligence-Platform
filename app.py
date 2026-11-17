import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from database.db import (
    get_memberships, get_movie_catalogue, get_movies,
    get_pending_tmdb_movies, refresh_database, save_tmdb_metadata,
)
from ingestion.csv_loader import DATASETS, load_all_datasets
from ingestion.tmdb_client import TMDBClient, poster_url

st.set_page_config(page_title="CineScope", page_icon="🎬", layout="wide")
st.title("🎬 CineScope")
st.subheader("Movies & Entertainment Intelligence Platform")
st.caption("PYTHON Programming (MCA411-2) | Component 3 | CHRIST University")
st.write("Explore curated movie lists through a data-driven Python and Streamlit dashboard.")

with st.sidebar:
    st.header("Source data")
    st.code("data/raw/\ntop_500.csv\ntop_250.csv\n2026_mov.csv")
    st.caption("Required columns: Rank, Title, LetterboxdURI")
    st.caption("SQLite database: database/cinescope.db")
    st.divider()
    st.header("TMDB enrichment")
    st.caption("Posters and movie metadata are cached in SQLite.")
    st.link_button("TMDB API documentation", "https://developer.themoviedb.org/docs")

source_movies, source_memberships, report = load_all_datasets()
if not report["loaded"]:
    st.warning("No valid source CSVs found. Add the three files to data/raw/ to begin.")
    for item in DATASETS:
        st.write(f"{item['name']} — {item['filename']}")
    st.stop()

try:
    refresh_database(source_movies, source_memberships)
    movies = get_movies()
    memberships = get_memberships()
except Exception as exc:
    st.error(f"Could not synchronize the SQLite database: {exc}")
    st.stop()

if movies.empty or memberships.empty:
    st.warning("The source files loaded, but no valid movie-list memberships were imported.")
    st.stop()

membership_counts = memberships.groupby("letterboxd_uri")["list_name"].nunique()
shared_count = int((membership_counts > 1).sum())
a, b, c, d = st.columns(4)
a.metric("Lists loaded", len(report["loaded"]))
b.metric("List entries", len(memberships))
c.metric("Unique movies", len(movies))
d.metric("Movies in multiple lists", shared_count)
st.caption("Dashboard data is read from SQLite and refreshed from the validated CSV sources on each app run.")

st.subheader("Data quality")
rows = [
    {"List": item["name"], "File": item["filename"], "Rows read": item["rows_read"],
     "Valid": item["valid_rows"], "Rejected": item["rejected_rows"]}
    for item in report["reports"]
]
st.dataframe(rows, use_container_width=True, hide_index=True)
for message in report["errors"]:
    st.warning(message)

left, right = st.columns(2)
with left:
    st.subheader("Movies by list")
    counts = memberships.groupby("list_name", as_index=False).size()
    fig = px.bar(counts, x="list_name", y="size", color="list_name",
                 labels={"list_name": "Curated list", "size": "Movie entries"})
    fig.update_layout(showlegend=False, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Overlap across lists")
    overlap = memberships.groupby("list_name")["letterboxd_uri"].nunique().rename(
        "Unique movies").reset_index()
    overlap_fig = px.pie(overlap, names="list_name", values="Unique movies")
    st.plotly_chart(overlap_fig, use_container_width=True)

tmdb_token = (
    st.secrets.get("TMDB_READ_ACCESS_TOKEN")
    or st.secrets.get("tmdb", {}).get("read_access_token")
    or os.getenv("TMDB_READ_ACCESS_TOKEN")
)

st.divider()
st.header("🎞️ Movie catalogue")

# Automatically enrich a small batch once per Streamlit session. Results are
# persisted in SQLite, so completed lookups are not repeated on later runs.
if tmdb_token and not st.session_state.get("tmdb_auto_enrichment_started", False):
    st.session_state["tmdb_auto_enrichment_started"] = True
    pending = get_pending_tmdb_movies(limit=40)
    if not pending.empty:
        client = TMDBClient(tmdb_token)
        progress = st.progress(0, text="Automatically loading movie posters…")
        completed = 0
        for _, row in pending.iterrows():
            try:
                metadata = client.enrich_title(row["title"])
                save_tmdb_metadata(row["movie_id"], metadata)
                completed += 1
                progress.progress(
                    completed / len(pending),
                    text=f"Loading movie artwork ({completed}/{len(pending)})…",
                )
            except Exception:
                # Keep the dashboard usable if TMDB is temporarily unavailable.
                # Unprocessed movies remain pending and can be retried next session.
                break
        progress.empty()

catalogue = get_movie_catalogue()
matched_count = int(catalogue["tmdb_id"].notna().sum())
checked_count = int(catalogue["match_status"].notna().sum())
pending_count = len(movies) - checked_count
col1, col2, col3 = st.columns(3)
col1.metric("TMDB matched", matched_count)
col2.metric("Not yet checked", pending_count)
col3.metric("Movies without a poster", int(catalogue["poster_path"].isna().sum()))

search = st.text_input("Search movie titles", key="catalogue_search")
matched = catalogue[catalogue["tmdb_id"].notna()].copy()
if search.strip():
    matched = matched[matched["title"].str.contains(search.strip(), case=False, na=False)]

st.caption(f"{len(matched)} TMDB-matched movies")
if matched.empty:
    st.info("Movie artwork will appear here as the catalogue is automatically enriched.")
else:
    page_size = 40
    page_count = max(1, (len(matched) + page_size - 1) // page_size)
    page = st.selectbox(
        "Poster page",
        options=list(range(1, page_count + 1)),
        format_func=lambda value: f"Page {value} of {page_count}",
    )
    visible = matched.iloc[(page - 1) * page_size : page * page_size]
    poster_cols = st.columns(5)
    for idx, (_, movie) in enumerate(visible.iterrows()):
        with poster_cols[idx % 5]:
            image_url = poster_url(movie["poster_path"])
            if image_url:
                st.image(image_url, use_container_width=True)
            else:
                st.markdown("🎬")
            st.markdown(f"**{movie['title']}**")
            release_year = str(movie["release_date"] or "")[:4]
            if release_year:
                st.caption(release_year)
            if pd.notna(movie["vote_average"]):
                st.caption(f"TMDB ★ {movie['vote_average']:.1f} · {int(movie['vote_count'] or 0)} votes")
            with st.expander("Details"):
                st.write(movie["overview"] or "No overview available.")
                genres = json.loads(movie["genres_json"] or "[]")
                if genres:
                    st.caption("Genres: " + ", ".join(genres))
                st.caption(f"TMDB ID: {int(movie['tmdb_id'])}")

with st.expander("Show all movie records and TMDB match status"):
    display = catalogue[["title", "release_date", "vote_average", "match_status"]].copy()
    display.columns = ["Title", "Release date", "TMDB rating", "Match status"]
    st.dataframe(display, use_container_width=True, hide_index=True)

st.info(
    "List rank is not a movie rating. TMDB ratings are separate from Letterboxd list ranks. "
    "Revenue, OTT availability, sentiment and verified release status require additional verified sources."
)
