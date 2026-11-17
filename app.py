import html
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
selected_id = st.query_params.get("movie_id")
if not selected_id:
    st.title("🎬 CineScope")
    st.subheader("Movies & Entertainment Intelligence Platform")
    st.caption("PYTHON Programming (MCA411-2) | Component 3 | CHRIST University")
    st.write("Explore curated movie lists through a data-driven Python and Streamlit dashboard.")

if not selected_id:
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


tmdb_token = (
    st.secrets.get("TMDB_READ_ACCESS_TOKEN")
    or st.secrets.get("tmdb", {}).get("read_access_token")
    or os.getenv("TMDB_READ_ACCESS_TOKEN")
)



if not selected_id:
    st.divider()
    st.header("🎞️ Movie catalogue")

# Process every unchecked source record automatically. Each title uses one
# TMDB search request; successful, ambiguous and unmatched results are cached.
pending = get_pending_tmdb_movies(limit=max(len(movies), 1)) if not selected_id else pd.DataFrame()
if not selected_id and tmdb_token and not pending.empty:
    client = TMDBClient(tmdb_token)
    progress = st.progress(0, text=f"Checking all {len(pending)} remaining movie records…")
    completed = 0
    failed_title = None
    for _, row in pending.iterrows():
        try:
            metadata = client.enrich_title(row["title"])
            save_tmdb_metadata(row["movie_id"], metadata)
            completed += 1
            progress.progress(
                completed / len(pending),
                text=f"TMDB catalogue enrichment: {completed} of {len(pending)} records checked",
            )
        except Exception as exc:
            failed_title = row["title"]
            st.warning(
                f"TMDB temporarily stopped while checking '{failed_title}'. "
                "The remaining records are still pending and will be retried automatically "
                "when the app is run again."
            )
            break
    progress.empty()
    if failed_title is None and completed:
        st.success(f"Finished checking {completed} movie record(s).")



catalogue = get_movie_catalogue()
has_poster = catalogue["poster_path"].fillna("").astype(str).str.strip().ne("")
poster_catalogue = catalogue.loc[has_poster].copy()
# A query-string route gives each poster a shareable, dedicated detail view.
selected_id = st.query_params.get("movie_id")
if selected_id:
    try:
        selected_id = int(selected_id)
        selected_rows = poster_catalogue[poster_catalogue["movie_id"] == selected_id]
    except (TypeError, ValueError):
        selected_rows = catalogue.iloc[0:0]

    if selected_rows.empty:
        st.error("That movie could not be found in the current catalogue.")
    else:
        movie = selected_rows.iloc[0]
        st.subheader(str(movie["title"]))
        if st.button("← Back to movie catalogue"):
            st.query_params.clear()
            st.rerun()

        # Fetch full TMDB detail fields only when a movie's detail page is opened.
        if tmdb_token and pd.notna(movie["tmdb_id"]) and (
            pd.isna(movie["runtime"]) or not movie["genres_json"] or movie["genres_json"] == "[]"
        ):
            try:
                details = TMDBClient(tmdb_token).movie_details(int(movie["tmdb_id"]))
                save_tmdb_metadata(int(movie["movie_id"]), {
                    "tmdb_id": details.get("id"),
                    "poster_path": details.get("poster_path"),
                    "backdrop_path": details.get("backdrop_path"),
                    "overview": details.get("overview"),
                    "release_date": details.get("release_date"),
                    "original_language": details.get("original_language"),
                    "vote_average": details.get("vote_average"),
                    "vote_count": details.get("vote_count"),
                    "runtime": details.get("runtime"),
                    "genres": [g.get("name") for g in details.get("genres", [])],
                    "match_status": "matched",
                })
                catalogue = get_movie_catalogue()
                movie = catalogue[catalogue["movie_id"] == selected_id].iloc[0]
            except Exception:
                st.info("Additional TMDB details are temporarily unavailable; showing the cached information.")

        detail_left, detail_right = st.columns([1, 2])
        with detail_left:
            image_url = poster_url(movie["poster_path"])
            st.image(image_url, use_container_width=True)
        with detail_right:
            release_date = movie["release_date"] if pd.notna(movie["release_date"]) else "Not available"
            year = str(release_date)[:4] if release_date != "Not available" else "Unknown"
            st.markdown(f"**Release year:** {year}")
            st.markdown(f"**Release date:** {release_date}")
            st.markdown(f"**Runtime:** {int(movie['runtime'])} minutes" if pd.notna(movie["runtime"]) else "**Runtime:** Not available")
            st.markdown(f"**Original language:** {movie['original_language'] or 'Not available'}")
            if pd.notna(movie["vote_average"]):
                st.markdown(f"**TMDB rating:** {float(movie['vote_average']):.1f}/10 ({int(movie['vote_count'] or 0):,} votes)")
            genres = json.loads(movie["genres_json"] or "[]")
            st.markdown("**Genres:** " + (", ".join(genres) if genres else "Not available"))
            st.markdown("**Overview**")
            st.write(movie["overview"] or "No synopsis is available from TMDB.")
            st.markdown(f"[Open Letterboxd page]({movie['letterboxd_uri']})")
            if pd.notna(movie["tmdb_id"]):
                st.markdown(f"[Open TMDB page](https://www.themoviedb.org/movie/{int(movie['tmdb_id'])})")

        source_rows = memberships[memberships["letterboxd_uri"] == movie["letterboxd_uri"]]
        st.markdown("**Curated list appearances**")
        if source_rows.empty:
            st.caption("No source-list membership found.")
        else:
            st.dataframe(
                source_rows[["list_name", "rank"]].rename(
                    columns={"list_name": "List", "rank": "List rank"}
                ),
                use_container_width=True,
                hide_index=True,
            )
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

matched_count = int(catalogue["tmdb_id"].notna().sum())
checked_count = int(catalogue["match_status"].notna().sum())
pending_count = max(0, len(catalogue) - checked_count)
poster_count = len(poster_catalogue)
hidden_count = len(catalogue) - poster_count
col1, col2, col3, col4 = st.columns(4)
col1.metric("Source movies", len(catalogue))
col2.metric("Movies with posters", poster_count)
col3.metric("Hidden (no poster)", hidden_count)
col4.metric("Lookups remaining", pending_count)
st.caption("Only movies with an official TMDB poster are shown. Movies without poster artwork remain stored in SQLite and the original CSV files.")


search = st.text_input("Search movie titles", key="catalogue_search")
year_values = (
    poster_catalogue["release_date"].fillna("").astype(str).str[:4]
    .where(poster_catalogue["release_date"].notna(), "")
)
available_years = sorted(
    {value for value in year_values if value.isdigit()}, reverse=True
)
year_options = ["All years"] + available_years + ["Unknown year"]
selected_year = st.selectbox("Filter by release year", year_options)

filtered = poster_catalogue.copy()
if search.strip():
    filtered = filtered[filtered["title"].str.contains(search.strip(), case=False, na=False)]
if selected_year == "Unknown year":
    filtered = filtered[year_values.loc[filtered.index] == ""]
elif selected_year != "All years":
    filtered = filtered[year_values.loc[filtered.index] == selected_year]

st.caption(f"Showing {len(filtered)} of {len(poster_catalogue)} movies with official posters. Select a poster to view its details.")
if filtered.empty:
    st.info("No movies match the selected search and year.")
else:
    page_size = 40
    page_count = max(1, (len(filtered) + page_size - 1) // page_size)
    current_page = int(st.session_state.get("poster_page", 1))
    st.session_state["poster_page"] = min(max(current_page, 1), page_count)
    page = st.session_state["poster_page"]
    visible = filtered.iloc[(page - 1) * page_size : page * page_size]
    poster_cols = st.columns(5)
    for idx, (_, movie) in enumerate(visible.iterrows()):
        with poster_cols[idx % 5]:
            image_url = poster_url(movie["poster_path"])
            movie_id = int(movie["movie_id"])
            title_text = html.escape(str(movie["title"]))
            st.markdown(
                f'<a href="?movie_id={movie_id}" target="_self" title="View {title_text}">'
                f'<img src="{image_url}" alt="{title_text}" '
                'style="width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:8px;cursor:pointer;" />'
                '</a>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**{movie['title']}**")
            release_year = str(movie["release_date"] or "")[:4]
            if release_year and release_year != "nan":
                st.caption(release_year)
            if pd.notna(movie["vote_average"]):
                st.caption(f"TMDB ★ {float(movie['vote_average']):.1f} · {int(movie['vote_count'] or 0):,} votes")

    st.divider()
    st.selectbox(
        "Poster page",
        options=list(range(1, page_count + 1)),
        format_func=lambda value: f"Page {value} of {page_count}",
        key="poster_page",
    )

st.info(
    "List rank is not a movie rating. TMDB ratings are separate from Letterboxd list ranks. "
    "Revenue, OTT availability, sentiment and verified release status require additional verified sources."
)
