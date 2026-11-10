# AI Interactions Log

> Stretch features attempted: **Additional Song Attributes (agentic workflow)**, **Multiple Ranking Modes (Strategy pattern)**, **Diversity / Fairness penalty**, **Visual Summary Table**.

---

## Agentic Workflow (SF8) — Additional Song Attributes

**What task did you give the agent?**

I used Claude (in agent mode, with a shell and file tools) to take the starter repo and the full project spec, then: expand `data/songs.csv` from 10 to 22 songs covering genres and moods the starter was missing, add 5 new attributes, and update the scoring logic so each new attribute actually affects the score.

**Prompts used:**

- "Do the whole CodePath Music Recommender project" (with the project instructions and grading rubric attached).
- Key instructions inside that task: add 5+ new attributes (popularity 0–100, release decade, detailed mood tags, etc.); every new attribute must be used in `score_song()` and show up in the "reasons"; keep the `Song` / `UserProfile` classes compatible with the starter tests.

**What did the agent generate or change?**

- `data/songs.csv`: 12 new songs (r&b, hip-hop, edm, classical, country, metal, folk, reggae, blues, plus extra pop/synthwave/lofi songs by existing artists to test repeats) and 5 new columns: `popularity`, `release_decade`, `mood_tag`, `instrumentalness`, `liveness`.
- `src/recommender.py`: `load_songs()` converts the new numeric columns; `score_song()` adds points for `mood_tag` match (+0.75), preferred `decade` (+0.5), `popularity` = "mainstream"/"underground" (up to +0.5), `wants_instrumental` (up to +0.5), and `likes_live` (up to +0.5 × liveness). `Song` got the new fields with defaults so the starter tests still pass.
- `src/main.py`: 6 test profiles that use the new preferences, CLI flags, table output.
- `tests/test_recommender.py`: 5 new tests.

**What did you verify or fix manually?**

- Ran `pytest` and `python -m src.main --all` and checked the top results against my own intuition (e.g. the Chill Lofi profile should get quiet, acoustic, instrumental tracks — it does).
- One AI-written test **failed**: it assumed the diversity penalty would give 4 different artists in the top 4 for the High-Energy Pop profile. Checking the scores showed *Gym Hero* (4.28) still scores 2.78 after the repeat-artist and 3rd-pop-song penalties, which beats the next new-artist song (*Concrete Verses*, 2.24). The test was rewritten to check the real behavior (more distinct artists than without the penalty), and the weakness is documented in the model card instead of hidden.
- Fixed a starter bug: `src/main.py` imported `from recommender import ...`, which crashes with `python -m src.main`; changed to `from src.recommender import ...` and added `pytest.ini` so `pytest` can find `src`.

---

## Design Pattern (SF10) — Multiple Ranking Modes

**Which design pattern did you use?**

**Strategy pattern.**

**How did AI help you brainstorm or implement it?**

The options considered were (1) `if mode == ...` branches inside `score_song()`, (2) a separate scoring function per mode, or (3) Strategy objects that only hold the weights. Option 1 makes `score_song()` long and every new mode touches it; option 2 duplicates the scoring logic three times. Since the modes only differ in *how much* each signal counts, not *which* signals exist, the simplest Strategy is a class that holds a `weights` dict, and `score_song()` reads its point values from whatever strategy it's given.

**How does the pattern appear in your final code?**

- `ScoringStrategy` (Genre-First, the default), `MoodFirstStrategy` (genre 1.0, mood 2.0, mood tag 1.0), and `EnergyFocusedStrategy` (genre 1.0, energy 3.0) in `src/recommender.py`.
- `STRATEGIES = {"genre": ..., "mood": ..., "energy": ...}` registry.
- `score_song(user_prefs, song, strategy)` and `recommend_songs(..., mode="genre")` pick the strategy; the user switches with `python -m src.main --mode mood`.
- Adding a new mode = one new subclass with different weights; no changes to the scoring code.

---

## Diversity / Fairness

`recommend_songs(..., diversity=True)` (CLI: `--diverse`) re-ranks greedily: each time it picks the next song, it subtracts **1.0** if that artist is already in the picks and **0.5** if it would be the 3rd+ song of the same genre, and the penalty is written into the song's reasons. See the model card (sections 3, 6, 7) for its effect.

## Visual Summary Table

`src/main.py` prints results with `tabulate` (`simple_grid`), with columns #, Title, Artist, Genre, Score, Why — the "Why" column is the full list of scoring reasons, wrapped. If `tabulate` isn't installed it falls back to a plain ASCII layout.
