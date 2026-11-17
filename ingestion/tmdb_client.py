"""Small client for TMDB's v3 API."""
import re
import requests

API_ROOT = "https://api.themoviedb.org/3"
IMAGE_ROOT = "https://image.tmdb.org/t/p/w500"


def normalize_title(value):
    """Normalize a title for conservative exact-match comparison."""
    value = str(value or "").casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


class TMDBClient:
    def __init__(self, read_access_token, timeout=20):
        if not read_access_token:
            raise ValueError("A TMDB API Read Access Token is required.")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {read_access_token}",
            "accept": "application/json",
        })
        self.timeout = timeout

    def _get(self, endpoint, params=None):
        response = self.session.get(
            f"{API_ROOT}/{endpoint.lstrip('/')}",
            params=params or {},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def search_movie(self, title):
        payload = self._get("search/movie", {"query": title, "include_adult": "false"})
        wanted = normalize_title(title)
        exact = [
            item for item in payload.get("results", [])
            if normalize_title(item.get("title")) == wanted
            or normalize_title(item.get("original_title")) == wanted
        ]
        if len(exact) == 1:
            return exact[0], "matched"
        if len(exact) > 1:
            return None, "ambiguous"
        return None, "unmatched"

    def movie_details(self, tmdb_id):
        return self._get(f"movie/{int(tmdb_id)}")

    def enrich_title(self, title):
        """Use one search request per title; full details load when a card is opened."""
        result, status = self.search_movie(title)
        if not result:
            return {"title": title, "match_status": status}
        return {
            "title": title,
            "tmdb_id": result.get("id"),
            "poster_path": result.get("poster_path"),
            "backdrop_path": result.get("backdrop_path"),
            "overview": result.get("overview"),
            "release_date": result.get("release_date"),
            "original_language": result.get("original_language"),
            "vote_average": result.get("vote_average"),
            "vote_count": result.get("vote_count"),
            "runtime": None,
            "genres": [],
            "match_status": "matched",
        }


def poster_url(poster_path):
    return f"{IMAGE_ROOT}{poster_path}" if poster_path else None
