import streamlit as st
import plotly.express as px
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

movies, memberships, report = load_all_datasets()
if not report["loaded"]:
    st.warning("No valid source CSVs found. Add the three files to data/raw/ to begin.")
    for item in DATASETS:
        st.write(f"{item['name']} — {item['filename']}")
    st.stop()

a, b, c = st.columns(3)
a.metric("Lists loaded", len(report["loaded"]))
b.metric("List entries", len(memberships))
c.metric("Unique movies", len(movies))

st.subheader("Data quality")
rows = [{"List": r["name"], "File": r["filename"], "Rows read": r["rows_read"], "Valid": r["valid_rows"], "Rejected": r["rejected_rows"]} for r in report["reports"]]
st.dataframe(rows, use_container_width=True, hide_index=True)
for message in report["errors"]:
    st.warning(message)

st.subheader("Movies by list")
counts = memberships.groupby("list_name", as_index=False).size()
fig = px.bar(counts, x="list_name", y="size", color="list_name", labels={"list_name": "Curated list", "size": "Movie entries"})
fig.update_layout(showlegend=False, xaxis_title=None)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Movie explorer")
query = st.text_input("Search titles")
selected = st.selectbox("Source list", ["All lists"] + sorted(memberships["list_name"].unique()))
view = movies
if query.strip():
    view = view[view["title"].str.contains(query.strip(), case=False, na=False)]
if selected != "All lists":
    urls = memberships.loc[memberships["list_name"] == selected, "letterboxd_uri"]
    view = view[view["letterboxd_uri"].isin(urls)]
st.caption(f"{len(view)} unique movies shown")
st.dataframe(view.rename(columns={"title": "Title", "letterboxd_uri": "Letterboxd URL"}), use_container_width=True, hide_index=True)

st.info("List rank is not a movie rating. Ratings, genres, revenue, OTT availability and release status require separately verified enrichment data.")
