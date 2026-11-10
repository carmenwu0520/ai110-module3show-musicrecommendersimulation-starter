"""
VibeFinder 1.0 - a small content-based music recommender.

Pipeline:  load_songs()  ->  score_song() for every song  ->  recommend_songs() ranks them.
Scoring weights live in "strategy" objects (Genre-First, Mood-First, Energy-Focused) so
the ranking mode can be swapped without touching the scoring code (Strategy pattern).
"""

import csv
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

NUMERIC_FLOAT_FIELDS = ["energy", "tempo_bpm", "valence", "danceability", "acousticness",
                        "instrumentalness", "liveness"]
NUMERIC_INT_FIELDS = ["id", "popularity"]


# ---------------------------------------------------------------------------
# Data classes (used by tests/test_recommender.py)
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """A song and its attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: int = 50
    release_decade: str = ""
    mood_tag: str = ""
    instrumentalness: float = 0.0
    liveness: float = 0.0


@dataclass
class UserProfile:
    """A user's taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

    def to_prefs(self) -> Dict:
        """Convert the profile to the dict format used by score_song()."""
        return {
            "genre": self.favorite_genre,
            "mood": self.favorite_mood,
            "energy": self.target_energy,
            "likes_acoustic": self.likes_acoustic,
        }


# ---------------------------------------------------------------------------
# Ranking strategies (Strategy pattern): each one is just a set of weights
# ---------------------------------------------------------------------------

class ScoringStrategy:
    """Base strategy: holds the point weights used by score_song()."""
    name = "Genre-First"
    weights = {
        "genre": 2.0,        # exact genre match
        "mood": 1.0,         # exact mood match
        "energy": 1.5,       # max points for a perfect energy match
        "acoustic": 0.5,     # acoustic / non-acoustic preference
        "valence": 0.5,      # closeness to target valence (if given)
        "danceability": 0.5, # closeness to target danceability (if given)
        "mood_tag": 0.75,    # detailed mood tag match (e.g. "nostalgic")
        "decade": 0.5,       # preferred release decade
        "popularity": 0.5,   # mainstream vs underground preference
        "instrumental": 0.5, # wants instrumental (no vocals) music
        "live": 0.5,         # prefers live / concert-sounding recordings
    }


class MoodFirstStrategy(ScoringStrategy):
    """Mood matters more than genre."""
    name = "Mood-First"
    weights = {**ScoringStrategy.weights, "genre": 1.0, "mood": 2.0, "mood_tag": 1.0}


class EnergyFocusedStrategy(ScoringStrategy):
    """Energy closeness dominates; genre counts half as much (the Phase 4 experiment)."""
    name = "Energy-Focused"
    weights = {**ScoringStrategy.weights, "genre": 1.0, "energy": 3.0}


STRATEGIES = {
    "genre": ScoringStrategy(),
    "mood": MoodFirstStrategy(),
    "energy": EnergyFocusedStrategy(),
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv into a list of dicts, converting numeric columns to numbers."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for field in NUMERIC_FLOAT_FIELDS:
                if row.get(field) not in (None, ""):
                    row[field] = float(row[field])
            for field in NUMERIC_INT_FIELDS:
                if row.get(field) not in (None, ""):
                    row[field] = int(row[field])
            songs.append(row)
    return songs


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _closeness(value: float, target: float) -> float:
    """Return 1.0 when value == target, falling linearly to 0.0 when they are 1.0 apart."""
    return max(0.0, 1.0 - abs(value - target))


def _genre_points(user_genre: str, song_genre: str, weight: float) -> Tuple[float, Optional[str]]:
    """Full points for an exact genre match, half points for a related genre (shared word)."""
    user_genre, song_genre = user_genre.lower().strip(), song_genre.lower().strip()
    if user_genre == song_genre:
        return weight, f"genre match: {song_genre} (+{weight:.2f})"
    if set(user_genre.split()) & set(song_genre.split()):
        pts = weight / 2
        return pts, f"related genre: {song_genre} (+{pts:.2f})"
    return 0.0, None


def score_song(user_prefs: Dict, song: Dict,
               strategy: ScoringStrategy = STRATEGIES["genre"]) -> Tuple[float, List[str]]:
    """Score one song against the user's preferences; return (score, list of reasons)."""
    w = strategy.weights
    score, reasons = 0.0, []

    def add(points: float, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(reason)

    # Categorical matches
    if user_prefs.get("genre"):
        pts, why = _genre_points(user_prefs["genre"], song["genre"], w["genre"])
        if why:
            add(pts, why)
    if user_prefs.get("mood") and user_prefs["mood"].lower() == song["mood"].lower():
        add(w["mood"], f"mood match: {song['mood']} (+{w['mood']:.2f})")
    if user_prefs.get("mood_tag") and user_prefs["mood_tag"].lower() == song.get("mood_tag", "").lower():
        add(w["mood_tag"], f"mood tag: {song['mood_tag']} (+{w['mood_tag']:.2f})")
    if user_prefs.get("decade") and user_prefs["decade"] == song.get("release_decade"):
        add(w["decade"], f"from the {song['release_decade']} (+{w['decade']:.2f})")

    # Numeric closeness: reward songs NEAR the target, not just higher/lower
    if "energy" in user_prefs:
        pts = w["energy"] * _closeness(song["energy"], user_prefs["energy"])
        add(pts, f"energy {song['energy']:.2f} vs target {user_prefs['energy']:.2f} (+{pts:.2f})")
    for key, label in (("valence", "valence"), ("danceability", "danceability")):
        if key in user_prefs:
            pts = w[key] * _closeness(song[key], user_prefs[key])
            add(pts, f"{label} close to target (+{pts:.2f})")

    # Preference flags
    if "likes_acoustic" in user_prefs:
        a = song["acousticness"]
        pts = w["acoustic"] * (a if user_prefs["likes_acoustic"] else 1 - a)
        kind = "acoustic" if user_prefs["likes_acoustic"] else "non-acoustic"
        add(pts, f"{kind} sound (+{pts:.2f})")
    if user_prefs.get("wants_instrumental"):
        pts = w["instrumental"] * song.get("instrumentalness", 0.0)
        add(pts, f"instrumental (+{pts:.2f})")
    if user_prefs.get("likes_live"):
        pts = w["live"] * song.get("liveness", 0.0)
        add(pts, f"live feel, liveness {song.get('liveness', 0.0):.2f} (+{pts:.2f})")
    if user_prefs.get("popularity") in ("mainstream", "underground"):
        pop = song.get("popularity", 50) / 100
        pts = w["popularity"] * (pop if user_prefs["popularity"] == "mainstream" else 1 - pop)
        add(pts, f"{user_prefs['popularity']} pick, popularity {song.get('popularity')} (+{pts:.2f})")

    return round(score, 2), reasons


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def _apply_diversity(scored: List[Tuple[Dict, float, List[str]]], k: int,
                     artist_penalty: float, genre_penalty: float) -> List[Tuple[Dict, float, List[str]]]:
    """Greedy re-rank: penalize songs whose artist/genre already appears in the picks so far."""
    picks, pool = [], list(scored)
    while pool and len(picks) < k:
        best = None
        for song, base, reasons in pool:
            penalty, notes = 0.0, []
            if any(p[0]["artist"] == song["artist"] for p in picks):
                penalty += artist_penalty
                notes.append(f"repeat artist (-{artist_penalty:.2f})")
            if sum(p[0]["genre"] == song["genre"] for p in picks) >= 2:
                penalty += genre_penalty
                notes.append(f"3rd+ {song['genre']} song (-{genre_penalty:.2f})")
            adjusted = round(base - penalty, 2)
            if best is None or adjusted > best[1]:
                best = (song, adjusted, reasons + notes)
        picks.append(best)
        pool = [item for item in pool if item[0] is not best[0]]
    return picks


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    mode: str = "genre", diversity: bool = False,
                    artist_penalty: float = 1.0, genre_penalty: float = 0.5
                    ) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort high to low, and return the top k as (song, score, explanation)."""
    strategy = STRATEGIES[mode]
    scored = [(song, *score_song(user_prefs, song, strategy)) for song in songs]
    # sorted() returns a NEW list and leaves `songs` untouched (.sort() would mutate in place)
    scored = sorted(scored, key=lambda item: item[1], reverse=True)
    if diversity:
        top = _apply_diversity(scored, k, artist_penalty, genre_penalty)
    else:
        top = scored[:k]
    return [(song, score, "; ".join(reasons)) for song, score, reasons in top]


# ---------------------------------------------------------------------------
# OOP wrapper (used by tests)
# ---------------------------------------------------------------------------

class Recommender:
    """OOP wrapper around score_song / recommend_songs for Song objects."""

    def __init__(self, songs: List[Song], mode: str = "genre"):
        self.songs = songs
        self.mode = mode

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for this user, highest score first."""
        prefs = user.to_prefs()
        strategy = STRATEGIES[self.mode]
        return sorted(self.songs, key=lambda s: score_song(prefs, vars(s), strategy)[0],
                      reverse=True)[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a readable sentence explaining a song's score for this user."""
        score, reasons = score_song(user.to_prefs(), vars(song), STRATEGIES[self.mode])
        return f"Score {score:.2f} because: " + "; ".join(reasons)
