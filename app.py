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
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');
.stApp{background:radial-gradient(ellipse at 12% 0%,rgba(111,35,70,.22),transparent 38%),radial-gradient(ellipse at 90% 8%,rgba(42,69,112,.20),transparent 34%),linear-gradient(160deg,#090b12,#10131d 48%,#090b12);color:#f4f4f7;font-family:'DM Sans',sans-serif}
h1,h2,h3{font-family:'Outfit',sans-serif!important;letter-spacing:-.035em}
[data-testid="stHeader"]{background:rgba(9,11,18,.72);backdrop-filter:blur(14px)}
[data-testid="stSidebar"]{display:none!important}[data-testid="stAppViewContainer"] .main .block-container{max-width:1440px;padding-top:2rem;padding-bottom:4rem}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(255,255,255,.075),rgba(255,255,255,.025));border:1px solid rgba(255,255,255,.10);border-radius:18px;padding:18px 20px;box-shadow:0 12px 34px rgba(0,0,0,.18);transition:transform .25s ease,border-color .25s ease,box-shadow .25s ease;animation:riseIn .7s both}
[data-testid="stMetric"]:hover{transform:translateY(-5px);border-color:rgba(255,61,90,.55);box-shadow:0 14px 38px rgba(255,61,90,.24)}
[data-testid="stMetricValue"]{font-family:'Outfit',sans-serif}
.stButton>button,.stLinkButton>a{border-radius:999px;border:1px solid rgba(255,255,255,.18);transition:all .22s ease;font-weight:600}
.stButton>button:hover,.stLinkButton>a:hover{border-color:#ff3d5a;color:#fff;box-shadow:0 0 22px rgba(255,61,90,.24);transform:translateY(-2px)}
[data-testid="stPlotlyChart"]{animation:fadeIn .9s ease both}
.cine-hero{position:relative;overflow:hidden;padding:clamp(28px,5vw,58px);border-radius:28px;margin:12px 0 28px;background:linear-gradient(115deg,rgba(31,20,34,.96),rgba(17,24,42,.94) 58%,rgba(42,19,34,.92));border:1px solid rgba(255,255,255,.13);box-shadow:0 24px 70px rgba(0,0,0,.35)}
.cine-hero:before{content:'';position:absolute;width:420px;height:420px;right:-100px;top:-240px;background:radial-gradient(circle,rgba(255,61,90,.34),transparent 68%);animation:ambientPulse 5s ease-in-out infinite alternate}
.cine-kicker{color:#ff8394;text-transform:uppercase;letter-spacing:.24em;font-size:.72rem;font-weight:700}
.cine-title{font-family:'Outfit',sans-serif;font-size:clamp(2.7rem,6vw,5.2rem);line-height:.98;font-weight:800;letter-spacing:-.055em;margin:12px 0}
.cine-title span{background:linear-gradient(90deg,#fff 5%,#ff8293 48%,#d9c5ff 95%);-webkit-background-clip:text;color:transparent}
.cine-subtitle{color:#c2c3d0;max-width:650px;font-size:1.04rem;line-height:1.7}
.cine-pulse{display:inline-block;width:8px;height:8px;border-radius:50%;background:#65e6b2;box-shadow:0 0 14px #65e6b2;margin-right:9px;animation:livePulse 1.8s infinite}
.cine-section{display:flex;align-items:center;gap:10px;margin:24px 0 12px;color:#f4f4f7;font-family:'Outfit',sans-serif;font-size:1.35rem;font-weight:700}
.cine-section:before{content:'';width:4px;height:24px;border-radius:8px;background:linear-gradient(#ff3d5a,#ff9c72);box-shadow:0 0 14px rgba(255,61,90,.24)}
.compare-panel{background:linear-gradient(145deg,rgba(255,255,255,.07),rgba(255,255,255,.025));border:1px solid rgba(255,255,255,.11);border-radius:20px;padding:18px;box-shadow:0 18px 45px rgba(0,0,0,.18);animation:riseIn .65s both}.compare-vs{font-family:'Outfit',sans-serif;font-weight:800;font-size:1.35rem;letter-spacing:.08em;color:#ff8293;text-align:center;padding-top:18px}.compare-label{color:#ff9aa8;text-transform:uppercase;letter-spacing:.14em;font-size:.68rem;font-weight:700}
.poster-card img{transition:transform .35s ease,filter .35s ease,box-shadow .35s ease}
.poster-card:hover img{transform:translateY(-7px) scale(1.025);filter:saturate(1.12) brightness(1.08);box-shadow:0 18px 38px rgba(255,61,90,.22)}
[data-testid="stImage"] img{border-radius:14px}
hr{border-color:rgba(255,255,255,.10)!important}
@keyframes riseIn{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes ambientPulse{from{transform:scale(.85);opacity:.65}to{transform:scale(1.18);opacity:1}}
@keyframes livePulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.45;transform:scale(.78)}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style>
""", unsafe_allow_html=True)
if not selected_id:
    st.markdown("""
    <section class="cine-hero">
      <div class="cine-kicker"><span class="cine-pulse"></span> YOUR PERSONAL CINEMA INTELLIGENCE HUB</div>
      <div class="cine-title"><span>CineScope</span></div>
      <div class="cine-subtitle">Discover the stories behind the screen. Explore curated movie collections, uncover connections across lists, and dive into film details through an immersive, data-powered experience.</div>
    </section>
    """, unsafe_allow_html=True)

# Source/API configuration is kept out of the viewer-facing layout.

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
    st.markdown('<div class="cine-section">🎞️ Explore the collection</div>', unsafe_allow_html=True)

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

st.markdown('<div class="cine-section">✦ Data quality</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="cine-section">▥ Movies by list</div>', unsafe_allow_html=True)
    counts = memberships.groupby("list_name", as_index=False).size()
    fig = px.bar(counts, x="list_name", y="size", color="list_name",
                 labels={"list_name": "Curated list", "size": "Movie entries"})
    fig.update_layout(showlegend=False, xaxis_title=None)
    fig.update_layout(transition_duration=700, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e9e9f0")
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.markdown('<div class="cine-section">◉ Collection overlap</div>', unsafe_allow_html=True)
    overlap = memberships.groupby("list_name")["letterboxd_uri"].nunique().rename(
        "Unique movies").reset_index()
    overlap_fig = px.pie(overlap, names="list_name", values="Unique movies")
    overlap_fig.update_layout(transition_duration=700, paper_bgcolor="rgba(0,0,0,0)", font_color="#e9e9f0")
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
                f'<a class="poster-card" href="?movie_id={movie_id}" target="_self" title="View {title_text}">'
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

# Interactive head-to-head comparison. Only poster-backed, TMDB-matched
# catalogue entries are offered so both sides have reliable artwork.
st.markdown('<div class="cine-section">⚔️ Movie Face-Off</div>', unsafe_allow_html=True)
st.caption("Pick two films and compare their available TMDB facts and curated-list footprints.")
if len(poster_catalogue) >= 2:
    comparison_ids = [int(value) for value in poster_catalogue["movie_id"].tolist()]
    movie_lookup = {
        int(row["movie_id"]): row
        for _, row in poster_catalogue.iterrows()
    }

    def comparison_label(movie_id):
        row = movie_lookup[int(movie_id)]
        release = row["release_date"]
        year = str(release)[:4] if pd.notna(release) and str(release) else "Year unknown"
        return f'{row["title"]} ({year})'

    pick_left, versus_col, pick_right = st.columns([5, 1, 5])
    with pick_left:
        left_query = st.text_input("Search first movie", placeholder="Type a title…", key="faceoff_search_left")
        left_options = [mid for mid in comparison_ids if left_query.strip().casefold() in str(movie_lookup[mid]["title"]).casefold()]
        if not left_options:
            st.warning("No first-movie matches. Try another title.")
    with versus_col:
        st.markdown('<div class="compare-vs">VS</div>', unsafe_allow_html=True)
    with pick_right:
        right_query = st.text_input("Search second movie", placeholder="Type a title…", key="faceoff_search_right")
        right_options = [mid for mid in comparison_ids if right_query.strip().casefold() in str(movie_lookup[mid]["title"]).casefold()]
        if not right_options:
            st.warning("No second-movie matches. Try another title.")

    if left_options and right_options:
        left_id = st.selectbox("Choose first film", options=left_options, format_func=comparison_label, key="compare_movie_left")
        right_id = st.selectbox("Choose second film", options=right_options, format_func=comparison_label, key="compare_movie_right")

    if not left_options or not right_options:
        st.info("Search for two titles to begin the face-off.")
    elif left_id == right_id:
        st.info("Choose two different movies to start the face-off.")
    else:
        left_movie = movie_lookup[int(left_id)]
        right_movie = movie_lookup[int(right_id)]

        def safe_text(value, fallback="Not available"):
            return fallback if pd.isna(value) or str(value).strip() == "" else str(value)

        def movie_year(row):
            value = safe_text(row["release_date"], "")
            return value[:4] if value else "Unknown"

        def movie_genres(row):
            try:
                values = json.loads(row["genres_json"] or "[]")
                return set(values) if isinstance(values, list) else set()
            except (TypeError, ValueError):
                return set()

        left_genres = movie_genres(left_movie)
        right_genres = movie_genres(right_movie)
        common_genres = sorted(left_genres & right_genres)
        left_members = set(memberships.loc[
            memberships["letterboxd_uri"] == left_movie["letterboxd_uri"], "list_name"
        ].dropna().astype(str))
        right_members = set(memberships.loc[
            memberships["letterboxd_uri"] == right_movie["letterboxd_uri"], "list_name"
        ].dropna().astype(str))
        common_lists = sorted(left_members & right_members)

        card_left, card_right = st.columns(2, gap="large")
        for card_col, row in ((card_left, left_movie), (card_right, right_movie)):
            with card_col:
                st.markdown('<div class="compare-panel">', unsafe_allow_html=True)
                st.image(poster_url(row["poster_path"]), use_container_width=True)
                st.markdown(f"### {row['title']}")
                st.markdown(
                    f'<div class="compare-label">{movie_year(row)} · {safe_text(row["original_language"], "Language unknown").upper()}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

        def compare_row(label, left_value, right_value):
            st.markdown(f"**{label}**")
            c1, c2 = st.columns(2)
            c1.write(left_value)
            c2.write(right_value)

        st.markdown("#### Head-to-head stats")
        left_rating = float(left_movie["vote_average"]) if pd.notna(left_movie["vote_average"]) else None
        right_rating = float(right_movie["vote_average"]) if pd.notna(right_movie["vote_average"]) else None
        left_votes = int(left_movie["vote_count"]) if pd.notna(left_movie["vote_count"]) else None
        right_votes = int(right_movie["vote_count"]) if pd.notna(right_movie["vote_count"]) else None
        left_runtime = int(left_movie["runtime"]) if pd.notna(left_movie["runtime"]) else None
        right_runtime = int(right_movie["runtime"]) if pd.notna(right_movie["runtime"]) else None
        compare_row("TMDB user score", f"{left_rating:.1f}/10" if left_rating is not None else "Not available",
                    f"{right_rating:.1f}/10" if right_rating is not None else "Not available")
        compare_row("TMDB vote count", f"{left_votes:,}" if left_votes is not None else "Not available",
                    f"{right_votes:,}" if right_votes is not None else "Not available")
        compare_row("Runtime", f"{left_runtime} min" if left_runtime is not None else "Not available",
                    f"{right_runtime} min" if right_runtime is not None else "Not available")
        compare_row("Genres", ", ".join(sorted(left_genres)) or "Not available",
                    ", ".join(sorted(right_genres)) or "Not available")
        compare_row("Curated lists", ", ".join(sorted(left_members)) or "None found",
                    ", ".join(sorted(right_members)) or "None found")

        st.markdown("#### What do they have in common?")
        common_col, list_col = st.columns(2)
        common_col.metric("Shared genres", len(common_genres))
        list_col.metric("Shared curated lists", len(common_lists))
        if common_genres:
            st.write("**Genres in common:** " + ", ".join(common_genres))
        else:
            st.caption("No shared genre metadata is available for this pair.")
        if common_lists:
            st.write("**Both appear in:** " + ", ".join(common_lists))
        else:
            st.caption("These movies do not share a curated source list.")
        if left_rating is not None and right_rating is not None:
            if left_rating > right_rating:
                st.success(f"{left_movie['title']} currently has the higher TMDB user score ({left_rating:.1f} vs {right_rating:.1f}).")
            elif right_rating > left_rating:
                st.success(f"{right_movie['title']} currently has the higher TMDB user score ({right_rating:.1f} vs {left_rating:.1f}).")
            else:
                st.info(f"Both movies currently have the same TMDB user score ({left_rating:.1f}/10).")
        st.markdown("#### Story snapshot")
        overview_left, overview_right = st.columns(2)
        overview_left.markdown(f"**{left_movie['title']}**")
        overview_left.write(safe_text(left_movie["overview"], "No synopsis available."))
        overview_right.markdown(f"**{right_movie['title']}**")
        overview_right.write(safe_text(right_movie["overview"], "No synopsis available."))
        if left_rating is not None or right_rating is not None:
            rating_plot = pd.DataFrame({
                "Movie": [str(left_movie["title"]), str(right_movie["title"])],
                "TMDB user score": [left_rating, right_rating],
            }).dropna()
            if not rating_plot.empty:
                score_fig = px.bar(rating_plot, x="Movie", y="TMDB user score", range_y=[0, 10], text_auto=".1f")
                score_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e9e9f0", transition_duration=650)
                st.plotly_chart(score_fig, use_container_width=True)
        st.caption("TMDB scores are user ratings, not critic scores. Vote counts and metadata can change as TMDB is updated.")
else:
    st.info("At least two movies with TMDB posters are needed to use Movie Face-Off.")


st.info(
    "List rank is not a movie rating. TMDB ratings are separate from Letterboxd list ranks. "
    "Revenue, OTT availability, sentiment and verified release status require additional verified sources."
)
