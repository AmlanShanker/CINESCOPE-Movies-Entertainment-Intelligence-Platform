import streamlit as st
import plotly.express as px

from database.db import get_memberships, get_movies, refresh_database
from ingestion.csv_loader import DATASETS, load_all_datasets

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

source_movies, source_memberships, report = load_all_datasets()
if not report["loaded"]:
    st.warning("No valid source CSVs found. Add the three files to data/raw/ to begin.")
    for item in DATASETS:
        st.write(f"{item['name']} — {item['filename']}")
    st.stop()

try:
    # Import validated source data, then use SQLite as the dashboard's data layer.
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
    {
        "List": item["name"],
        "File": item["filename"],
        "Rows read": item["rows_read"],
        "Valid": item["valid_rows"],
        "Rejected": item["rejected_rows"],
    }
    for item in report["reports"]
]
st.dataframe(rows, use_container_width=True, hide_index=True)
for message in report["errors"]:
    st.warning(message)

left, right = st.columns(2)
with left:
    st.subheader("Movies by list")
    counts = memberships.groupby("list_name", as_index=False).size()
    fig = px.bar(
        counts,
        x="list_name",
        y="size",
        color="list_name",
        labels={"list_name": "Curated list", "size": "Movie entries"},
    )
    fig.update_layout(showlegend=False, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Overlap across lists")
    overlap = (
        memberships.groupby("list_name")["letterboxd_uri"]
        .nunique()
        .rename("Unique movies")
        .reset_index()
    )
    overlap_fig = px.pie(overlap, names="list_name", values="Unique movies")
    st.plotly_chart(overlap_fig, use_container_width=True)

st.subheader("Movie explorer")
query = st.text_input("Search titles")
list_names = sorted(memberships["list_name"].unique().tolist())
selected = st.selectbox("Source list", ["All lists"] + list_names)
view = movies.copy()
if query.strip():
    view = view[view["title"].str.contains(query.strip(), case=False, na=False)]
if selected != "All lists":
    urls = memberships.loc[
        memberships["list_name"] == selected, "letterboxd_uri"
    ]
    view = view[view["letterboxd_uri"].isin(urls)]
st.caption(f"{len(view)} unique movies shown")
st.dataframe(
    view[["title", "letterboxd_uri"]].rename(
        columns={"title": "Title", "letterboxd_uri": "Letterboxd URL"}
    ),
    use_container_width=True,
    hide_index=True,
)

st.info(
    "List rank is not a movie rating. Ratings, genres, revenue, OTT availability "
    "and release status require separately verified enrichment data."
)
