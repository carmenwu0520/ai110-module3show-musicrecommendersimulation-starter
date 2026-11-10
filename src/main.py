"""
Command line runner for the Music Recommender Simulation (VibeFinder 1.0).

Examples:
    python -m src.main                       # default pop/happy profile, Genre-First mode
    python -m src.main --all                 # every test profile
    python -m src.main --all --mode energy   # switch ranking strategy
    python -m src.main --profile "Chill Lofi" --diverse
"""

import argparse
import textwrap

from src.recommender import STRATEGIES, load_songs, recommend_songs

try:
    from tabulate import tabulate
except ImportError:  # tabulate is optional; fall back to plain ASCII
    tabulate = None

DEFAULT_PROFILE = {"genre": "pop", "mood": "happy", "energy": 0.8}

PROFILES = {
    # --- three "normal" listeners ---
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.85,
                        "likes_acoustic": False, "popularity": "mainstream"},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35,
                   "likes_acoustic": True, "wants_instrumental": True},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.9,
                          "likes_acoustic": False},
    # --- adversarial / edge cases ---
    "Sad but Hyped (conflict)": {"genre": "pop", "mood": "sad", "energy": 0.9},
    "Genre Not In Catalog": {"genre": "k-pop", "mood": "happy", "energy": 0.7},
    "Acoustic Headbanger (conflict)": {"genre": "metal", "mood": "angry", "energy": 0.95,
                                       "likes_acoustic": True},
}


def format_table(recs) -> str:
    """Render recommendations as a table with rank, title, artist, score and reasons."""
    rows = []
    for i, (song, score, explanation) in enumerate(recs, start=1):
        reasons = "\n".join(textwrap.wrap(explanation.replace("; ", " | "), 48))
        rows.append([i, song["title"], song["artist"], song["genre"], f"{score:.2f}", reasons])
    headers = ["#", "Title", "Artist", "Genre", "Score", "Why"]
    if tabulate:
        return tabulate(rows, headers=headers, tablefmt="simple_grid", disable_numparse=True)
    # ASCII fallback: one line per song, reasons indented underneath
    lines = [f"{'#':<3}{'Title':<24}{'Artist':<18}{'Genre':<12}{'Score':>6}", "-" * 63]
    for r in rows:
        lines.append(f"{r[0]:<3}{r[1]:<24}{r[2]:<18}{r[3]:<12}{r[4]:>6}")
        lines += ["     " + line for line in r[5].split("\n")]
    return "\n".join(lines)


def run_profile(name: str, prefs: dict, songs, mode: str, diverse: bool, k: int) -> None:
    """Print the top-k recommendations for one profile."""
    shown = ", ".join(f"{key}={val}" for key, val in prefs.items())
    print(f"\n=== {name} ===")
    print(f"Profile: {shown}")
    print(f"Mode: {STRATEGIES[mode].name}" + (" + diversity penalty" if diverse else ""))
    print(format_table(recommend_songs(prefs, songs, k=k, mode=mode, diversity=diverse)))


def main() -> None:
    parser = argparse.ArgumentParser(description="VibeFinder music recommender")
    parser.add_argument("--mode", choices=list(STRATEGIES), default="genre",
                        help="ranking strategy: genre (default), mood, or energy")
    parser.add_argument("--diverse", action="store_true",
                        help="penalize repeat artists / 3rd+ song of the same genre")
    parser.add_argument("--profile", choices=list(PROFILES), help="run one named profile")
    parser.add_argument("--all", action="store_true", help="run every test profile")
    parser.add_argument("-k", type=int, default=5, help="number of recommendations")
    args = parser.parse_args()

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    if args.all:
        for name, prefs in PROFILES.items():
            run_profile(name, prefs, songs, args.mode, args.diverse, args.k)
    elif args.profile:
        run_profile(args.profile, PROFILES[args.profile], songs, args.mode, args.diverse, args.k)
    else:
        run_profile("Default (pop / happy)", DEFAULT_PROFILE, songs, args.mode, args.diverse, args.k)


if __name__ == "__main__":
    main()
